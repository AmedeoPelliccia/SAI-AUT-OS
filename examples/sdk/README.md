<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# sdk/ — SDKs

**Status:** Non-normative · **Layer:** Adoption · **Spec:** v1.0.0-draft.1

Developer-experience libraries for adopting the standard. SDKs exist for developers; the reference implementation exists to demonstrate conformance — the two are deliberately separate. Every SDK targets conformance L1 by default and MUST state the spec version it tracks.

## What belongs here

- `python/` (first), `rust/`, `go/`, `typescript/`

## What must NOT go here

- Normative behavior not present in `spec/` — SDKs never extend the standard silently
