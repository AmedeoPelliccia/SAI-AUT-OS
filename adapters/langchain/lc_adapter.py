#!/usr/bin/env python3
"""SAI-AUT-OS — LangChain runtime adapter (reference implementation, non-normative).

LangChain has no configuration-management substrate to inherit: tool sets are
Python lists, memory is a mutable store. This binding manufactures the
substrate the framework lacks:

    canonical tool manifest        ->  baseline (the manifest hash IS the revision)
    anchor store (hash -> object)  ->  manufactured immutable history (SAO-RBK-001)
    enforce gate at construction   ->  fail-closed allowlist (the runtime teeth)

Two update classes, one adapter:

    tool set delta                 ->  tool-permission-change  (component: tool-binding)
    durable memory promotion       ->  memory-update           (component: memory)

Governability criterion for memory: what survives the session is
configuration; turn-level buffers are runtime state and are out of scope.

Division of labour (see adapters/README.md): the adapter PROPOSES and, on an
Authorization whose decision is "allow", APPLIES. It never evaluates,
authorizes, or decides. Capability classes (side effects) are DECLARED by the
integrator, never inferred — guessing capabilities is how least-privilege dies.

Determinism: plain dicts in, hash-bound records out; no clocks, no randomness,
no network. Standalone by design: helpers shared with sibling adapters
graduate to sdk/python when it lands.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

SPEC_VERSION = "1.0.0-draft.1"
ADAPTER_ID = "adapters/langchain"
ADAPTER_VERSION = "0.1.0"

# Adapter-local capability vocabulary (promotion to an official registry is
# RFC material). Order is documentation, not precedence.
SIDE_EFFECT_CLASSES = (
    "read-only", "network", "filesystem-read", "filesystem-write", "execute",
)

ABSENT = "absent"  # rollback-anchor sentinel for keys that did not exist


# ----------------------------------------------------------------------------
# Canonicalization — one serialization, everywhere, or hashes mean nothing.
# ----------------------------------------------------------------------------

def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class AdapterRefusal(RuntimeError):
    """Raised whenever proceeding would violate the standard. Refusals are loud."""


# ----------------------------------------------------------------------------
# Tool specs, identities, manifests — the manufactured baseline
# ----------------------------------------------------------------------------

def tool_spec(name: str, description: str, args_schema: dict,
              side_effects: list[str]) -> dict:
    """A live tool spec (full text). Identity is derived, never stored loose."""
    unknown = sorted(set(side_effects) - set(SIDE_EFFECT_CLASSES))
    if unknown:
        raise AdapterRefusal(f"undeclared side-effect classes: {unknown}")
    return {"name": name, "description": description,
            "args_schema": args_schema, "side_effects": sorted(side_effects)}


def identity(spec: dict) -> dict:
    """Tool identity: name + description hash + schema hash + capabilities.
    The description hash is deliberate — a changed description is a changed
    behaviour surface for the agent, as steering as changed code."""
    return {
        "name": spec["name"],
        "description_sha256": sha256_hex(spec["description"]),
        "args_schema_sha256": sha256_hex(canonical(spec["args_schema"])),
        "side_effects": sorted(spec["side_effects"]),
    }


def build_manifest(agent_id: str, specs: list[dict]) -> dict:
    return {"agent_id": agent_id,
            "tools": [identity(s) for s in sorted(specs, key=lambda s: s["name"])]}


def manifest_hash(manifest: dict) -> str:
    return sha256_hex(canonical(manifest))


def anchor_put(anchors: dict, obj) -> str:
    """Content-addressed, append-only store: the immutable history LangChain
    never had. Anchoring is idempotent by construction."""
    h = sha256_hex(canonical(obj))
    anchors[h] = json.loads(canonical(obj))
    return h


def from_langchain_tools(tools, side_effects_by_name: dict) -> list[dict]:
    """Convert live LangChain BaseTool objects to plain specs by duck-typing
    (no LangChain import required). Capability classes must be declared."""
    specs = []
    for tool in tools:
        name = tool.name
        if name not in side_effects_by_name:
            raise AdapterRefusal(f"no declared side-effect class for tool {name!r}")
        schema = {}
        args_schema = getattr(tool, "args_schema", None)
        if args_schema is not None and hasattr(args_schema, "model_json_schema"):
            schema = args_schema.model_json_schema()
        elif hasattr(tool, "args"):
            schema = dict(tool.args)
        specs.append(tool_spec(name, getattr(tool, "description", "") or "",
                               schema, side_effects_by_name[name]))
    return specs


# ----------------------------------------------------------------------------
# Pipeline (tools): observe -> collect -> normalize -> propose
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolDelta:
    agent_id: str
    pinned_hash: str
    proposed_hash: str
    added: tuple[str, ...]
    removed: tuple[str, ...]
    modified: tuple[str, ...]
    widening: bool
    narrowing: bool


def observe_tools(agent_id: str, live_specs: list[dict],
                  pins: dict, anchors: dict) -> ToolDelta | None:
    pinned_hash = pins[agent_id]["tools"]
    pinned = anchors[pinned_hash]
    proposed = build_manifest(agent_id, live_specs)
    proposed_hash = manifest_hash(proposed)
    if proposed_hash == pinned_hash:
        return None

    before = {t["name"]: t for t in pinned["tools"]}
    after = {t["name"]: t for t in proposed["tools"]}
    added = tuple(sorted(after.keys() - before.keys()))
    removed = tuple(sorted(before.keys() - after.keys()))
    modified = tuple(sorted(n for n in before.keys() & after.keys()
                            if before[n] != after[n]))
    widening = bool(added) or any(
        set(after[n]["side_effects"]) - set(before[n]["side_effects"])
        for n in modified)
    narrowing = bool(removed) or any(
        set(before[n]["side_effects"]) - set(after[n]["side_effects"])
        for n in modified)
    return ToolDelta(agent_id, pinned_hash, proposed_hash,
                     added, removed, modified, widening, narrowing)


def collect_tools(delta: ToolDelta, live_specs: list[dict],
                  anchors: dict) -> dict:
    return {
        "pinned_manifest": anchors[delta.pinned_hash],
        "proposed_manifest": build_manifest(delta.agent_id, live_specs),
        "specs_by_name": {s["name"]: s for s in live_specs},
    }


def normalize_tools(delta: ToolDelta, raw: dict) -> list[dict]:
    """Evidence records (schemas/evidence.schema.json), hash-bound."""
    proposed = raw["proposed_manifest"]
    pinned_tools = {t["name"]: t for t in raw["pinned_manifest"]["tools"]}
    specs = raw["specs_by_name"]

    records = []

    records.append({
        "id": f"evd-attestation-{delta.proposed_hash[:12]}",
        "type": "attestation",
        "source": f"lc:{delta.agent_id}#tools",
        "collected_by": ADAPTER_ID,
        "payload_hash": delta.proposed_hash,
        "summary": (f"Canonical tool manifest for {delta.agent_id} "
                    f"({len(proposed['tools'])} tools, identities sha256-bound)."),
    })

    delta_payload = {
        "agent_id": delta.agent_id,
        "pinned_manifest_sha256": delta.pinned_hash,
        "proposed_manifest_sha256": delta.proposed_hash,
        "added": [specs[n] for n in delta.added],
        "removed": [pinned_tools[n] for n in delta.removed],
        "modified": [{"name": n, "before": pinned_tools[n],
                      "after": specs[n]} for n in delta.modified],
        "widening": delta.widening,
        "narrowing": delta.narrowing,
    }
    dhash = sha256_hex(canonical(delta_payload))
    records.append({
        "id": f"evd-attestation-{dhash[:12]}",
        "type": "attestation",
        "source": f"lc:{delta.agent_id}#tools/delta",
        "collected_by": ADAPTER_ID,
        "payload_hash": dhash,
        "summary": (f"Tool-binding delta: +{len(delta.added)} "
                    f"-{len(delta.removed)} ~{len(delta.modified)}; "
                    f"widening={delta.widening} narrowing={delta.narrowing}."),
    })
    return records


def propose_tools(delta: ToolDelta, raw: dict, evidence: list[dict]) -> dict:
    """Draft CCI (schemas/cci.schema.json). Ownership passes to the control
    plane from here. The integrity block makes apply self-contained."""
    proposed = raw["proposed_manifest"]
    return {
        "id": f"cci-lc-{_slug(delta.agent_id)}-tools-{delta.proposed_hash[:12]}",
        "class": "tool-permission-change",
        "version": "1.0.0",
        "provenance": {
            "proposer": ADAPTER_ID,
            "adapter_version": ADAPTER_VERSION,
            "source": "langchain-runtime",
            "agent_id": delta.agent_id,
            "proposed_manifest_sha256": delta.proposed_hash,
            "integrity": {"algorithm": "sha256", "tools": proposed["tools"]},
        },
        "scope": {
            "adaptive_component": "tool-binding",
            "component_id": delta.agent_id.split("/")[-1],
            "target": f"lc:{delta.agent_id}#tools",
        },
        "effectivity": {"environments": ["staging"]},
        "evidence": evidence,
        "rollback_target": f"lc:{delta.agent_id}#tools@{delta.pinned_hash}",
        "supersedes": f"lc:{delta.agent_id}#tools@{delta.pinned_hash}",
    }


# ----------------------------------------------------------------------------
# Pipeline (memory): durable promotions only
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class MemoryDelta:
    agent_id: str
    namespace: str
    key: str
    value: str
    value_sha256: str
    prior_present: bool
    prior_sha256: str | None
    source_session: str


def observe_memory(agent_id: str, proposals: list[dict],
                   store: dict) -> list[MemoryDelta]:
    out = []
    for p in proposals:
        prior = store.get(p["namespace"], {}).get(p["key"])
        value_sha = sha256_hex(p["value"])
        prior_sha = sha256_hex(prior["value"]) if prior else None
        if prior_sha == value_sha:
            continue  # no-op: not a candidate
        out.append(MemoryDelta(agent_id, p["namespace"], p["key"], p["value"],
                               value_sha, prior is not None, prior_sha,
                               p["source"]))
    return out


def normalize_memory(delta: MemoryDelta) -> list[dict]:
    payload = {
        "agent_id": delta.agent_id,
        "namespace": delta.namespace,
        "key": delta.key,
        "value_sha256": delta.value_sha256,
        "prior": {"present": delta.prior_present, "sha256": delta.prior_sha256},
        "source_session": delta.source_session,
    }
    phash = sha256_hex(canonical(payload))
    return [{
        "id": f"evd-attestation-{phash[:12]}",
        "type": "attestation",
        "source": f"lc:{delta.agent_id}#memory/{delta.namespace}/{delta.key}",
        "collected_by": ADAPTER_ID,
        "payload_hash": phash,
        "summary": (f"Durable memory promotion {delta.namespace}/{delta.key}: "
                    f"prior={'present' if delta.prior_present else 'absent'}, "
                    f"value sha256-bound."),
    }]


def propose_memory(delta: MemoryDelta, evidence: list[dict]) -> dict:
    anchor = delta.prior_sha256 if delta.prior_present else ABSENT
    return {
        "id": (f"cci-lc-{_slug(delta.agent_id)}-mem-{_slug(delta.key)}-"
               f"{delta.value_sha256[:12]}"),
        "class": "memory-update",
        "version": "1.0.0",
        "provenance": {
            "proposer": ADAPTER_ID,
            "adapter_version": ADAPTER_VERSION,
            "source": "langchain-runtime",
            "agent_id": delta.agent_id,
            "namespace": delta.namespace,
            "key": delta.key,
            "content": delta.value,
            "value_sha256": delta.value_sha256,
            "source_session": delta.source_session,
            "prior": {"present": delta.prior_present,
                      "sha256": delta.prior_sha256},
        },
        "scope": {
            "adaptive_component": "memory",
            "component_id": delta.namespace,
            "target": f"lc:{delta.agent_id}#memory/{delta.namespace}/{delta.key}",
        },
        "effectivity": {"environments": ["staging"]},
        "evidence": evidence,
        "rollback_target": (f"lc:{delta.agent_id}#memory/{delta.namespace}/"
                            f"{delta.key}@{anchor}"),
        "supersedes": (f"lc:{delta.agent_id}#memory/{delta.namespace}/"
                       f"{delta.key}@{anchor}"),
    }


# ----------------------------------------------------------------------------
# Apply / rollback / enforce — the only writes, and only on orders
# ----------------------------------------------------------------------------

def _require_allow(cci: dict, authorization: dict) -> None:
    if authorization.get("cci_id") != cci["id"]:
        raise AdapterRefusal("authorization does not reference this CCI (SAO-AUT-001)")
    decision = authorization.get("decision")
    if decision != "allow":
        raise AdapterRefusal(
            f"decision is {decision!r}; this adapter applies only 'allow' "
            "(BLOCK/WARN semantics arrive with RFC-0001)")


def _anchor_token(anchor: str) -> str:
    return anchor.rsplit("@", 1)[1]


def apply_authorized_tools(cci: dict, authorization: dict,
                           pins: dict, anchors: dict) -> tuple[dict, dict]:
    """Atomic compare-and-swap repin of the tool manifest.

    Self-contained: the manifest is rebuilt from the CCI's own integrity block
    and its hash re-verified — a tampered CCI is refused. Returns
    (new_pins, deployment_record_draft); pins are never mutated, the anchor
    store grows by exactly the applied manifest (append-only by contract)."""
    _require_allow(cci, authorization)
    prov = cci["provenance"]
    manifest = {"agent_id": prov["agent_id"], "tools": prov["integrity"]["tools"]}
    new_hash = manifest_hash(manifest)
    if new_hash != prov["proposed_manifest_sha256"]:
        raise AdapterRefusal("integrity mismatch — CCI tampered or malformed")

    agent_id = prov["agent_id"]
    expected_prev = _anchor_token(cci["rollback_target"])
    current = pins[agent_id]["tools"]
    if current != expected_prev:
        raise AdapterRefusal(
            "pin drifted since proposal (CAS failure): expected "
            f"{expected_prev[:12]}, found {current[:12]} — re-propose")

    anchor_put(anchors, manifest)
    new_pins = {**pins, agent_id: {**pins[agent_id], "tools": new_hash}}
    record = {
        "record_id": f"dep-{cci['id']}",
        "cci_id": cci["id"],
        "authorization_ref": f"authz:{cci['id']}",
        "deployed_version": f"lc:{agent_id}#tools@{new_hash}",
        "previous_version": cci["rollback_target"],
        "status": "live",
    }
    return new_pins, record


def execute_rollback_tools(cci: dict, deployment_record: dict,
                           pins: dict, anchors: dict,
                           reason: str) -> tuple[dict, dict]:
    agent_id = cci["provenance"]["agent_id"]
    target = _anchor_token(cci["rollback_target"])
    if target not in anchors:
        raise AdapterRefusal(
            "rollback anchor unresolvable — manufactured immutability violated "
            "(SAO-RBK-001)")
    new_pins = {**pins, agent_id: {**pins[agent_id], "tools": target}}
    record = {
        "cci_id": cci["id"],
        "deployment_ref": deployment_record["record_id"],
        "rollback_target": cci["rollback_target"],
        "reason": reason,
        "status": "executed",
    }
    return new_pins, record


def apply_authorized_memory(cci: dict, authorization: dict,
                            store: dict, anchors: dict) -> tuple[dict, dict]:
    """CAS upsert of a durable memory entry. The superseded value is anchored
    at swap time, so the rollback anchor is resolvable by construction."""
    _require_allow(cci, authorization)
    prov = cci["provenance"]
    ns, key = prov["namespace"], prov["key"]
    declared_prior = _anchor_token(cci["rollback_target"])

    current = store.get(ns, {}).get(key)
    current_token = sha256_hex(current["value"]) if current else ABSENT
    if current_token != declared_prior:
        raise AdapterRefusal(
            "memory drifted since proposal (CAS failure): expected prior "
            f"{declared_prior[:12]}, found {current_token[:12]} — re-propose")

    if current is not None:
        # Content-addressed by the value's own hash — the same token the
        # rollback anchor declares, so reversal resolves by construction.
        anchors[current_token] = {"value": current["value"]}

    new_ns = {**store.get(ns, {}), key: {"value": prov["content"],
                                         "cci_id": cci["id"]}}
    new_store = {**store, ns: new_ns}
    record = {
        "record_id": f"dep-{cci['id']}",
        "cci_id": cci["id"],
        "authorization_ref": f"authz:{cci['id']}",
        "deployed_version": f"lc:{prov['agent_id']}#memory/{ns}/{key}@"
                            f"{prov['value_sha256']}",
        "previous_version": cci["rollback_target"],
        "status": "live",
    }
    return new_store, record


def execute_rollback_memory(cci: dict, deployment_record: dict,
                            store: dict, anchors: dict,
                            reason: str) -> tuple[dict, dict]:
    """Restore the anchored prior value, or delete the key if the anchor is
    the ABSENT sentinel (the key did not exist before this CCI)."""
    prov = cci["provenance"]
    ns, key = prov["namespace"], prov["key"]
    target = _anchor_token(cci["rollback_target"])

    ns_entries = dict(store.get(ns, {}))
    if target == ABSENT:
        ns_entries.pop(key, None)
    else:
        anchored = anchors.get(target)
        if anchored is None:
            raise AdapterRefusal(
                "rollback anchor unresolvable — manufactured immutability "
                "violated (SAO-RBK-001)")
        ns_entries[key] = {"value": anchored["value"]}
    new_store = {**store, ns: ns_entries}
    record = {
        "cci_id": cci["id"],
        "deployment_ref": deployment_record["record_id"],
        "rollback_target": cci["rollback_target"],
        "reason": reason,
        "status": "executed",
    }
    return new_store, record


def enforce_tools(manifest: dict, live_specs: list[dict]) -> list[str]:
    """Fail-closed allowlist at agent construction. Refuses on unlisted live
    tools, missing manifest tools, and ANY identity drift — including the
    description hash, because a mutated description is a mutated behaviour
    surface. Returns the manifest-ordered tool names to construct with."""
    live = {s["name"]: identity(s) for s in live_specs}
    pinned = {t["name"]: t for t in manifest["tools"]}

    unlisted = sorted(live.keys() - pinned.keys())
    if unlisted:
        raise AdapterRefusal(f"unlisted live tools (fail closed): {unlisted}")
    missing = sorted(pinned.keys() - live.keys())
    if missing:
        raise AdapterRefusal(f"manifest tools missing from runtime: {missing}")

    for name, expected in pinned.items():
        got = live[name]
        if got != expected:
            drifted = sorted(k for k in expected if expected[k] != got[k])
            raise AdapterRefusal(
                f"identity drift on tool {name!r}: {drifted} "
                "(description drift is a behaviour-surface change)")
    return [t["name"] for t in manifest["tools"]]


# ----------------------------------------------------------------------------
# Fixture loading (shared by demo and tests)
# ----------------------------------------------------------------------------

def load_fixture(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    agent_id = data["agent_id"]
    pinned_specs = [tool_spec(**s) for s in data["pinned_tools"]]
    live_specs = [tool_spec(**s) for s in data["live_tools"]]
    anchors: dict = {}
    pinned_hash = anchor_put(anchors, build_manifest(agent_id, pinned_specs))
    return {
        "agent_id": agent_id,
        "live_specs": live_specs,
        "pins": {agent_id: {"tools": pinned_hash}},
        "anchors": anchors,
        "store": json.loads(canonical(data["memory_store"])),
        "proposals": data["memory_proposals"],
    }


# ----------------------------------------------------------------------------
# Demo (offline, deterministic)
# ----------------------------------------------------------------------------

def _demo() -> None:
    here = Path(__file__).resolve().parent
    fx = load_fixture(here / "fixtures" / "runtime_snapshot.json")

    delta = observe_tools(fx["agent_id"], fx["live_specs"],
                          fx["pins"], fx["anchors"])
    assert delta is not None
    raw = collect_tools(delta, fx["live_specs"], fx["anchors"])
    evidence = normalize_tools(delta, raw)
    cci = propose_tools(delta, raw, evidence)
    print(f"[observe]   tools: +{list(delta.added)} ~{list(delta.modified)} "
          f"-{list(delta.removed)}  widening={delta.widening}")
    print(f"[propose]   {cci['id']}  class={cci['class']}")
    print(f"            rollback_target=...@{delta.pinned_hash[:12]}")

    for mdelta in observe_memory(fx["agent_id"], fx["proposals"], fx["store"]):
        mcci = propose_memory(mdelta, normalize_memory(mdelta))
        print(f"[propose]   {mcci['id']}  class={mcci['class']}  "
              f"prior={'present' if mdelta.prior_present else 'absent'}")
    print("--- lifecycle ownership now passes to the control plane ---")


if __name__ == "__main__":
    _demo()
