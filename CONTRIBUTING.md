<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# Contributing

**Status:** Project law (seed) · **Spec:** v1.0.0-draft.1

## The one rule that is different here

The repository **structure** is a controlled artifact. Its single source of
truth is [`tools/scaffold.py`](tools/scaffold.py). To add, move, or remove a
controlled directory or seed file, change the generator first — CI runs
`python tools/scaffold.py --check` and fails on structural drift.

## How changes flow (specification-first)

1. **Normative changes** (spec text, schemas, registries, conformance):
   open an RFC in `spec/rfcs/` using `0000-template.md`. Ratification per
   `GOVERNANCE.md`; ratified text lands as an amendment, never as a rewrite.
2. **Non-normative changes** (impl, sdk, adapters, docs, examples):
   ordinary pull requests. They MUST NOT change normative meaning.
3. **Registry entries**: RFC required. Entries are never deleted, only
   deprecated.

## Requirement identifiers

Every normative statement carries a stable ID (`SAO-<AREA>-<NNN>`).
Reference IDs, not prose, in tests, issues, and commits.
