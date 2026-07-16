<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# Registry — Authority Levels

**Status:** Normative · **Layer:** Interoperability · **Spec:** v1.0.0-draft.1

Reservation rules: new entries MUST be added only via a ratified RFC
(see `spec/rfcs/`). Entries are never deleted — they are deprecated by
amendment and remain resolvable forever. IDs are lowercase kebab-case.

| ID | Name | Description | Status | Defined by |
|---|---|---|---|---|
| `a0-automatic` | Automatic | Policy-only authorization; reversible, low-impact classes | seed | RFC-0000 |
| `a1-gated` | Gated | Deterministic gates must pass; no human in the loop | seed | RFC-0000 |
| `a2-human-ratified` | Human-Ratified | A named, accountable human ratifies | seed | RFC-0000 |
| `a3-external-authority` | External Authority | Domain/regulatory authority attestation required | seed | RFC-0000 |
