<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# conformance/runner/

**Status:** Normative tool · **Layer:** Assurance · **Spec:** v1.0.0-draft.1

The official harness. Contract: point it at an implementation endpoint/CLI, it feeds vectors, compares emitted records byte-for-byte after canonicalization, and exits 0 only on a full pass for the claimed level. Verdicts are calculated, never generated.
