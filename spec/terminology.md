<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# Terminology

**Status:** Normative · **Spec:** v1.0.0-draft.1

| Term | Definition |
|---|---|
| Cognitive Configuration Management (CCM) | The discipline of governing the evolution of adaptive AI systems through controlled configuration items, evidence, declarative policy, accountable authorization, and guaranteed reversibility. |
| Evolution Control Plane | The governance layer that decides whether a candidate evolution is allowed, independent of any model or runtime. |
| Foundation Core | The immutable base of a governed system (e.g. base model weights). Never modified by the control plane. |
| Adaptive Component | A mutable part of the system under governance: memory, LoRA/adapters, RAG indexes, tool bindings, prompt profiles. Types are registered in `registry/adaptive-components/`. |
| Cognitive Configuration Item (CCI) | The governed unit of evolution: one candidate update with provenance, scope, effectivity, evidence, validation, authorization, version, deployment history, and rollback target. |
| Evidence | A verifiable, hash-bound record supporting or opposing a CCI. Types registered in `registry/evidence-types/`. |
| Update Class | The registered category of a CCI (`registry/update-types/`), which policies key on. |
| Authority Level | The registered accountability tier required to authorize a CCI (`registry/authority-levels/`). |
| Effectivity | The declared scope in which a CCI applies (systems, environments, time windows). |
| Ledger | The append-only, hash-chained trace of all lifecycle records. |
| Rollback Target | The exact prior configuration a deployed CCI can be reverted to. |
