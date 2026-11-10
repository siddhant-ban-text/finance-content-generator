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
