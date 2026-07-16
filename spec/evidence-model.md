<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# Evidence Model

**Status:** Normative · **Spec:** v1.0.0-draft.1 (seed)

Evidence is the currency of evolution (SAO-EVD-001). Each Evidence record
is typed (`registry/evidence-types/`), attributed to a source and a
collector, and bound to its payload by hash (`payload_hash`), making it
tamper-evident and replayable by auditors.

Evidence never expires from the ledger; policies MAY discount evidence by
age or provenance, but MUST do so declaratively.
