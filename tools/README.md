<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# tools/ — Deterministic Tooling

**Status:** Meta · **Layer:** Meta · **Spec:** v1.0.0-draft.1

Generators and validators. `scaffold.py` is the single source of truth for repository structure: change the generator, not the tree. CI runs `python tools/scaffold.py --check` as a structural conformance gate — the repository is the first configuration item governed by its own standard.

## What belongs here

- `scaffold.py` — deterministic structure generator + `--check` gate
- `validate_cci.py` (planned) — validate documents against `schemas/`
