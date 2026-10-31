# The data engineering field guide

A dictionary of real-world problems you will meet in production, and how to handle each one,
with and without Claude. Look up the symptom, not the solution.

Every entry follows the same shape:

> **Symptom** what you see · **Why** the usual root causes · **Diagnose** the first queries/commands to run ·
> **Fix** the standard pattern · **With Claude** the prompt or feature that speeds it up · **Prevent** the guardrail
> so it never happens again · **Practise** where in this lab

## Index (A–Z)

| Problem | Chapter |
|---|---|
| Access requests and least privilege | [Governance](04-governance.md#access-control-and-least-privilege) |
| Agent gives a confident wrong number | [AI in production](05-ai-agents.md#confident-wrong-answers) |
| Agent loops / never finishes | [AI in production](05-ai-agents.md#agent-loops-or-stalls) |
| Backfill / reprocessing history | [Modelling](02-modelling.md#backfills-and-reprocessing) |
| CDC: deletes and updates from source | [Ingestion](01-ingestion.md#cdc-updates-and-hard-deletes) |
| Context window overflow / forgetful sessions | [AI in production](05-ai-agents.md#context-overflow) |
| Cost blow-up (warehouse) | [Operations](03-operations.md#warehouse-cost-blow-up) |
| Cost blow-up (LLM tokens) | [AI in production](05-ai-agents.md#token-cost-blow-up) |
| Currency, units and tax confusion | [Modelling](02-modelling.md#units-currency-and-tax) |
| Data contract violations by producers | [Governance](04-governance.md#data-contracts) |
| Double counting after a join (fan-out) | [Modelling](02-modelling.md#fan-out-joins-and-double-counting) |
| Duplicates / re-sent data | [Ingestion](01-ingestion.md#duplicates-and-re-sent-data) |
| Encoding, delimiters, malformed files | [Ingestion](01-ingestion.md#malformed-files) |
| Flaky tests and alert fatigue | [Operations](03-operations.md#flaky-tests-and-alert-fatigue) |
| Freshness / SLA breach | [Operations](03-operations.md#freshness-and-sla-breaches) |
| GDPR / right to be forgotten | [Governance](04-governance.md#deletion-requests-gdpr-dpdp) |
| Idempotency: re-runs double the data | [Modelling](02-modelling.md#idempotency) |
| Incident at 3 am | [Operations](03-operations.md#the-3-am-pipeline-failure) |
| Late-arriving data | [Ingestion](01-ingestion.md#late-arriving-data) |
| LLM output changes after a model upgrade | [AI in production](05-ai-agents.md#behaviour-changes-after-model-upgrades) |
| Metric definition disputes ("which revenue?") | [Modelling](02-modelling.md#metric-definition-disputes) |
| Missing partition / file never arrived | [Ingestion](01-ingestion.md#missing-partitions) |
| Nulls breaking aggregates | [Modelling](02-modelling.md#nulls-in-aggregates-and-joins) |
| Orphan keys / referential integrity | [Ingestion](01-ingestion.md#orphan-keys) |
| PII leaking into logs, prompts or notebooks | [Governance](04-governance.md#pii-in-logs-prompts-and-notebooks) |
| Prompt injection through data | [Governance](04-governance.md#prompt-injection-through-data) |
| Rate limits and API errors (429 / 5xx) | [AI in production](05-ai-agents.md#rate-limits-and-api-errors) |
| Schema drift | [Ingestion](01-ingestion.md#schema-drift) |
| SCD: history of changing dimensions | [Modelling](02-modelling.md#slowly-changing-dimensions) |
| Secrets in code or config | [Governance](04-governance.md#secrets) |
| Skew, OOM and slow queries | [Operations](03-operations.md#slow-queries-skew-and-oom) |
| Small files | [Ingestion](01-ingestion.md#small-files) |
| Timezones and DST | [Ingestion](01-ingestion.md#timezones-and-dst) |
| Unauditable agent actions | [Governance](04-governance.md#auditing-agent-actions) |
| Upstream API: pagination, throttling | [Ingestion](01-ingestion.md#upstream-apis-pagination-and-throttling) |
| Volume anomaly (sudden drop or spike) | [Operations](03-operations.md#volume-anomalies) |

## How to use it

- **During an incident:** find the symptom, run the *Diagnose* block, paste the output into Claude with the *With Claude* prompt.
- **In design reviews:** walk the *Prevent* lines as a checklist for any new pipeline.
- **As practice:** each entry lists a lab day or a way to reproduce it on the lab data.
- **Grow it:** after every real incident, add an entry. Ask Claude: `Add a field-guide entry for today's incident from de-lab/reports/session_notes.md in the same format.`
