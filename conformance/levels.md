<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# Conformance Levels

**Status:** Normative · **Spec:** v1.0.0-draft.1

| Level | Name | Requires | Claim it earns |
|---|---|---|---|
| L0 | Observed | observe + collect + normalize + hash-chained ledger (SAO-LGR-001) | "No silent evolution." |
| L1 | Governed | L0 + evaluate + validate + authorize under declarative policy (SAO-EVD-001, SAO-POL-001, SAO-AUT-001) | "No evolution without evidence." |
| L2 | Reversible | L1 + deployment records + declared and *verified* rollback (SAO-DEP-001, SAO-RBK-001) | "Every evolution is explainable, traceable and reversible." |

Levels are cumulative. Profiles (see `profiles/`) MAY narrow but never
relax a level. Claims name the level and the spec version:
`Conformant SAI-AUT-OS L2 · spec 1.x`.
