<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# Policy Language

**Status:** Normative · **Spec:** v1.0.0-draft.1 (seed)

Policies are declarative, versioned documents conforming to
`schemas/policy.schema.json`. Evaluation is deterministic (SAO-POL-001):
identical CCI + identical evidence + identical policy ⇒ identical decision.

A policy binds: (a) the update classes it applies to, (b) the evidence
types and thresholds required, (c) the validation gates, and (d) the
minimum authority level for authorization. Reference packs live in
`policies/`.

*(Seed. The full rule grammar is defined via RFC before 1.0.)*
