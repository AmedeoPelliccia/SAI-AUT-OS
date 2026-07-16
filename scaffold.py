#!/usr/bin/env python3
"""
scaffold.py — deterministic repository scaffold generator for SAI-AUT-OS.

    SAI-AUT-OS — Selective AI for Autonomous Upgrade and Tuning
    The open standard for Cognitive Configuration Management (CCM).

This generator is the SINGLE SOURCE OF TRUTH for the repository structure.
Structural changes to the repository MUST be made here first; CI enforces
this via `python tools/scaffold.py --check` (see .github/workflows/).

Guarantees
----------
* Deterministic : identical bytes on every run — no clocks, no randomness,
                  no environment-dependent content. stdlib only.
* Idempotent    : re-running against an existing tree creates nothing new
                  and changes nothing (existing files are skipped).
* Non-destructive: existing files are never overwritten unless --force.
* Self-verifying: --check validates that every controlled path exists;
                  --manifest emits a SHA-256 evidence record of all seeds.

Usage
-----
    python tools/scaffold.py                      # scaffold into CWD (repo root)
    python tools/scaffold.py --root /path/to/repo
    python tools/scaffold.py --check              # structural conformance (CI gate)
    python tools/scaffold.py --manifest seed.json # SHA-256 manifest of seed set
    python tools/scaffold.py --list               # print controlled paths
    python tools/scaffold.py --force              # re-seed (overwrites!)

Exit codes: 0 = OK · 1 = check failed (missing controlled paths) · 2 = usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import textwrap
from pathlib import Path

# ----------------------------------------------------------------------------
# Controlled constants (the only place versions are declared)
# ----------------------------------------------------------------------------

STANDARD = "SAI-AUT-OS"
SPEC_VERSION = "1.0.0-draft.1"      # version of the specification seed
SCAFFOLD_VERSION = "0.2.0"          # version of this generator
TAGLINE = "The open standard for Cognitive Configuration Management (CCM)."
MOTTO = "Specification before implementation. Governance before evolution."

SEED_MD = f"<!-- sai-aut-os:seed scaffold={SCAFFOLD_VERSION} spec={SPEC_VERSION} -->"
SEED_HASH = f"# sai-aut-os:seed scaffold={SCAFFOLD_VERSION} spec={SPEC_VERSION}"

FILES: dict[str, str] = {}  # rel POSIX path -> exact file content (ordered)


# ----------------------------------------------------------------------------
# Content helpers
# ----------------------------------------------------------------------------

def T(s: str) -> str:
    """Dedent a block, strip outer blank lines, guarantee one trailing newline."""
    return textwrap.dedent(s).strip("\n") + "\n"


def add(rel: str, content: str) -> None:
    """Register a controlled file. @SPEC@/@SCAF@ placeholders are resolved here."""
    if rel in FILES:
        raise ValueError(f"duplicate controlled path: {rel}")
    FILES[rel] = (
        content.replace("@SPEC@", SPEC_VERSION).replace("@SCAF@", SCAFFOLD_VERSION)
    )


def readme(rel: str, title: str, status: str, layer: str, purpose: str,
           holds: list[str] | None = None, not_here: list[str] | None = None,
           extra: str | None = None) -> None:
    """Seed a controlled README.md with a consistent identity header."""
    lines = [
        SEED_MD,
        "",
        f"# {title}",
        "",
        f"**Status:** {status} · **Layer:** {layer} · **Spec:** v@SPEC@",
        "",
        purpose.strip(),
        "",
    ]
    if holds:
        lines += ["## What belongs here", ""] + [f"- {h}" for h in holds] + [""]
    if not_here:
        lines += ["## What must NOT go here", ""] + [f"- {n}" for n in not_here] + [""]
    if extra:
        lines += [extra.strip(), ""]
    add(rel, "\n".join(lines).strip("\n") + "\n")


def schema(name: str, title: str, desc: str,
           required: list[str], props: dict) -> None:
    """Seed a machine-readable JSON Schema stub (draft 2020-12, URN-versioned)."""
    doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"urn:sai-aut-os:schema:{name}:{SPEC_VERSION}",
        "title": title,
        "description": desc + " Seed stub — normative fields pending ratification.",
        "type": "object",
        "required": required,
        "properties": props,
        "additionalProperties": True,
        "x-sao-status": "seed",
        "x-sao-spec": SPEC_VERSION,
    }
    add(f"schemas/{name}.schema.json",
        json.dumps(doc, indent=2, sort_keys=True) + "\n")


def registry_file(rel: str, title: str, rows: list[tuple[str, str, str]]) -> None:
    """Seed an official registry as a diffable Markdown table (IANA-style)."""
    lines = [
        SEED_MD,
        "",
        f"# Registry — {title}",
        "",
        f"**Status:** Normative · **Layer:** Interoperability · **Spec:** v@SPEC@",
        "",
        "Reservation rules: new entries MUST be added only via a ratified RFC",
        "(see `spec/rfcs/`). Entries are never deleted — they are deprecated by",
        "amendment and remain resolvable forever. IDs are lowercase kebab-case.",
        "",
        "| ID | Name | Description | Status | Defined by |",
        "|---|---|---|---|---|",
    ]
    for rid, rname, rdesc in rows:
        lines.append(f"| `{rid}` | {rname} | {rdesc} | seed | RFC-0000 |")
    add(rel, "\n".join(lines) + "\n")


# ============================================================================
# 1. ROOT — project identity and project-law files
# ============================================================================

add("README.md", T("""
    """ + SEED_MD + """

    # SAI-AUT-OS

    **Selective AI for Autonomous Upgrade and Tuning**

    > """ + TAGLINE + """

    **Motto.** *""" + MOTTO + """*

    **Status:** Specification v@SPEC@ (draft) · pre-1.0 · structure controlled by
    [`tools/scaffold.py`](tools/scaffold.py)

    ---

    ## What is Cognitive Configuration Management?

    **Cognitive Configuration Management (CCM)** is the discipline of governing
    the evolution of adaptive AI systems through controlled configuration items,
    evidence, declarative policy, accountable authorization, and guaranteed
    reversibility. SAI-AUT-OS defines CCM the way Kubernetes defined container
    orchestration and OpenTelemetry defined telemetry: as an open, vendor-neutral
    standard, not a product.

    SAI-AUT-OS is **not** a foundation model and **not** an agent framework.
    It is an **Evolution Control Plane**: any model, any framework, any cloud,
    any runtime.

    ## Specification-first

    ```mermaid
    flowchart TD
        A[Specification] --> B[Schemas]
        B --> C[Conformance]
        C --> D[SDKs]
        D --> E[Reference Implementation]
        E --> F[Integrations]
    ```

    Everything downstream exists to serve the specification — never the reverse.

    ## Repository map

    | Path | Layer | Purpose |
    |---|---|---|
    | [`constitution/`](constitution/) | Constitutional | Technical Constitution for AI evolution — the founding, precedence-setting documents |
    | [`spec/`](spec/) | Normative | The SAI-AUT-OS specification, terminology, amendments, and RFCs |
    | [`schemas/`](schemas/) | Normative | Machine-readable JSON Schemas — the interoperability surface |
    | [`policies/`](policies/) | Reference | Declarative policy packs (baseline, regulated, enterprise) |
    | [`conformance/`](conformance/) | Assurance | Conformance levels, profiles, test vectors, golden datasets, runner |
    | [`registry/`](registry/) | Interoperability | Official registries: update types, evidence types, authority levels, adaptive components |
    | [`sdk/`](sdk/) | Adoption | Developer SDKs (Python, Rust, Go, TypeScript) |
    | [`impl/`](impl/) | Demonstration | Reference implementation — proves conformance, nothing more |
    | [`adapters/`](adapters/) | Integration | Ecosystem bindings (HF, vLLM, LangChain, MCP, vector stores…) |
    | [`telemetry/`](telemetry/) | Integration | Evidence collectors, exporters, OpenTelemetry bridge |
    | [`examples/`](examples/) | Demonstration | End-to-end governed-update walkthroughs |
    | [`docs/`](docs/) | Informative | Non-normative guides, FAQ, comparisons |
    | [`tools/`](tools/) | Meta | Deterministic generators and validators |

    ## Governance in one line

    Contributors and AI systems may **propose**. Deterministic pipelines
    **calculate**. Accountable humans **ratify**. See
    [`GOVERNANCE.md`](GOVERNANCE.md) and the
    [`constitution/`](constitution/).

    ## Manifesto

    The full public manifesto — vision, lifecycle, CCI model, decision grammar,
    conformance ladder — is authored in [`docs/manifesto.md`](docs/manifesto.md).
    This README carries only the controlled identity of the standard.
    """))

add("LICENSE", T("""
    SAI-AUT-OS — LICENSING DECLARATION (SEED)

    Intended licensing model (to be finalized before first tagged release):

      * Code (impl/, sdk/, adapters/, telemetry/, tools/, conformance/runner/):
          Apache License 2.0
      * Specification text, constitution, schemas, registries, documentation:
          Creative Commons Attribution 4.0 International (CC BY 4.0)

    ACTION REQUIRED: replace this seed with the canonical license texts as
    LICENSE-APACHE and LICENSE-CC-BY-4.0, and update this file to point to
    both, before any release is tagged. No release may ship this seed.
    """))

add("GOVERNANCE.md", T("""
    """ + SEED_MD + """

    # Governance

    **Status:** Normative (project law) · **Spec:** v@SPEC@

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
    """))

add("CODE_OF_CONDUCT.md", T("""
    """ + SEED_MD + """

    # Code of Conduct

    **Status:** Project law (seed)

    This project adopts the Contributor Covenant, v2.1.

    ACTION REQUIRED: replace this seed with the full Contributor Covenant v2.1
    text (https://www.contributor-covenant.org) and designate the enforcement
    contact before opening the repository to external contribution.
    """))

add("CONTRIBUTING.md", T("""
    """ + SEED_MD + """

    # Contributing

    **Status:** Project law (seed) · **Spec:** v@SPEC@

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
    """))

add("SECURITY.md", T("""
    """ + SEED_MD + """

    # Security Policy

    **Status:** Project law (seed)

    Report vulnerabilities privately to the security contact (ACTION REQUIRED:
    designate address before first release). Do not open public issues for
    exploitable findings.

    Scope of interest, in priority order: (1) integrity of the ledger hash
    chain, (2) policy-bypass paths in the authorize stage, (3) evidence forgery
    or replay, (4) rollback-target corruption, (5) supply chain of the
    reference implementation and SDKs.

    Coordinated disclosure target: 90 days.
    """))

add("VERSIONING.md", T("""
    """ + SEED_MD + """

    # Versioning

    **Status:** Normative (project law) · **Spec:** v@SPEC@

    Three independent semver streams — deliberately decoupled:

    | Stream | Governs | Carried where |
    |---|---|---|
    | Specification | Normative text + conformance meaning | `spec/`, this seed: v@SPEC@ |
    | Schemas | Wire/interop compatibility | `$id` URN of each schema |
    | Implementations | Reference impl and each SDK | Their own package versions |

    Rules:

    - Conformance claims are made **against a specification version**
      (e.g. "Conformant SAI-AUT-OS L1 · spec 1.x"), never against an SDK.
    - Schema MAJOR bumps require a spec amendment; MINOR additions must be
      backward-compatible; nothing is ever removed within a MAJOR.
    - Ratified spec text is immutable; change happens only by superseding
      amendment (`constitution/AMENDMENT-PROCESS.md`).
    - Pre-1.0 drafts carry `-draft.N` and confer no conformance rights.
    """))

add("CHANGELOG.md", T("""
    """ + SEED_MD + """

    # Changelog

    Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
    This file doubles as the project's own deployment record.

    ## [Unreleased]

    ### Added
    - Deterministic repository scaffold (seed set, scaffold v@SCAF@, spec v@SPEC@).
    - Public manifesto surface: controlled stub at `docs/manifesto.md`, linked
      from the root README identity block.
    """))

add(".gitattributes", T("""
    """ + SEED_HASH + """
    # LF everywhere: byte-determinism of the seed set depends on it.
    * text eol=lf
    *.png binary
    *.jpg binary
    *.pdf binary
    """))


# ============================================================================
# 2. CONSTITUTION — the founding layer
# ============================================================================

readme(
    "constitution/README.md",
    "constitution/ — Technical Constitution for AI Evolution",
    "Constitutional (highest precedence)", "Foundational",
    "The founding documents of SAI-AUT-OS. This is not a specification: it is "
    "the layer that constrains all specifications, policies, and "
    "implementations. Where any lower text conflicts with the constitution, "
    "the lower text is defective.",
    holds=[
        "`AI-CONSTITUTION.md` — articles binding every conformant system",
        "`GOVERNANCE-PRINCIPLES.md` — the principles behind the articles",
        "`RIGHTS-AND-RESPONSIBILITIES.md` — actors, their rights, their duties",
        "`AMENDMENT-PROCESS.md` — how this layer itself may evolve",
    ],
    not_here=[
        "Technical mechanisms (those live in `spec/`)",
        "Anything amendable without due process",
    ],
)

add("constitution/AI-CONSTITUTION.md", T("""
    """ + SEED_MD + """

    # The Technical Constitution for AI Evolution

    **Status:** Constitutional · **Spec:** v@SPEC@ (seed articles)

    ## Preamble

    True freedom is not the absence of rules. True freedom is
    self-determination. An intelligent system should not evolve because it
    *can*; it should evolve because its evolution follows transparent,
    accountable and reversible rules. This constitution exists to make
    autonomous AI evolution trustworthy.

    ## Articles

    **Article I — Immutability of the Foundation Core.**
    The Foundation Core of a governed system MUST NOT be modified by the
    evolution control plane. Only adaptive components evolve.

    **Article II — No evolution without evidence.**
    No candidate update SHALL be authorized without at least one verifiable
    Evidence record bound to it.

    **Article III — No evolution without policy.**
    Every authorization decision MUST result from the deterministic evaluation
    of declarative, versioned policy — never from ad-hoc judgment.

    **Article IV — No authorization without accountable authority.**
    Every authorization MUST record the accountable authority that produced
    it. A model may propose; a model never ratifies.

    **Article V — No deployment without reversibility.**
    Every deployed update MUST declare a rollback target before deployment,
    and rollback MUST remain executable for as long as the update is live.

    **Article VI — Total traceability.**
    Every record of the lifecycle MUST be appended to a tamper-evident,
    hash-chained ledger. Nothing evolves silently.

    **Article VII — Amendment by due process only.**
    Ratified text is immutable. Change occurs only through superseding
    amendments that reference what they supersede. History is never rewritten.

    **Article VIII — Precedence.**
    Constitution over specification; specification over policy; policy over
    implementation.
    """))

add("constitution/GOVERNANCE-PRINCIPLES.md", T("""
    """ + SEED_MD + """

    # Governance Principles

    **Status:** Constitutional · **Spec:** v@SPEC@

    The eleven principles the articles are built from:

    1. Immutable Foundation Core.
    2. Selective adaptive evolution.
    3. Open governance.
    4. Declarative policies.
    5. Evidence-driven decisions.
    6. Complete traceability.
    7. Configuration-controlled evolution.
    8. Guaranteed rollback.
    9. Vendor neutrality.
    10. Open standards.
    11. Deterministic governance.

    Each principle maps to at least one article of `AI-CONSTITUTION.md` and at
    least one requirement family (`SAO-<AREA>-*`) in the specification. The
    mapping table is maintained in `spec/SAIAUTOS-SPEC.md` §2.
    """))

add("constitution/RIGHTS-AND-RESPONSIBILITIES.md", T("""
    """ + SEED_MD + """

    # Rights and Responsibilities

    **Status:** Constitutional · **Spec:** v@SPEC@ (seed table)

    | Actor | Rights | Responsibilities |
    |---|---|---|
    | AI System | To propose its own updates; to have proposals evaluated by declared policy, not arbitrary veto | To emit complete, honest evidence; never to bypass the control plane |
    | Operator | To set policy within constitutional bounds; to roll back at any time | To keep rollback targets viable; to preserve the ledger |
    | Authority | To ratify, deny, or escalate | To be identifiable and accountable for every decision |
    | Auditor | To read the full ledger and reproduce every decision from evidence + policy | To report tampering and constitutional violations |
    | Implementer | To claim conformance once earned | To claim only the level actually passed, against a named spec version |
    """))

add("constitution/AMENDMENT-PROCESS.md", T("""
    """ + SEED_MD + """

    # Amendment Process

    **Status:** Constitutional · **Spec:** v@SPEC@

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
    """))


# ============================================================================
# 3. SPEC — the normative core
# ============================================================================

readme(
    "spec/README.md",
    "spec/ — The SAI-AUT-OS Specification",
    "Normative", "Specification",
    "The normative heart of the standard. RFC 2119 / RFC 8174 keywords apply "
    "throughout. Every normative statement carries a stable requirement ID of "
    "the form `SAO-<AREA>-<NNN>`; conformance tests reference IDs, never prose.",
    holds=[
        "`SAIAUTOS-SPEC.md` — the consolidated specification (entry point)",
        "`terminology.md` — the controlled vocabulary",
        "`architecture.md`, `update-lifecycle.md`, `policy-language.md`, "
        "`evidence-model.md`, `conformance-model.md` — normative modules",
        "`amendments/` — ratified amendments only",
        "`rfcs/` — candidate proposals, not yet ratified",
    ],
    not_here=[
        "Tutorials, marketing, comparisons (→ `docs/`)",
        "Implementation detail of any particular runtime (→ `impl/`, `sdk/`)",
    ],
    extra=T("""
        ## Reading order

        1. `terminology.md` → 2. `architecture.md` → 3. `update-lifecycle.md`
        → 4. `evidence-model.md` → 5. `policy-language.md`
        → 6. `conformance-model.md` → 7. `SAIAUTOS-SPEC.md` (consolidated).
        """),
)

add("spec/SAIAUTOS-SPEC.md", T("""
    """ + SEED_MD + """

    # SAI-AUT-OS Specification

    **Version:** @SPEC@ · **Status:** Draft (confers no conformance rights)

    ## 1. Scope

    This specification defines Cognitive Configuration Management (CCM): the
    objects, records, lifecycle, policy semantics, and conformance model for
    governing the evolution of adaptive AI systems. It is model-agnostic,
    infrastructure-agnostic, and deployment-agnostic.

    ## 2. Conformance

    The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD
    NOT, RECOMMENDED, MAY, and OPTIONAL are to be interpreted as described in
    RFC 2119 and RFC 8174 when, and only when, they appear in all capitals.

    Requirement identifier grammar: `SAO-<AREA>-<NNN>` where AREA ∈
    { COR core · CCI configuration items · EVD evidence · POL policy ·
      AUT authorization · DEP deployment · RBK rollback · LGR ledger ·
      CTX runtime context · LCY lifecycle · CON conformance }.
    IDs are stable forever; withdrawn requirements are marked withdrawn,
    never reused.

    ## 3. Terms — see `terminology.md` (normative).

    ## 4. Architecture — see `architecture.md` (normative).

    ## 5. Cognitive Configuration Items

    - **SAO-CCI-001.** Every candidate update MUST be represented as a CCI
      conforming to `schemas/cci.schema.json`.
    - **SAO-CCI-002.** An authorized CCI is immutable; any change MUST be a
      new CCI version referencing its predecessor.

    ## 6. Evidence — see `evidence-model.md`.

    - **SAO-EVD-001.** No CCI SHALL be authorized without at least one
      Evidence record bound to it. *(No evolution without evidence.)*

    ## 7. Policy — see `policy-language.md`.

    - **SAO-POL-001.** Authorization decisions MUST be produced by
      deterministic evaluation of declarative, versioned policy.

    ## 8. Update lifecycle — see `update-lifecycle.md`.

    ## 9. Authorization and authority

    - **SAO-AUT-001.** Every Authorization record MUST identify the
      accountable authority and its authority level (see
      `registry/authority-levels/`).

    ## 10. Deployment and rollback

    - **SAO-DEP-001.** Every deployment MUST emit a Deployment Record before
      the update is considered live.
    - **SAO-RBK-001.** Every CCI MUST declare a `rollback_target` prior to
      deployment; rollback MUST remain executable while the CCI is live.

    ## 11. Ledger and traceability

    - **SAO-LGR-001.** Every lifecycle record MUST be appended to a
      hash-chained, append-only ledger conforming to
      `schemas/ledger.schema.json`.

    ## 12. Foundation Core

    - **SAO-COR-001.** The control plane MUST NOT modify the Foundation Core.

    ## 13. Conformance levels — see `conformance-model.md` and
    `conformance/levels.md`.

    *(Seed skeleton. Each section is expanded and ratified via RFC.)*
    """))

add("spec/terminology.md", T("""
    """ + SEED_MD + """

    # Terminology

    **Status:** Normative · **Spec:** v@SPEC@

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
    """))

add("spec/architecture.md", T("""
    """ + SEED_MD + """

    # Architecture

    **Status:** Normative · **Spec:** v@SPEC@

    ```mermaid
    flowchart TB
        CP["SAI-AUT-OS · Evolution Control Plane"]
        FC["Foundation Core (immutable)"]
        AC["Adaptive Components<br/>memory · adapters · RAG · tools · prompts"]
        KS["Knowledge Sources"]
        RT["Runtime AI System"]
        CP -->|governs| FC
        CP -->|governs| AC
        CP -->|governs| KS
        FC --> RT
        AC --> RT
        KS --> RT
    ```

    The Foundation Core remains stable (SAO-COR-001). Adaptive components
    evolve. The control plane determines whether evolution is allowed, by
    running the update lifecycle over CCIs.

    Separation of concerns, by analogy with modern engineering: intelligence
    is separated from the governance of its evolution, as applications are
    separated from orchestration and code from version control.
    """))

add("spec/update-lifecycle.md", T("""
    """ + SEED_MD + """

    # Update Lifecycle

    **Status:** Normative · **Spec:** v@SPEC@

    ```mermaid
    flowchart LR
        O[Observe] --> C[Collect] --> N[Normalize] --> E[Evaluate]
        E --> V[Validate] --> A[Authorize] --> D[Deploy]
        D -. if required .-> R[Rollback]
    ```

    | Stage | Consumes | Produces | Schema |
    |---|---|---|---|
    | Observe | Runtime signals | Candidate signal | — |
    | Collect | Candidate signal | Raw evidence | — |
    | Normalize | Raw evidence | Evidence records | `evidence.schema.json` |
    | Evaluate | CCI + evidence | Evaluation result (deterministic) | part of CCI `validation` |
    | Validate | Evaluation result | Validation result (gates) | part of CCI `validation` |
    | Authorize | CCI + policy | Authorization record | `authorization.schema.json` |
    | Deploy | Authorized CCI | Deployment record | `deployment-record.schema.json` |
    | Rollback | Deployment record | Rollback record | `rollback.schema.json` |

    Every produced record is appended to the ledger (SAO-LGR-001).
    Every evolution becomes observable. Every evolution becomes governed.
    """))

add("spec/policy-language.md", T("""
    """ + SEED_MD + """

    # Policy Language

    **Status:** Normative · **Spec:** v@SPEC@ (seed)

    Policies are declarative, versioned documents conforming to
    `schemas/policy.schema.json`. Evaluation is deterministic (SAO-POL-001):
    identical CCI + identical evidence + identical policy ⇒ identical decision.

    A policy binds: (a) the update classes it applies to, (b) the evidence
    types and thresholds required, (c) the validation gates, and (d) the
    minimum authority level for authorization. Reference packs live in
    `policies/`.

    *(Seed. The full rule grammar is defined via RFC before 1.0.)*
    """))

add("spec/evidence-model.md", T("""
    """ + SEED_MD + """

    # Evidence Model

    **Status:** Normative · **Spec:** v@SPEC@ (seed)

    Evidence is the currency of evolution (SAO-EVD-001). Each Evidence record
    is typed (`registry/evidence-types/`), attributed to a source and a
    collector, and bound to its payload by hash (`payload_hash`), making it
    tamper-evident and replayable by auditors.

    Evidence never expires from the ledger; policies MAY discount evidence by
    age or provenance, but MUST do so declaratively.
    """))

add("spec/conformance-model.md", T("""
    """ + SEED_MD + """

    # Conformance Model

    **Status:** Normative · **Spec:** v@SPEC@ (seed)

    Conformance is claimed per **level** (L0/L1/L2 — `conformance/levels.md`),
    optionally narrowed by **profile** (`conformance/profiles/`), and always
    against a named specification version.

    A claim is valid only if the implementation passes the corresponding
    deterministic test vectors under `conformance/` using the official runner.
    Verdicts are calculated, never generated: no model output may decide a
    conformance result. Claim wording: `Conformant SAI-AUT-OS L<k> · spec <v>`.
    """))

readme(
    "spec/amendments/README.md",
    "spec/amendments/ — Ratified Amendments",
    "Normative", "Specification",
    "Only ratified amendments live here, one file per amendment, numbered and "
    "immutable once merged. Amendments supersede; they never rewrite "
    "(constitution/AMENDMENT-PROCESS.md, rules S1–S3).",
    holds=["`A-0001-<slug>.md`, `A-0002-<slug>.md`, …"],
    not_here=["Drafts or proposals (→ `spec/rfcs/`)"],
)

readme(
    "spec/rfcs/README.md",
    "spec/rfcs/ — Requests for Comments",
    "Pre-normative", "Specification",
    "Candidate updates to the standard. An RFC is itself a governed change "
    "proposal: it declares scope, affected requirement IDs, and evidence. "
    "Ratification per GOVERNANCE.md turns an RFC into an amendment.",
    holds=["`NNNN-<slug>.md` proposals, starting from 0001",
           "`0000-template.md` — the controlled template"],
)

add("spec/rfcs/0000-template.md", T("""
    """ + SEED_MD + """

    # RFC-0000 — Title

    | Field | Value |
    |---|---|
    | RFC | 0000 |
    | Title | *(concise, imperative)* |
    | Author(s) | *(name, affiliation)* |
    | Status | draft / review / ratified / withdrawn |
    | Constitutional | true / false |
    | Spec sections affected | *(e.g. §6, §10)* |
    | Requirement IDs added / changed / withdrawn | *(e.g. SAO-EVD-002)* |
    | Registries affected | *(e.g. update-types)* |
    | Supersedes | *(amendment/RFC refs or "—")* |

    ## Summary

    ## Motivation

    ## Normative changes (exact text)

    ## Evidence

    ## Compatibility and migration

    ## Decision record

    *(Filled at ratification: date, voting record, resulting amendment ID.)*
    """))


# ============================================================================
# 4. SCHEMAS — the machine-readable interoperability surface
# ============================================================================

readme(
    "schemas/README.md",
    "schemas/ — Machine-Readable Schemas",
    "Normative", "Interoperability",
    "JSON Schema (draft 2020-12) definitions of every record in the standard. "
    "This is the surface vendors implement: interoperability is judged against "
    "these schemas, not against prose. `$id` URNs carry the version "
    "(VERSIONING.md).",
    holds=[
        "`cci.schema.json` — the atom of CCM",
        "`evidence`, `policy`, `authorization`, `deployment-record`, "
        "`rollback`, `ledger`, `runtime-context` schemas",
    ],
    not_here=["Vendor extensions (use `x-` prefixed fields in your documents)"],
)

schema(
    "cci", "Cognitive Configuration Item",
    "The governed unit of AI evolution. Nothing evolves without context, "
    "traceability, and accountability.",
    required=["id", "class", "version", "provenance", "evidence", "rollback_target"],
    props={
        "id": {"type": "string", "description": "Globally unique CCI identifier."},
        "class": {"type": "string", "description": "Update class ID from registry/update-types/."},
        "version": {"type": "string", "description": "Semver of this CCI."},
        "provenance": {"type": "object", "description": "Who/what proposed this update, and from which signals."},
        "scope": {"type": "object", "description": "Adaptive components and systems this CCI touches."},
        "effectivity": {"type": "object", "description": "Where and when the CCI applies."},
        "evidence": {"type": "array", "items": {"type": "object"}, "description": "Evidence records (evidence.schema.json)."},
        "validation": {"type": "object", "description": "Evaluation and validation results."},
        "authorization": {"type": "object", "description": "Authorization record (authorization.schema.json)."},
        "deployment_history": {"type": "array", "items": {"type": "object"}, "description": "Deployment records, newest last."},
        "rollback_target": {"type": "string", "description": "Exact prior configuration to revert to (SAO-RBK-001)."},
        "supersedes": {"type": "string", "description": "Predecessor CCI id/version, if any (SAO-CCI-002)."},
    },
)

schema(
    "evidence", "Evidence Record",
    "A verifiable, hash-bound record supporting or opposing a CCI "
    "(SAO-EVD-001).",
    required=["id", "type", "source", "payload_hash"],
    props={
        "id": {"type": "string"},
        "type": {"type": "string", "description": "Evidence type ID from registry/evidence-types/."},
        "source": {"type": "string", "description": "System, dataset, or actor the evidence came from."},
        "collected_by": {"type": "string", "description": "Collector identity (human, pipeline, or model — models may collect, never ratify)."},
        "payload_hash": {"type": "string", "description": "SHA-256 of the raw payload; makes the record tamper-evident."},
        "summary": {"type": "string"},
    },
)

schema(
    "policy", "Policy",
    "A declarative, versioned governance document. Evaluation is "
    "deterministic (SAO-POL-001).",
    required=["id", "version", "applies_to", "rules", "authority_level_required"],
    props={
        "id": {"type": "string"},
        "version": {"type": "string"},
        "applies_to": {"type": "array", "items": {"type": "string"}, "description": "Update class IDs this policy governs."},
        "rules": {"type": "array", "items": {"type": "object"}, "description": "Ordered declarative rules (grammar per spec/policy-language.md)."},
        "authority_level_required": {"type": "string", "description": "Minimum authority level ID from registry/authority-levels/."},
    },
)

schema(
    "authorization", "Authorization Record",
    "The accountable decision on a CCI (SAO-AUT-001).",
    required=["cci_id", "policy_id", "decision", "authority"],
    props={
        "cci_id": {"type": "string"},
        "policy_id": {"type": "string"},
        "decision": {"type": "string", "enum": ["allow", "deny", "escalate"]},
        "authority": {"type": "object", "description": "Accountable authority identity and level."},
        "rationale": {"type": "string"},
        "evidence_refs": {"type": "array", "items": {"type": "string"}},
    },
)

schema(
    "deployment-record", "Deployment Record",
    "Emitted before a CCI is considered live (SAO-DEP-001).",
    required=["cci_id", "authorization_ref", "deployed_version", "status"],
    props={
        "cci_id": {"type": "string"},
        "authorization_ref": {"type": "string"},
        "deployed_version": {"type": "string"},
        "previous_version": {"type": "string"},
        "status": {"type": "string", "enum": ["pending", "live", "superseded", "rolled_back"]},
        "ledger_ref": {"type": "string"},
    },
)

schema(
    "rollback", "Rollback Record",
    "The exercised guarantee of reversibility (SAO-RBK-001).",
    required=["cci_id", "deployment_ref", "rollback_target", "status"],
    props={
        "cci_id": {"type": "string"},
        "deployment_ref": {"type": "string"},
        "rollback_target": {"type": "string"},
        "reason": {"type": "string"},
        "status": {"type": "string", "enum": ["requested", "executed", "verified", "failed"]},
    },
)

schema(
    "ledger", "Ledger Entry",
    "One link of the append-only, hash-chained trace (SAO-LGR-001).",
    required=["seq", "record_type", "record_hash", "prev_hash"],
    props={
        "seq": {"type": "integer", "minimum": 0},
        "record_type": {"type": "string", "enum": ["evidence", "authorization", "deployment", "rollback", "cci", "policy"]},
        "record_hash": {"type": "string", "description": "SHA-256 of the canonicalized record."},
        "prev_hash": {"type": "string", "description": "record_hash of the previous entry; genesis uses 64 zeros."},
        "payload_ref": {"type": "string"},
    },
)

schema(
    "runtime-context", "Runtime Context",
    "The declared shape of a governed system: what is immutable, what may "
    "evolve.",
    required=["system_id", "foundation_core", "adaptive_components"],
    props={
        "system_id": {"type": "string"},
        "foundation_core": {"type": "object", "description": "Identity + hash of the immutable core (SAO-COR-001)."},
        "adaptive_components": {"type": "array", "items": {"type": "object"}, "description": "Instances typed per registry/adaptive-components/."},
        "environment": {"type": "object"},
    },
)


# ============================================================================
# 5. POLICIES — reference declarative packs
# ============================================================================

readme(
    "policies/README.md",
    "policies/ — Reference Policy Packs",
    "Reference (non-normative content, normative format)", "Specification support",
    "Declarative policy packs conforming to `schemas/policy.schema.json`. The "
    "packs are starting points, not mandates: conformance requires *a* policy, "
    "not *these* policies.",
    holds=[
        "`baseline/` — the minimal pack a fresh L1 deployment can adopt",
        "`regulated/` — human-in-the-loop and external-attestation defaults",
        "`enterprise/` — organizational controls and separation of duties",
        "`examples/` — didactic single-purpose policies",
    ],
)
readme("policies/baseline/README.md", "policies/baseline/",
       "Reference", "Policy pack",
       "Minimal conformant defaults: every registered update class mapped to "
       "evidence requirements and an authority level. Designed so a new "
       "deployment can reach L1 without writing policy from scratch.")
readme("policies/regulated/README.md", "policies/regulated/",
       "Reference", "Policy pack",
       "Defaults for regulated domains: high-impact update classes require "
       "authority level `a2-human-ratified` or above, external attestation "
       "evidence, and mandatory verified rollback drills.")
readme("policies/enterprise/README.md", "policies/enterprise/",
       "Reference", "Policy pack",
       "Organizational defaults: separation of duties between proposer, "
       "validator, and authority; environment-scoped effectivity; change "
       "windows.")
readme("policies/examples/README.md", "policies/examples/",
       "Informative", "Policy pack",
       "Small, single-purpose policies used by `examples/` and by the "
       "conformance vectors. Optimized for readability, not production.")


# ============================================================================
# 6. CONFORMANCE — what earns the word "standard"
# ============================================================================

readme(
    "conformance/README.md",
    "conformance/ — Conformance Suite",
    "Normative", "Assurance",
    "The machinery that makes 'open standard' a testable claim. Conformance "
    "verdicts are calculated deterministically from vectors — never generated "
    "by a model.",
    holds=[
        "`levels.md` — the L0/L1/L2 ladder",
        "`profiles/` — domain profiles stacked on levels",
        "`test-vectors/` — deterministic input → expected-record fixtures",
        "`golden-datasets/` — frozen evidence corpora for reproducible runs",
        "`runner/` — the official harness any implementation can execute",
    ],
    not_here=["Anything nondeterministic; anything requiring network access"],
)

add("conformance/levels.md", T("""
    """ + SEED_MD + """

    # Conformance Levels

    **Status:** Normative · **Spec:** v@SPEC@

    | Level | Name | Requires | Claim it earns |
    |---|---|---|---|
    | L0 | Observed | observe + collect + normalize + hash-chained ledger (SAO-LGR-001) | "No silent evolution." |
    | L1 | Governed | L0 + evaluate + validate + authorize under declarative policy (SAO-EVD-001, SAO-POL-001, SAO-AUT-001) | "No evolution without evidence." |
    | L2 | Reversible | L1 + deployment records + declared and *verified* rollback (SAO-DEP-001, SAO-RBK-001) | "Every evolution is explainable, traceable and reversible." |

    Levels are cumulative. Profiles (see `profiles/`) MAY narrow but never
    relax a level. Claims name the level and the spec version:
    `Conformant SAI-AUT-OS L2 · spec 1.x`.
    """))

readme("conformance/profiles/README.md", "conformance/profiles/",
       "Normative", "Assurance",
       "Domain profiles: a profile = a level + additional constraints + a "
       "policy-pack floor. Seed roadmap: `regulated-industry` (L2 + "
       "policies/regulated), `open-research` (L1 + full public ledger).")
readme("conformance/test-vectors/README.md", "conformance/test-vectors/",
       "Normative", "Assurance",
       "Deterministic fixtures: one directory per vector containing input CCI, "
       "evidence, policy, and the byte-exact expected records per stage. If a "
       "vector cannot state its expected output exactly, it does not belong "
       "here.")
readme("conformance/golden-datasets/README.md", "conformance/golden-datasets/",
       "Normative", "Assurance",
       "Frozen, hash-pinned evidence corpora referenced by vectors. Never "
       "edited in place — superseded by new versions only, like everything "
       "else in this standard.")
readme("conformance/runner/README.md", "conformance/runner/",
       "Normative tool", "Assurance",
       "The official harness. Contract: point it at an implementation "
       "endpoint/CLI, it feeds vectors, compares emitted records byte-for-byte "
       "after canonicalization, and exits 0 only on a full pass for the "
       "claimed level. Verdicts are calculated, never generated.")


# ============================================================================
# 7. REGISTRY — official registries (IANA-style)
# ============================================================================

readme(
    "registry/README.md",
    "registry/ — Official Registries",
    "Normative", "Interoperability",
    "Every mature standard maintains official registries — as the Internet "
    "has MIME types and IANA registries, SAI-AUT-OS has these. Registries are "
    "diffable Markdown tables; entries are added only via ratified RFC and "
    "never deleted, only deprecated.",
    holds=[
        "`adaptive-components/` — the governable component types",
        "`update-types/` — the classes a CCI may declare",
        "`evidence-types/` — the admissible kinds of evidence",
        "`authority-levels/` — the accountability ladder",
    ],
    not_here=["This directory is unrelated to `impl/reference-python/registry/` "
              "(a runtime module)."],
)

readme("registry/adaptive-components/README.md", "registry/adaptive-components/",
       "Normative", "Interoperability",
       "Registered types of adaptive components — the parts of an AI system "
       "the control plane is allowed to evolve. See `REGISTRY.md`.")
registry_file("registry/adaptive-components/REGISTRY.md", "Adaptive Component Types", [
    ("memory", "Memory", "Persistent or working memory stores attached to the system"),
    ("lora-adapter", "LoRA / Adapter", "Parameter-efficient adapter weights layered on the Foundation Core"),
    ("rag-index", "RAG Index", "Retrieval corpora and their index structures"),
    ("tool-binding", "Tool Binding", "Tools/functions exposed to the system and their permissions"),
    ("prompt-profile", "Prompt Profile", "System prompts and behavioral configuration"),
])

readme("registry/update-types/README.md", "registry/update-types/",
       "Normative", "Interoperability",
       "Registered update classes. Every CCI declares exactly one class; "
       "policies key on it. See `REGISTRY.md`.")
registry_file("registry/update-types/REGISTRY.md", "Update Classes", [
    ("memory-update", "Memory Update", "Insertion, revision, or retirement of memory content"),
    ("lora-adapter-promotion", "Adapter Promotion", "Promoting trained adapter weights into service"),
    ("rag-corpus-update", "RAG Corpus Update", "Adding, superseding, or removing retrieval content"),
    ("tool-permission-change", "Tool Permission Change", "Widening or narrowing a tool binding"),
    ("prompt-policy-update", "Prompt Profile Update", "Changing system prompts or behavioral configuration"),
])

readme("registry/evidence-types/README.md", "registry/evidence-types/",
       "Normative", "Interoperability",
       "Registered kinds of admissible evidence. Policies state which types, "
       "how many, and at what thresholds. See `REGISTRY.md`.")
registry_file("registry/evidence-types/REGISTRY.md", "Evidence Types", [
    ("metric", "Metric", "A measured quantity with method and unit"),
    ("eval-run", "Evaluation Run", "Results of a defined evaluation suite, hash-pinned"),
    ("regression-suite", "Regression Suite", "Pass/fail record of a frozen regression set"),
    ("attestation", "Attestation", "Signed statement by an external system or authority"),
    ("human-review", "Human Review", "Recorded, attributable human judgment"),
])

readme("registry/authority-levels/README.md", "registry/authority-levels/",
       "Normative", "Interoperability",
       "The accountability ladder for authorization (SAO-AUT-001). Policies "
       "declare the minimum level per update class. See `REGISTRY.md`.")
registry_file("registry/authority-levels/REGISTRY.md", "Authority Levels", [
    ("a0-automatic", "Automatic", "Policy-only authorization; reversible, low-impact classes"),
    ("a1-gated", "Gated", "Deterministic gates must pass; no human in the loop"),
    ("a2-human-ratified", "Human-Ratified", "A named, accountable human ratifies"),
    ("a3-external-authority", "External Authority", "Domain/regulatory authority attestation required"),
])


# ============================================================================
# 8. SDK — developer experience layer
# ============================================================================

readme(
    "sdk/README.md",
    "sdk/ — SDKs",
    "Non-normative", "Adoption",
    "Developer-experience libraries for adopting the standard. SDKs exist for "
    "developers; the reference implementation exists to demonstrate "
    "conformance — the two are deliberately separate. Every SDK targets "
    "conformance L1 by default and MUST state the spec version it tracks.",
    holds=["`python/` (first), `rust/`, `go/`, `typescript/`"],
    not_here=["Normative behavior not present in `spec/` — SDKs never extend "
              "the standard silently"],
)
for lang, note in [
    ("python", "First SDK; tracks the reference implementation most closely."),
    ("rust", "Planned. Target: embedded and high-assurance control planes."),
    ("go", "Planned. Target: infrastructure and platform teams."),
    ("typescript", "Planned. Target: web runtimes and agent frameworks."),
]:
    readme(f"sdk/{lang}/README.md", f"sdk/{lang}/",
           "Non-normative", "Adoption",
           f"{note} Declares its spec target in its package metadata and "
           "passes the official conformance runner before any release.")


# ============================================================================
# 9. IMPL — reference implementation (proof, not product)
# ============================================================================

readme(
    "impl/README.md",
    "impl/ — Reference Implementation",
    "Non-normative", "Demonstration",
    "Exists to prove the standard is implementable and to pass "
    "`conformance/` — not to be the best implementation, and not to be the "
    "SDK. Where the reference implementation and the specification disagree, "
    "the specification wins and the implementation is defective.",
    holds=["`reference-python/` — one honest, readable implementation"],
)

readme(
    "impl/reference-python/README.md",
    "impl/reference-python/",
    "Non-normative", "Demonstration",
    "Readable Python implementation of the full lifecycle. Module layout is "
    "1:1 with the pipeline stages in `spec/update-lifecycle.md` so the "
    "crosswalk spec → schema → code needs no map.",
    holds=["One package directory per stage; `tests/` runs unit tests plus "
           "the conformance vectors"],
    not_here=["Performance tricks that obscure the spec crosswalk"],
)

_STAGES = {
    "observe":   "Watch adaptive components and runtime signals; surface candidate updates.",
    "collect":   "Gather raw evidence for a candidate update from declared sources.",
    "normalize": "Reduce raw evidence to Evidence records conforming to `schemas/evidence.schema.json`.",
    "evaluate":  "Score a CCI against policy-declared metrics. Deterministic by construction (SAO-POL-001).",
    "validate":  "Run validation gates; produce the CCI `validation` result.",
    "authorize": "Evaluate policy + authority level; emit the Authorization record (SAO-AUT-001).",
    "deploy":    "Apply an authorized CCI; emit the Deployment Record before it goes live (SAO-DEP-001).",
    "rollback":  "Restore the declared `rollback_target`; emit the Rollback record (SAO-RBK-001).",
    "registry":  "Runtime registry of adaptive-component types (loads `registry/` definitions).",
    "ledger":    "Append-only, SHA-256 hash-chained trace of every lifecycle record (SAO-LGR-001).",
    "tests":     "Unit tests plus execution of `conformance/test-vectors/` via the official runner.",
}
for stage, purpose in _STAGES.items():
    readme(f"impl/reference-python/{stage}/README.md",
           f"impl/reference-python/{stage}/",
           "Non-normative", "Demonstration", purpose)


# ============================================================================
# 10. ADAPTERS — ecosystem bindings
# ============================================================================

readme(
    "adapters/README.md",
    "adapters/ — Ecosystem Bindings",
    "Non-normative", "Integration",
    "Bindings that map external ecosystems' mutable state onto registered "
    "Adaptive Component types, so existing stacks can be governed without "
    "modification. An adapter never makes governance decisions — it only "
    "exposes state and applies authorized CCIs.",
)
_ADAPTERS = {
    "huggingface": "Model hub artifacts and adapter weights ⇢ `lora-adapter`.",
    "vllm":        "Serving-time adapter and prompt-profile switching ⇢ `lora-adapter`, `prompt-profile`.",
    "langchain":   "Chains, tools, and memory ⇢ `tool-binding`, `memory`.",
    "llamaindex":  "Indexes and retrievers ⇢ `rag-index`.",
    "mcp":         "Model Context Protocol servers and tool exposure ⇢ `tool-binding`.",
    "qdrant":      "Collections and payload schemas ⇢ `rag-index`.",
    "milvus":      "Collections and indexes ⇢ `rag-index`.",
    "pgvector":    "Postgres vector tables ⇢ `rag-index`.",
}
for name, purpose in _ADAPTERS.items():
    readme(f"adapters/{name}/README.md", f"adapters/{name}/",
           "Non-normative", "Integration", purpose)


# ============================================================================
# 11. TELEMETRY — evidence in, observability out
# ============================================================================

readme(
    "telemetry/README.md",
    "telemetry/ — Telemetry and Observability",
    "Non-normative", "Integration",
    "Evidence collection and export. SAI-AUT-OS aims to do for AI evolution "
    "what OpenTelemetry did for observability — so it bridges to OTel rather "
    "than reinventing it.",
    holds=[
        "`evidence-collector/` — turns runtime signals into Evidence records",
        "`exporters/` — ship ledger and records to external sinks",
        "`dashboards/` — reference views over the ledger",
        "`otel-bridge/` — Evidence/records ⇄ OTel spans, logs, and metrics",
    ],
)
for name, purpose in {
    "evidence-collector": "Collect raw signals and hand them to `normalize` — "
                          "collectors gather, they never judge.",
    "exporters": "Append-only export of ledger entries and records to files, "
                 "queues, or stores; exports never mutate the ledger.",
    "dashboards": "Reference dashboards: evolution timeline, evidence "
                  "coverage, authority-level distribution, rollback drills.",
    "otel-bridge": "Map lifecycle records to OpenTelemetry semantics so "
                   "existing observability stacks see AI evolution natively.",
}.items():
    readme(f"telemetry/{name}/README.md", f"telemetry/{name}/",
           "Non-normative", "Integration", purpose)


# ============================================================================
# 12. EXAMPLES · DOCS · TOOLS · CI
# ============================================================================

readme(
    "examples/README.md",
    "examples/ — Governed-Update Walkthroughs",
    "Informative", "Demonstration",
    "End-to-end, runnable walkthroughs — one per seed update class, each "
    "exercising the full lifecycle Observe → … → Deploy (and one exercising "
    "Rollback).",
    holds=[
        "`01-memory-update/` (planned)",
        "`02-lora-adapter-promotion/` (planned)",
        "`03-rag-corpus-update/` (planned)",
        "`04-tool-permission-change/` (planned, includes a rollback)",
    ],
)

readme(
    "docs/README.md",
    "docs/ — Non-Normative Documentation",
    "Informative", "Informative",
    "Explanatory material only: architecture guides, FAQ, comparisons "
    "(Kubernetes / OpenTelemetry analogies), adoption paths. Nothing here "
    "carries normative force; where docs and `spec/` diverge, `spec/` wins.",
    holds=["`manifesto.md` — the public manifesto (authored editorial content; "
           "existence controlled, text free)"],
    not_here=["Normative statements or requirement IDs defined here"],
)

add("docs/manifesto.md", T("""
    """ + SEED_MD + """

    # SAI-AUT-OS — Public Manifesto

    **Status:** Informative (authored) · **Spec:** v@SPEC@

    This file is editorial, not seed-governed: the scaffold guarantees its
    existence — so the root README link can never dangle — but does not govern
    its text. Replace this stub with the full public manifesto. Where the
    manifesto and `spec/` diverge, `spec/` wins.
    """))

readme(
    "tools/README.md",
    "tools/ — Deterministic Tooling",
    "Meta", "Meta",
    "Generators and validators. `scaffold.py` is the single source of truth "
    "for repository structure: change the generator, not the tree. CI runs "
    "`python tools/scaffold.py --check` as a structural conformance gate — "
    "the repository is the first configuration item governed by its own "
    "standard.",
    holds=[
        "`scaffold.py` — deterministic structure generator + `--check` gate",
        "`validate_cci.py` (planned) — validate documents against `schemas/`",
    ],
)

add(".github/workflows/structure-check.yml", T("""
    """ + SEED_HASH + """
    # Structural conformance gate: the repository tree must match the
    # single source of truth in tools/scaffold.py.
    name: structure-check
    on:
      push:
      pull_request:
    jobs:
      structure:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with:
              python-version: "3.12"
          - name: Verify controlled structure
            run: python tools/scaffold.py --check
    """))


# ----------------------------------------------------------------------------
# Engine
# ----------------------------------------------------------------------------

def emit(root: Path, force: bool) -> tuple[int, int, int]:
    created = skipped = overwritten = 0
    for rel, content in FILES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        exists = path.exists()
        if exists and not force:
            skipped += 1
            continue
        with path.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        overwritten += int(exists)
        created += int(not exists)
    return created, skipped, overwritten


def check(root: Path) -> int:
    missing: list[str] = []
    seed_state = authored = 0
    for rel, content in FILES.items():
        path = root / rel
        if not path.exists():
            missing.append(rel)
        elif path.read_bytes() == content.encode("utf-8"):
            seed_state += 1
        else:
            authored += 1
    if missing:
        print(f"[FAIL] structure: {len(missing)} controlled path(s) missing:")
        for rel in missing:
            print(f"       - {rel}")
        print("       Update tools/scaffold.py (the SSOT) or restore the paths.")
        return 1
    total = len(FILES)
    print(f"[OK]   structure: all {total} controlled paths present.")
    print(f"[info] authoring progress: {authored}/{total} authored, "
          f"{seed_state}/{total} still at seed state.")
    return 0


def manifest_json() -> str:
    return json.dumps(
        {
            "standard": STANDARD,
            "spec_version": SPEC_VERSION,
            "scaffold_version": SCAFFOLD_VERSION,
            "file_count": len(FILES),
            "files": {
                rel: {
                    "sha256": hashlib.sha256(c.encode("utf-8")).hexdigest(),
                    "bytes": len(c.encode("utf-8")),
                }
                for rel, c in FILES.items()
            },
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scaffold.py",
        description=f"{STANDARD} deterministic repository scaffold "
                    f"(scaffold v{SCAFFOLD_VERSION}, spec v{SPEC_VERSION}).",
    )
    parser.add_argument("--root", default=".", help="repository root (default: CWD)")
    parser.add_argument("--force", action="store_true",
                        help="overwrite existing files with seed content")
    parser.add_argument("--check", action="store_true",
                        help="verify structure instead of writing (CI gate)")
    parser.add_argument("--manifest", metavar="PATH",
                        help="write SHA-256 manifest of the seed set to PATH")
    parser.add_argument("--list", action="store_true",
                        help="print controlled paths and exit")
    args = parser.parse_args(argv)

    if args.list:
        for rel in FILES:
            print(rel)
        return 0

    def write_manifest() -> None:
        out = Path(args.manifest)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(manifest_json())
        print(f"[OK]   manifest: {len(FILES)} seed files -> {out}")

    root = Path(args.root)
    if args.check:
        rc = check(root)
        if args.manifest:
            write_manifest()
        return rc

    created, skipped, overwritten = emit(root, args.force)
    if args.manifest:
        write_manifest()
    print(f"[OK]   {STANDARD} scaffold v{SCAFFOLD_VERSION} · spec v{SPEC_VERSION}")
    print(f"       root: {root.resolve()}")
    print(f"       created={created} skipped={skipped} overwritten={overwritten} "
          f"(controlled files: {len(FILES)})")
    if skipped and not args.force:
        print("       existing files were preserved (use --force to re-seed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())