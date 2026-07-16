<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# schemas/ — Machine-Readable Schemas

**Status:** Normative · **Layer:** Interoperability · **Spec:** v1.0.0-draft.1

JSON Schema (draft 2020-12) definitions of every record in the standard. This is the surface vendors implement: interoperability is judged against these schemas, not against prose. `$id` URNs carry the version (VERSIONING.md).

## What belongs here

- `cci.schema.json` — the atom of CCM
- `evidence`, `policy`, `authorization`, `deployment-record`, `rollback`, `ledger`, `runtime-context` schemas

## What must NOT go here

- Vendor extensions (use `x-` prefixed fields in your documents)
