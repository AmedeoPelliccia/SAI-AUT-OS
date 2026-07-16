<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# Governance

**Status:** Normative (project law) · **Spec:** v1.0.0-draft.1

## Authority model

| Role | Powers | Accountability |
|---|---|---|
| Contributor | Propose RFCs, patches, registry entries | Signed provenance on every proposal |
| Maintainer | Triage, review, merge non-normative changes | Named in MAINTAINERS list |
| Technical Steering | Ratify RFCs, amendments, registry entries, releases | Recorded vote per decision |
| External Authority | Optional domain sign-off for regulated profiles | Attestation recorded as Evidence |

## The responsibility split

Contributors and AI systems may **propose**. Deterministic pipelines
**calculate** (validation, conformance, structure checks). Accountable
humans **ratify**. No ratification is ever produced by a model.

## Precedence

`constitution/` > `spec/` > `policies/` > implementations. Where texts
conflict, the higher layer prevails and the lower layer is defective.

## Self-hosting rule

This project governs its own evolution with its own standard: RFCs are
candidate updates, ratification is authorization, `CHANGELOG.md` is the
deployment record, and `tools/scaffold.py --check` is a structural
conformance gate enforced in CI.
