<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# Conformance Model

**Status:** Normative · **Spec:** v1.0.0-draft.1 (seed)

Conformance is claimed per **level** (L0/L1/L2 — `conformance/levels.md`),
optionally narrowed by **profile** (`conformance/profiles/`), and always
against a named specification version.

A claim is valid only if the implementation passes the corresponding
deterministic test vectors under `conformance/` using the official runner.
Verdicts are calculated, never generated: no model output may decide a
conformance result. Claim wording: `Conformant SAI-AUT-OS L<k> · spec <v>`.
