<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# policies/ — Reference Policy Packs

**Status:** Reference (non-normative content, normative format) · **Layer:** Specification support · **Spec:** v1.0.0-draft.1

Declarative policy packs conforming to `schemas/policy.schema.json`. The packs are starting points, not mandates: conformance requires *a* policy, not *these* policies.

## What belongs here

- `baseline/` — the minimal pack a fresh L1 deployment can adopt
- `regulated/` — human-in-the-loop and external-attestation defaults
- `enterprise/` — organizational controls and separation of duties
- `examples/` — didactic single-purpose policies
