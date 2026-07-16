<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# impl/reference-python/

**Status:** Non-normative · **Layer:** Demonstration · **Spec:** v1.0.0-draft.1

Readable Python implementation of the full lifecycle. Module layout is 1:1 with the pipeline stages in `spec/update-lifecycle.md` so the crosswalk spec → schema → code needs no map.

## What belongs here

- One package directory per stage; `tests/` runs unit tests plus the conformance vectors

## What must NOT go here

- Performance tricks that obscure the spec crosswalk
