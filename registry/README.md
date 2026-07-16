<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# registry/ — Official Registries

**Status:** Normative · **Layer:** Interoperability · **Spec:** v1.0.0-draft.1

Every mature standard maintains official registries — as the Internet has MIME types and IANA registries, SAI-AUT-OS has these. Registries are diffable Markdown tables; entries are added only via ratified RFC and never deleted, only deprecated.

## What belongs here

- `adaptive-components/` — the governable component types
- `update-types/` — the classes a CCI may declare
- `evidence-types/` — the admissible kinds of evidence
- `authority-levels/` — the accountability ladder

## What must NOT go here

- This directory is unrelated to `impl/reference-python/registry/` (a runtime module).
