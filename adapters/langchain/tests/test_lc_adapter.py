#!/usr/bin/env python3
"""Deterministic tests for the LangChain runtime adapter.

Run from the repository root:

    python adapters/langchain/tests/test_lc_adapter.py

Requires `jsonschema` (pip install jsonschema). No network, no clocks:
identical inputs must yield byte-identical records. Assertions cite the
requirement IDs they exercise, per CONTRIBUTING.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ADAPTER_DIR = HERE.parents[1]          # adapters/langchain/
REPO_ROOT = HERE.parents[3]            # repository root
SCHEMAS = REPO_ROOT / "schemas"

sys.path.insert(0, str(ADAPTER_DIR))

import lc_adapter as lc  # noqa: E402

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


def fixture() -> dict:
    return lc.load_fixture(ADAPTER_DIR / "fixtures" / "runtime_snapshot.json")


def tool_pipeline(fx: dict):
    delta = lc.observe_tools(fx["agent_id"], fx["live_specs"],
                             fx["pins"], fx["anchors"])
    assert delta is not None, "fixture must yield a tool-binding delta"
    raw = lc.collect_tools(delta, fx["live_specs"], fx["anchors"])
    evidence = lc.normalize_tools(delta, raw)
    cci = lc.propose_tools(delta, raw, evidence)
    return delta, raw, evidence, cci


def allow(cci: dict) -> dict:
    authz = {
        "cci_id": cci["id"],
        "policy_id": f"policies/baseline#{cci['class']}",
        "decision": "allow",
        "authority": {"id": "tsc/reviewer-01", "level": "a2-human-ratified"},
        "rationale": "reviewed diff, staging only",
    }
    V_AUTH.validate(authz)
    return authz


def main() -> int:
    print("== T1: observe finds the toolset drift ==")
    fx = fixture()
    delta, raw, evidence, cci = tool_pipeline(fx)
    assert delta.added == ("ticket_create",)
    assert delta.removed == ("legacy_export",)
    assert delta.modified == ("kb_search",)
    assert delta.widening and delta.narrowing
    assert delta.proposed_hash != delta.pinned_hash
    ok("delta = +ticket_create -legacy_export ~kb_search; widening flagged")

    print("== T2: evidence records are schema-valid and hash-bound ==")
    assert len(evidence) >= 1, "SAO-EVD-001: no CCI without at least one Evidence record"
    for record in evidence:
        V_EVIDENCE.validate(record)
        assert len(record["payload_hash"]) == 64, "payload_hash must be SHA-256 hex"
    ok(f"{len(evidence)} records valid against evidence.schema.json (SAO-EVD-001)")

    print("== T3: draft CCI is schema-valid with a declared anchor ==")
    V_CCI.validate(cci)
    assert cci["class"] == "tool-permission-change", "registered update class required"
    assert cci["rollback_target"].endswith(delta.pinned_hash), \
        "SAO-RBK-001: rollback anchor must be declared before deployment"
    assert cci["scope"]["adaptive_component"] == "tool-binding"
    assert delta.pinned_hash in fx["anchors"], \
        "SAO-RBK-001: anchor must resolve in the manufactured history"
    ok("CCI valid against cci.schema.json; anchor = pinned manifest (SAO-RBK-001)")

    print("== T4: determinism — two runs, identical bytes ==")
    _, _, evidence2, cci2 = tool_pipeline(fixture())
    assert lc.canonical(cci) == lc.canonical(cci2)
    assert lc.canonical(evidence) == lc.canonical(evidence2)
    ok("byte-identical canonical output across runs")

    print("== T5: apply refuses without a matching 'allow' authorization ==")
    for bad in (
        {"cci_id": "cci-other", "decision": "allow"},
        {"cci_id": cci["id"], "decision": "deny"},
        {"cci_id": cci["id"], "decision": "escalate"},
        {},
    ):
        try:
            lc.apply_authorized_tools(cci, bad, fx["pins"], fx["anchors"])
            raise AssertionError(f"applied despite authorization={bad!r}")
        except lc.AdapterRefusal:
            pass
    ok("all refusals loud (SAO-AUT-001; grammar per seed spec, RFC-0001 pending)")

    print("== T6: authorized apply = atomic CAS repin + valid Deployment Record ==")
    authz = allow(cci)
    new_pins, deploy = lc.apply_authorized_tools(cci, authz, fx["pins"], fx["anchors"])
    V_DEPLOY.validate(deploy)
    assert new_pins[fx["agent_id"]]["tools"] == delta.proposed_hash
    assert fx["pins"][fx["agent_id"]]["tools"] == delta.pinned_hash, \
        "inputs must not mutate"
    assert deploy["status"] == "live" and deploy["previous_version"] == cci["rollback_target"]
    ok("repin applied; deployment record valid; inputs untouched")

    print("== T7: integrity mismatch — a tampered CCI is refused ==")
    tampered = json.loads(lc.canonical(cci))
    tampered["provenance"]["integrity"]["tools"][0]["side_effects"] = ["execute"]
    try:
        lc.apply_authorized_tools(tampered, allow(tampered), fx["pins"], fx["anchors"])
        raise AssertionError("applied a tampered CCI")
    except lc.AdapterRefusal:
        ok("integrity block re-verified at apply time; tampering refused")

    print("== T8: CAS failure — stale proposal is refused ==")
    drifted = {**fx["pins"], fx["agent_id"]: {"tools": "0" * 64}}
    try:
        lc.apply_authorized_tools(cci, authz, drifted, fx["anchors"])
        raise AssertionError("applied over a drifted pin")
    except lc.AdapterRefusal:
        ok("drifted pin refused — repin is compare-and-swap, hence atomic")

    print("== T9: rollback repins to the anchor + valid Rollback record ==")
    back_pins, rollback = lc.execute_rollback_tools(
        cci, deploy, new_pins, fx["anchors"],
        reason="staging anomaly: unexpected tool routing")
    V_ROLLBACK.validate(rollback)
    assert back_pins[fx["agent_id"]]["tools"] == delta.pinned_hash
    assert rollback["status"] == "executed"
    assert rollback["rollback_target"] == cci["rollback_target"]
    ok("anchor restored (SAO-RBK-001); rollback record valid")

    print("== T10: rollback refuses an unresolvable anchor ==")
    try:
        lc.execute_rollback_tools(cci, deploy, new_pins, {}, reason="x")
        raise AssertionError("rolled back without a resolvable anchor")
    except lc.AdapterRefusal:
        ok("unresolvable anchor refused (SAO-RBK-001)")

    print("== T11: memory observe skips no-ops; drafts are hash-only ==")
    fx = fixture()
    mdeltas = lc.observe_memory(fx["agent_id"], fx["proposals"], fx["store"])
    keys = sorted(d.key for d in mdeltas)
    assert keys == ["timezone", "tone"], f"unexpected candidates: {keys}"
    mccis = {}
    for mdelta in mdeltas:
        mevidence = lc.normalize_memory(mdelta)
        for record in mevidence:
            V_EVIDENCE.validate(record)
            assert mdelta.value not in lc.canonical(record), \
                "evidence must bind memory by hash only, never content"
        mcci = lc.propose_memory(mdelta, mevidence)
        V_CCI.validate(mcci)
        assert mcci["class"] == "memory-update"
        assert mcci["scope"]["adaptive_component"] == "memory"
        mccis[mdelta.key] = mcci
    assert mccis["tone"]["rollback_target"].count("@") == 1
    assert mccis["timezone"]["rollback_target"].endswith(f"@{lc.ABSENT}")
    ok("no-op skipped; 2 memory CCIs valid; hash-only evidence; ABSENT sentinel")

    print("== T12: memory apply = CAS upsert; superseded value anchored ==")
    store, anchors = fx["store"], fx["anchors"]
    tone_cci = mccis["tone"]
    prior_sha = lc._anchor_token(tone_cci["rollback_target"])
    store2, mdeploy = lc.apply_authorized_memory(tone_cci, allow(tone_cci),
                                                 store, anchors)
    V_DEPLOY.validate(mdeploy)
    assert store2["user-prefs"]["tone"]["value"] == "concise and friendly"
    assert store["user-prefs"]["tone"]["value"] == "formal", "inputs must not mutate"
    assert prior_sha in anchors, "superseded value must be anchored at swap time"
    try:
        lc.apply_authorized_memory(tone_cci, allow(tone_cci), store2, anchors)
        raise AssertionError("re-applied over a drifted memory entry")
    except lc.AdapterRefusal:
        pass
    ok("CAS upsert applied; prior anchored; drifted re-apply refused")

    print("== T13: memory rollback restores prior / deletes ABSENT ==")
    store3, mrollback = lc.execute_rollback_memory(
        tone_cci, mdeploy, store2, anchors, reason="user retracted preference")
    V_ROLLBACK.validate(mrollback)
    assert store3["user-prefs"]["tone"]["value"] == "formal"
    assert mrollback["status"] == "executed"
    tz_cci = mccis["timezone"]
    store4, tz_deploy = lc.apply_authorized_memory(tz_cci, allow(tz_cci),
                                                   store3, anchors)
    store5, _ = lc.execute_rollback_memory(tz_cci, tz_deploy, store4, anchors,
                                           reason="scope error")
    assert "timezone" not in store5["user-prefs"], \
        "ABSENT anchor must delete the key on rollback"
    ok("prior value restored; ABSENT rollback deletes the key (SAO-RBK-001)")

    print("== T14: enforce gate — declaration is not authorization ==")
    fx = fixture()
    pinned_manifest = fx["anchors"][fx["pins"][fx["agent_id"]]["tools"]]
    try:
        lc.enforce_tools(pinned_manifest, fx["live_specs"])
        raise AssertionError("unauthorized live toolset reached construction")
    except lc.AdapterRefusal:
        pass
    pinned_specs = [s for s in fx["live_specs"] if s["name"] == "calculator"]
    try:
        lc.enforce_tools(pinned_manifest, pinned_specs)
        raise AssertionError("constructed with manifest tools missing")
    except lc.AdapterRefusal:
        pass
    ok("fail-closed: unlisted and missing tools both refused at construction")

    print("== T15: enforce gate admits an exact match, manifest-ordered ==")
    delta, raw, evidence, cci = tool_pipeline(fx)
    authz = allow(cci)
    new_pins, _ = lc.apply_authorized_tools(cci, authz, fx["pins"], fx["anchors"])
    live_manifest = fx["anchors"][new_pins[fx["agent_id"]]["tools"]]
    names = lc.enforce_tools(live_manifest, fx["live_specs"])
    assert names == [t["name"] for t in live_manifest["tools"]]
    ok("authorized toolset admitted; identity drift (incl. description) gated")

    print(f"\nALL TESTS PASSED ({PASSED}) — 5 seed schemas exercised: "
          "cci, evidence, authorization, deployment-record, rollback")
    return 0


if __name__ == "__main__":
    sys.exit(main())
