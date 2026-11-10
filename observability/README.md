# Observability baseline

## Why Phoenix
Use Arize Phoenix as the single local observability and evaluation workspace. It supports OpenTelemetry-based tracing, datasets, experiments and evaluators. Separate projects per agent provide focused views; trace context links them into an end-to-end run.

References:
- https://arize.com/docs/phoenix/
- https://github.com/Arize-ai/phoenix

## Local start
```bash
docker compose -f observability/docker-compose.yml up -d
```
Then open `http://localhost:6006`.

Pin a tested Phoenix release instead of `latest` before reproducible team/production use. Confirm the current image's port and environment variables from its release documentation.

## Required instrumentation contract
At minimum, create spans for:
- pipeline run
- agent invocation
- each retrieval/tool call
- each model call
- each evaluator
- human approval decision
- render and publish adapter operations (publishing remains disabled until explicitly approved)

Required span attributes:
`agent.name`, `agent.version`, `prompt.version`, `model.provider`, `model.name`, `run.id`, `story.id`, `pipeline.stage`, `dataset.name`, `dataset.version`, `experiment.id`, `result.status`, `retry.count`.

Record token counts/cost only where available from the provider. Do not fabricate estimates as actual cost. Use structured events for claim IDs, source IDs and state transitions; avoid logging full article text or secrets.

## OpenTelemetry implementation notes
- Use the Python OpenTelemetry SDK and OTLP exporter.
- Set Phoenix OTLP endpoint from environment variables; do not hard-code credentials.
- Propagate W3C trace context between orchestrator and agent calls.
- Use one trace per story pipeline run; each agent invocation is a child span.
- Keep stable business identifiers (`run.id`, `story.id`) as attributes; do not use them as trace IDs.
- If Phoenix is down, use a bounded local queue/file exporter and mark the run's observability status as degraded.

## Evaluation integration
Phoenix is the system of record for experiment traces and comparison. Keep evaluator definitions and golden dataset source files version-controlled in this repository. Add an adapter layer so evaluator execution is not tightly coupled to a specific Phoenix SDK version. Export a machine-readable eval summary to CI and fail the release gate on critical regressions.

## Per-agent project names
- `finance-media-news-scout`
- `finance-media-novelty`
- `finance-media-research`
- `finance-media-fact-check`
- `finance-media-scriptwriter`
- `finance-media-producer`
- `finance-media-growth`
- `finance-media-orchestrator`

## Security
Phoenix is local by default in this starter. Do not expose it to the public internet without authentication, TLS, access controls and a retention policy. Redact credentials, personal data and copyrighted source bodies before tracing.
