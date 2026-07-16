#!/usr/bin/env python3
"""Deterministic tests for the HuggingFace adapter.

Run from the repository root:

    python adapters/huggingface/tests/test_hf_adapter.py

Requires `jsonschema` (pip install jsonschema). No network, no clocks:
identical inputs must yield byte-identical records. Assertions cite the
requirement IDs they exercise, per CONTRIBUTING.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ADAPTER_DIR = HERE.parents[1]          # adapters/huggingface/
REPO_ROOT = HERE.parents[3]            # repository root
SCHEMAS = REPO_ROOT / "schemas"

sys.path.insert(0, str(ADAPTER_DIR))

import hf_adapter as hf  # noqa: E402

from jsonschema import Draft202012Validator  # noqa: E402


def load_validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


V_CCI = load_validator("cci")
V_EVIDENCE = load_validator("evidence")
V_AUTH = load_validator("authorization")
V_DEPLOY = load_validator("deployment-record")
V_ROLLBACK = load_validator("rollback")

PASSED = 0


def ok(label: str) -> None:
    global PASSED
    PASSED += 1
    print(f"  [pass] {label}")


def pipeline():
    client = hf.SnapshotClient.from_file(ADAPTER_DIR / "fixtures" / "hub_snapshot.json")
    pins = client.pins
    cands = hf.observe(client, pins)
    assert len(cands) == 1, "fixture must yield exactly one candidate"
    cand = cands[0]
    raw = hf.collect(client, cand)
    evidence = hf.normalize(cand, raw)
    cci = hf.propose(cand, raw, evidence)
    return client, pins, cand, evidence, cci


def main() -> int:
    print("== T1: observe finds the moved head ==")
    client, pins, cand, evidence, cci = pipeline()
    assert cand.repo_id == "acme/legalese-lora"
    assert cand.pinned_sha != cand.head_sha
    ok("candidate = pinned SHA != head SHA")

    print("== T2: evidence records are schema-valid and hash-bound ==")
    assert len(evidence) >= 1, "SAO-EVD-001: no CCI without at least one Evidence record"
    for record in evidence:
        V_EVIDENCE.validate(record)
        assert len(record["payload_hash"]) == 64, "payload_hash must be SHA-256 hex"
    types = sorted({r["type"] for r in evidence})
    assert types == ["attestation", "metric"], f"unexpected evidence types: {types}"
    ok(f"{len(evidence)} records valid against evidence.schema.json (SAO-EVD-001)")

    print("== T3: draft CCI is schema-valid with a resolvable anchor ==")
    V_CCI.validate(cci)
    assert cci["class"] == "lora-adapter-promotion", "registered update class required"
    assert cci["rollback_target"].endswith(cand.pinned_sha), \
        "SAO-RBK-001: rollback anchor must be declared before deployment"
    assert cci["scope"]["adaptive_component"] == "lora-adapter"
    ok("CCI valid against cci.schema.json; anchor = pinned revision (SAO-RBK-001)")

    print("== T4: determinism — two runs, identical bytes ==")
    _, _, _, evidence2, cci2 = pipeline()
    assert hf.canonical(cci) == hf.canonical(cci2)
    assert hf.canonical(evidence) == hf.canonical(evidence2)
    ok("byte-identical canonical output across runs")

    print("== T5: apply refuses without a matching 'allow' authorization ==")
    for bad in (
        {"cci_id": "cci-other", "decision": "allow"},
        {"cci_id": cci["id"], "decision": "deny"},
        {"cci_id": cci["id"], "decision": "escalate"},
        {},
    ):
        try:
            hf.apply_authorized(cci, bad, pins)
            raise AssertionError(f"applied despite authorization={bad!r}")
        except hf.AdapterRefusal:
            pass
    ok("all refusals loud (SAO-AUT-001; grammar per seed spec, RFC-0001 pending)")

    print("== T6: authorized apply = atomic CAS repin + valid Deployment Record ==")
    authz = {
        "cci_id": cci["id"],
        "policy_id": "policies/baseline#lora-adapter-promotion",
        "decision": "allow",
        "authority": {"id": "tsc/reviewer-01", "level": "a2-human-ratified"},
        "rationale": "metrics improved, integrity verified, staging only",
    }
    V_AUTH.validate(authz)
    new_pins, deploy = hf.apply_authorized(cci, authz, pins)
    V_DEPLOY.validate(deploy)
    assert new_pins["acme/legalese-lora"]["sha"] == cand.head_sha
    assert pins["acme/legalese-lora"]["sha"] == cand.pinned_sha, "inputs must not mutate"
    assert deploy["status"] == "live" and deploy["previous_version"] == cci["rollback_target"]
    ok("repin applied; deployment record valid; inputs untouched")

    print("== T7: CAS failure — stale proposal is refused ==")
    drifted = {**pins, "acme/legalese-lora": {**pins["acme/legalese-lora"],
                                              "sha": "0" * 40}}
    try:
        hf.apply_authorized(cci, authz, drifted)
        raise AssertionError("applied over a drifted pin")
    except hf.AdapterRefusal:
        ok("drifted pin refused — repin is compare-and-swap, hence atomic")

    print("== T8: rollback repins to the anchor + valid Rollback record ==")
    back_pins, rollback = hf.execute_rollback(cci, deploy, new_pins,
                                              reason="staging anomaly: latency regression")
    V_ROLLBACK.validate(rollback)
    assert back_pins["acme/legalese-lora"]["sha"] == cand.pinned_sha
    assert rollback["status"] == "executed"
    assert rollback["rollback_target"] == cci["rollback_target"]
    ok("anchor restored (SAO-RBK-001); rollback record valid")

    print(f"\nALL TESTS PASSED ({PASSED}) — 5 seed schemas exercised: "
          "cci, evidence, authorization, deployment-record, rollback")
    return 0


if __name__ == "__main__":
    sys.exit(main())
