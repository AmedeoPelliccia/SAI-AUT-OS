<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# Versioning

**Status:** Normative (project law) · **Spec:** v1.0.0-draft.1

Three independent semver streams — deliberately decoupled:

| Stream | Governs | Carried where |
|---|---|---|
| Specification | Normative text + conformance meaning | `spec/`, this seed: v1.0.0-draft.1 |
| Schemas | Wire/interop compatibility | `$id` URN of each schema |
| Implementations | Reference impl and each SDK | Their own package versions |

Rules:

- Conformance claims are made **against a specification version**
  (e.g. "Conformant SAI-AUT-OS L1 · spec 1.x"), never against an SDK.
- Schema MAJOR bumps require a spec amendment; MINOR additions must be
  backward-compatible; nothing is ever removed within a MAJOR.
- Ratified spec text is immutable; change happens only by superseding
  amendment (`constitution/AMENDMENT-PROCESS.md`).
- Pre-1.0 drafts carry `-draft.N` and confer no conformance rights.
