<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# Registry — Evidence Types

**Status:** Normative · **Layer:** Interoperability · **Spec:** v1.0.0-draft.1

Reservation rules: new entries MUST be added only via a ratified RFC
(see `spec/rfcs/`). Entries are never deleted — they are deprecated by
amendment and remain resolvable forever. IDs are lowercase kebab-case.

| ID | Name | Description | Status | Defined by |
|---|---|---|---|---|
| `metric` | Metric | A measured quantity with method and unit | seed | RFC-0000 |
| `eval-run` | Evaluation Run | Results of a defined evaluation suite, hash-pinned | seed | RFC-0000 |
| `regression-suite` | Regression Suite | Pass/fail record of a frozen regression set | seed | RFC-0000 |
| `attestation` | Attestation | Signed statement by an external system or authority | seed | RFC-0000 |
| `human-review` | Human Review | Recorded, attributable human judgment | seed | RFC-0000 |
