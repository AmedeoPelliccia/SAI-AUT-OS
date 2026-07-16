<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# Amendment Process

**Status:** Constitutional · **Spec:** v1.0.0-draft.1

1. **Draft** — an RFC in `spec/rfcs/` marked `constitutional: true`.
2. **Review** — public comment window (minimum to be fixed by Technical
   Steering before 1.0; seed default: 30 days).
3. **Evidence** — impact analysis attached as Evidence records.
4. **Ratification** — supermajority of Technical Steering, recorded vote.
5. **Record** — amendment lands in `spec/amendments/`, changelog updated,
   spec version bumped.

Supersession rules:

- **S1.** Ratified text is immutable.
- **S2.** Change occurs only via a superseding amendment.
- **S3.** Every amendment MUST reference exactly what it supersedes.
