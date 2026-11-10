# Foundation development runbook

Use the isolated codex/finance-foundations worktree. Original checkout remains
unchanged. Setup: `uv sync --locked`; tests: `uv run pytest`.
Regenerate checked-in schemas: `uv run python -m app.contracts.export --out schemas/v1`.

Configuration uses FINANCE_ environment variables; secrets stay in ignored local
.env files and must never be printed, traced or committed. To load one explicitly,
use `uv run --env-file .env <command>`. Publishing stays disabled in these
foundations. API providers are unset and require explicit opt-in even to configure.
Fake stages are allowed only in demo/test environments.

Task 1 implements contracts/settings/prompt integrity only. No agent, provider,
state persistence, telemetry service, evaluation framework or approval UI exists
at this task boundary. Task 5 supplies tracing/fallback, Task 7 begins datasets,
and later tasks supply authenticated human review. Do not infer achieved agent
quality or publication readiness from contract tests.

## Durable tracing and offline evidence

`Telemetry(Path("data/telemetry.sqlite"))` uses a dedicated SQLite outbox, separate
from the business connection. Create the parent directory before construction.
Use `story_context(run_id, story_id)` and `span(name, project, attributes)` with
typed business UUIDs. The SDK generates trace/span IDs. Manual instrumentation
retains only the documented metadata vocabulary; names, resources, events and
exception paths are sanitized before buffering or network export.

Queue limits are 10,000 pending records or 50 MiB of serialized payload, whichever
is reached first. Lower per-instance limits are supported. Overflow preserves the
existing queue and records loss/degraded run IDs. Export uses an explicit flush or
shutdown, outside state transactions, with a maximum five-second wait. Unavailable
disk and permanently blocked exporters surface typed health errors. Disk-unavailable
health cannot itself always be persisted; in-memory fallback is exposed to callers.
When a flush exhausts its budget, its report leaves `pending_count` unknown and
records timeout degradation in memory without further database work. Query health
separately for the current count. This timeout signal may be lost on process exit;
pending span records remain durable. A zero-budget flush performs no database work.

`telemetry.export_offline(Path("data/trace-export"))` writes sanitized `spans.jsonl`
and a checksummed `manifest.json` without removing pending spans. Verify the hash
before loading lines as versioned `SpanRecord` objects; enqueue them into another
outbox to replay. Replay preserves the original SDK identifiers and is at-least-once:
an acknowledged batch retried after an acknowledgement/write failure may duplicate
delivery. Collector/UI deduplication is not assumed; Task 9 verifies actual behavior.

Local startup (optional; never part of default tests):

```sh
docker compose -f observability/docker-compose.yml up -d
uv run python -m app.observability.health
```

The health command probes `/healthz` and returns JSON plus exit 0/1. Liveness alone
does not prove span ingestion. `Telemetry.health()` reports local queue health and
degradation separately. `FINANCE_PHOENIX_ENDPOINT` may select another literal
loopback IP/port, with exact `/v1/traces` path; credentials, query strings, fragments
and remote hosts are rejected. Ambient `OTEL_*` headers and proxy variables cannot
override this application boundary. Compose exposes only loopback HTTP port 6006,
disables Phoenix UI analytics/external resources, and preserves its named volume.
Editorial authentication is a separate future GitHub review service; local Phoenix
development authentication is disabled and must not be exposed publicly.

No real model, agent golden evaluation, or authenticated editorial approval is
provided by tracing. Offline span evidence validates infrastructure behavior only.
