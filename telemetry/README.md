<!-- sai-aut-os:seed scaffold=0.2.0 spec=1.0.0-draft.1 -->

# telemetry/ — Telemetry and Observability

**Status:** Non-normative · **Layer:** Integration · **Spec:** v1.0.0-draft.1

Evidence collection and export. SAI-AUT-OS aims to do for AI evolution what OpenTelemetry did for observability — so it bridges to OTel rather than reinventing it.

## What belongs here

- `evidence-collector/` — turns runtime signals into Evidence records
- `exporters/` — ship ledger and records to external sinks
- `dashboards/` — reference views over the ledger
- `otel-bridge/` — Evidence/records ⇄ OTel spans, logs, and metrics
