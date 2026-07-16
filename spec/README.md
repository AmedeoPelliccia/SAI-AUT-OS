<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# spec/ — The SAI-AUT-OS Specification

**Status:** Normative · **Layer:** Specification · **Spec:** v1.0.0-draft.1

The normative heart of the standard. RFC 2119 / RFC 8174 keywords apply throughout. Every normative statement carries a stable requirement ID of the form `SAO-<AREA>-<NNN>`; conformance tests reference IDs, never prose.

## What belongs here

- `SAIAUTOS-SPEC.md` — the consolidated specification (entry point)
- `terminology.md` — the controlled vocabulary
- `architecture.md`, `update-lifecycle.md`, `policy-language.md`, `evidence-model.md`, `conformance-model.md` — normative modules
- `amendments/` — ratified amendments only
- `rfcs/` — candidate proposals, not yet ratified

## What must NOT go here

- Tutorials, marketing, comparisons (→ `docs/`)
- Implementation detail of any particular runtime (→ `impl/`, `sdk/`)

## Reading order

1. `terminology.md` → 2. `architecture.md` → 3. `update-lifecycle.md`
→ 4. `evidence-model.md` → 5. `policy-language.md`
→ 6. `conformance-model.md` → 7. `SAIAUTOS-SPEC.md` (consolidated).
