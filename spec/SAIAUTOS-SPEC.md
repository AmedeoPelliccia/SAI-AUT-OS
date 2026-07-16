<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# SAI-AUT-OS Specification

**Version:** 1.0.0-draft.1 · **Status:** Draft (confers no conformance rights)

## 1. Scope

This specification defines Cognitive Configuration Management (CCM): the
objects, records, lifecycle, policy semantics, and conformance model for
governing the evolution of adaptive AI systems. It is model-agnostic,
infrastructure-agnostic, and deployment-agnostic.

## 2. Conformance

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD
NOT, RECOMMENDED, MAY, and OPTIONAL are to be interpreted as described in
RFC 2119 and RFC 8174 when, and only when, they appear in all capitals.

Requirement identifier grammar: `SAO-<AREA>-<NNN>` where AREA ∈
{ COR core · CCI configuration items · EVD evidence · POL policy ·
  AUT authorization · DEP deployment · RBK rollback · LGR ledger ·
  CTX runtime context · LCY lifecycle · CON conformance }.
IDs are stable forever; withdrawn requirements are marked withdrawn,
never reused.

## 3. Terms — see `terminology.md` (normative).

## 4. Architecture — see `architecture.md` (normative).

## 5. Cognitive Configuration Items

- **SAO-CCI-001.** Every candidate update MUST be represented as a CCI
  conforming to `schemas/cci.schema.json`.
- **SAO-CCI-002.** An authorized CCI is immutable; any change MUST be a
  new CCI version referencing its predecessor.

## 6. Evidence — see `evidence-model.md`.

- **SAO-EVD-001.** No CCI SHALL be authorized without at least one
  Evidence record bound to it. *(No evolution without evidence.)*

## 7. Policy — see `policy-language.md`.

- **SAO-POL-001.** Authorization decisions MUST be produced by
  deterministic evaluation of declarative, versioned policy.

## 8. Update lifecycle — see `update-lifecycle.md`.

## 9. Authorization and authority

- **SAO-AUT-001.** Every Authorization record MUST identify the
  accountable authority and its authority level (see
  `registry/authority-levels/`).

## 10. Deployment and rollback

- **SAO-DEP-001.** Every deployment MUST emit a Deployment Record before
  the update is considered live.
- **SAO-RBK-001.** Every CCI MUST declare a `rollback_target` prior to
  deployment; rollback MUST remain executable while the CCI is live.

## 11. Ledger and traceability

- **SAO-LGR-001.** Every lifecycle record MUST be appended to a
  hash-chained, append-only ledger conforming to
  `schemas/ledger.schema.json`.

## 12. Foundation Core

- **SAO-COR-001.** The control plane MUST NOT modify the Foundation Core.

## 13. Conformance levels — see `conformance-model.md` and
`conformance/levels.md`.

*(Seed skeleton. Each section is expanded and ratified via RFC.)*
