#!/usr/bin/env python3
"""SAI-AUT-OS — HuggingFace Hub adapter (reference implementation, non-normative).

Binds HuggingFace Hub repositories to SAI-AUT-OS governed objects:

    Hub revision (commit SHA)  ->  baseline identity / rollback anchor
    per-file SHA-256           ->  provenance integrity / evidence payload_hash
    model-card metadata        ->  Evidence records (attestation, metric)
    new head on tracked repo   ->  candidate update -> draft CCI

Division of labour (see adapters/README.md):
    the adapter PROPOSES (observe -> collect -> normalize -> propose)
    the control plane DECIDES (evaluate -> validate -> authorize)
    the adapter APPLIES only authorized CCIs (atomic compare-and-swap repin)

Determinism: the core takes a Hub *snapshot* (SnapshotClient) and a pin store;
identical inputs yield byte-identical records — no clocks, no randomness, no
network. The optional HfApiClient exists for live deployments only and is
never used by tests or conformance vectors.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

SPEC_VERSION = "1.0.0-draft.1"
ADAPTER_ID = "adapters/huggingface"
ADAPTER_VERSION = "0.1.0"

# Registered IDs (registry/update-types, registry/adaptive-components).
UPDATE_CLASS_BY_KIND = {
    "peft-adapter": "lora-adapter-promotion",
    "dataset": "rag-corpus-update",
}
COMPONENT_BY_KIND = {
    "peft-adapter": "lora-adapter",
    "dataset": "rag-index",
}


# ----------------------------------------------------------------------------
# Canonicalization — one serialization, everywhere, or hashes mean nothing.
# ----------------------------------------------------------------------------

def canonical(obj) -> str:
    """Canonical JSON: sorted keys, tight separators, UTF-8 text."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------------
# Hub model
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class HubFile:
    path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class HubRevision:
    repo_id: str
    sha: str
    kind: str                 # "peft-adapter" | "dataset"
    files: tuple[HubFile, ...]
    card: dict                # model-card metadata (read-only by convention)


class HubClient(Protocol):
    def head(self, repo_id: str) -> str: ...
    def revision(self, repo_id: str, sha: str) -> HubRevision: ...


class SnapshotClient:
    """Deterministic client over a local JSON snapshot (fixtures, tests, vectors)."""

    def __init__(self, snapshot: dict):
        self._snap = snapshot

    @classmethod
    def from_file(cls, path: str | Path) -> "SnapshotClient":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    @property
    def pins(self) -> dict:
        """Initial pin store shipped with the snapshot, if any."""
        return json.loads(canonical(self._snap.get("pins", {})))  # deep copy

    def head(self, repo_id: str) -> str:
        return self._snap["repos"][repo_id]["head"]

    def revision(self, repo_id: str, sha: str) -> HubRevision:
        repo = self._snap["repos"][repo_id]
        rev = repo["revisions"][sha]
        files = tuple(
            HubFile(f["path"], f["sha256"], f["size"])
            for f in sorted(rev["files"], key=lambda f: f["path"])
        )
        return HubRevision(repo_id, sha, repo["kind"], files, rev.get("card", {}))


class HfApiClient:
    """Live client (optional). Requires the `huggingface_hub` package and network
    egress to huggingface.co. Best effort: files without LFS metadata fall back
    to their blob id. Never used by tests — determinism first."""

    def __init__(self):
        from huggingface_hub import HfApi  # deferred: optional dependency
        self._api = HfApi()

    def head(self, repo_id: str) -> str:
        return self._api.model_info(repo_id).sha

    def revision(self, repo_id: str, sha: str) -> HubRevision:
        info = self._api.model_info(repo_id, revision=sha, files_metadata=True)
        files = tuple(
            HubFile(s.rfilename,
                    (s.lfs.sha256 if getattr(s, "lfs", None) else (s.blob_id or "")),
                    s.size or 0)
            for s in sorted(info.siblings, key=lambda s: s.rfilename)
        )
        card = dict(info.card_data.to_dict()) if info.card_data else {}
        kind = "peft-adapter" if "peft" in (info.tags or []) else "dataset"
        return HubRevision(repo_id, sha, kind, files, card)


# ----------------------------------------------------------------------------
# Pipeline: observe -> collect -> normalize -> propose
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class Candidate:
    repo_id: str
    pinned_sha: str
    head_sha: str
    kind: str


def observe(client: HubClient, pins: dict) -> list[Candidate]:
    """A candidate exists wherever the Hub head has moved past the pin."""
    out: list[Candidate] = []
    for repo_id in sorted(pins):
        pin = pins[repo_id]
        head = client.head(repo_id)
        if head != pin["sha"]:
            out.append(Candidate(repo_id, pin["sha"], head, pin["kind"]))
    return out


def collect(client: HubClient, cand: Candidate) -> dict:
    return {
        "pinned": client.revision(cand.repo_id, cand.pinned_sha),
        "head": client.revision(cand.repo_id, cand.head_sha),
    }


def _file_manifest(rev: HubRevision) -> list[dict]:
    return [{"path": f.path, "sha256": f.sha256, "size": f.size} for f in rev.files]


def normalize(cand: Candidate, raw: dict) -> list[dict]:
    """Reduce raw Hub data to Evidence records (schemas/evidence.schema.json).

    Every record binds its payload by hash: replayable, tamper-evident."""
    head, pinned = raw["head"], raw["pinned"]
    records: list[dict] = []

    manifest = {"repo": cand.repo_id, "revision": head.sha,
                "files": _file_manifest(head)}
    mhash = sha256_hex(canonical(manifest))
    records.append({
        "id": f"evd-attestation-{mhash[:12]}",
        "type": "attestation",
        "source": f"hf:{cand.repo_id}@{head.sha}",
        "collected_by": ADAPTER_ID,
        "payload_hash": mhash,
        "summary": (f"Hub file manifest for {cand.repo_id}@{head.sha[:12]} "
                    f"({len(head.files)} files, sha256-bound)."),
    })

    for name in sorted(head.card.get("metrics", {})):
        payload = {
            "metric": name,
            "value": head.card["metrics"][name],
            "baseline_value": pinned.card.get("metrics", {}).get(name),
            "source": "model-card",
        }
        phash = sha256_hex(canonical(payload))
        records.append({
            "id": f"evd-metric-{phash[:12]}",
            "type": "metric",
            "source": f"hf:{cand.repo_id}@{head.sha}#card",
            "collected_by": ADAPTER_ID,
            "payload_hash": phash,
            "summary": (f"{name}: {payload['baseline_value']} -> "
                        f"{payload['value']} (declared in model card)."),
        })
    return records


def propose(cand: Candidate, raw: dict, evidence: list[dict]) -> dict:
    """Draft a CCI (schemas/cci.schema.json). A draft, not a decision:
    lifecycle ownership passes to the control plane from here."""
    head = raw["head"]
    return {
        "id": f"cci-hf-{cand.repo_id.replace('/', '-')}-{cand.head_sha[:12]}",
        "class": UPDATE_CLASS_BY_KIND[cand.kind],
        "version": "1.0.0",
        "provenance": {
            "proposer": ADAPTER_ID,
            "adapter_version": ADAPTER_VERSION,
            "source": "huggingface-hub",
            "repo_id": cand.repo_id,
            "revision": cand.head_sha,
            "base_model": head.card.get("base_model"),
            "license": head.card.get("license"),
            "integrity": {"algorithm": "sha256", "files": _file_manifest(head)},
        },
        "scope": {
            "adaptive_component": COMPONENT_BY_KIND[cand.kind],
            "component_id": cand.repo_id.split("/")[-1],
            "target": f"hf:{cand.repo_id}",
        },
        # Effectivity discipline: proposals land in staging; widening scope is
        # a control-plane decision, never an adapter default.
        "effectivity": {"environments": ["staging"]},
        "evidence": evidence,
        "rollback_target": f"hf:{cand.repo_id}@{cand.pinned_sha}",
        "supersedes": f"hf:{cand.repo_id}@{cand.pinned_sha}",
    }


# ----------------------------------------------------------------------------
# Apply / rollback — the only writes this adapter performs, and only on orders
# ----------------------------------------------------------------------------

class AdapterRefusal(RuntimeError):
    """Raised whenever applying would violate the standard. Refusals are loud."""


def _anchor_sha(anchor: str) -> str:
    return anchor.split("@", 1)[1]


def apply_authorized(cci: dict, authorization: dict, pins: dict) -> tuple[dict, dict]:
    """Apply an *authorized* CCI as an atomic compare-and-swap repin.

    Returns (new_pins, deployment_record_draft). Never mutates its inputs.
    Refuses (SAO-AUT-001) unless the Authorization record references this CCI
    with decision == "allow" — the only applying decision in the ratified
    grammar; BLOCK/WARN semantics arrive with RFC-0001."""
    if authorization.get("cci_id") != cci["id"]:
        raise AdapterRefusal("authorization does not reference this CCI (SAO-AUT-001)")
    decision = authorization.get("decision")
    if decision != "allow":
        raise AdapterRefusal(
            f"decision is {decision!r}; this adapter applies only 'allow' "
            "(BLOCK/WARN semantics arrive with RFC-0001)")

    repo_id = cci["provenance"]["repo_id"]
    new_sha = cci["provenance"]["revision"]
    expected_prev = _anchor_sha(cci["rollback_target"])
    current = pins[repo_id]["sha"]
    if current != expected_prev:
        raise AdapterRefusal(
            "pin drifted since proposal (CAS failure): expected "
            f"{expected_prev[:12]}, found {current[:12]} — re-propose")

    new_pins = {**pins, repo_id: {**pins[repo_id], "sha": new_sha}}
    record = {
        "record_id": f"dep-{cci['id']}",
        "cci_id": cci["id"],
        "authorization_ref": f"authz:{cci['id']}",
        "deployed_version": f"hf:{repo_id}@{new_sha}",
        "previous_version": cci["rollback_target"],
        "status": "live",
    }
    return new_pins, record


def execute_rollback(cci: dict, deployment_record: dict, pins: dict,
                     reason: str) -> tuple[dict, dict]:
    """Repin to the declared rollback anchor (SAO-RBK-001) on control-plane
    order. Hub revisions are immutable, so the anchor is always resolvable.
    Returns (new_pins, rollback_record_draft)."""
    repo_id = cci["provenance"]["repo_id"]
    target_sha = _anchor_sha(cci["rollback_target"])
    new_pins = {**pins, repo_id: {**pins[repo_id], "sha": target_sha}}
    record = {
        "cci_id": cci["id"],
        "deployment_ref": deployment_record["record_id"],
        "rollback_target": cci["rollback_target"],
        "reason": reason,
        "status": "executed",
    }
    return new_pins, record


# ----------------------------------------------------------------------------
# Demo (offline, deterministic)
# ----------------------------------------------------------------------------

def _demo() -> None:
    here = Path(__file__).resolve().parent
    client = SnapshotClient.from_file(here / "fixtures" / "hub_snapshot.json")
    pins = client.pins

    candidates = observe(client, pins)
    print(f"[observe]   {len(candidates)} candidate(s)")
    for cand in candidates:
        raw = collect(client, cand)
        evidence = normalize(cand, raw)
        cci = propose(cand, raw, evidence)
        print(f"[collect]   {cand.repo_id}: {cand.pinned_sha[:12]} -> {cand.head_sha[:12]}")
        print(f"[normalize] {len(evidence)} evidence record(s), hash-bound")
        print(f"[propose]   {cci['id']}  class={cci['class']}")
        print(f"            rollback_target={cci['rollback_target']}")
        print("--- draft CCI (canonical) ---")
        print(json.dumps(cci, indent=2, sort_keys=True))
        print("--- lifecycle ownership now passes to the control plane ---")


if __name__ == "__main__":
    _demo()
