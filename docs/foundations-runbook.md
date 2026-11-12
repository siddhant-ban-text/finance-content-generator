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
Editorial authentication uses the separate browser service described below; local
Phoenix development authentication is disabled and must not be exposed publicly.

No real model, agent golden evaluation, or authenticated editorial approval is
provided by tracing. Offline span evidence validates infrastructure behavior only.

## Local browser reviewer login (Task 11)

This slice establishes browser identity only. No HTTP approval or publishing
routes are installed. `ReleaseService` remains default-deny unless its caller
explicitly supplies `SessionService.verify_principal`; Task 12 will wire actual
human decision routes. The verifier uses the same SQLite connection and only
reads session state, including when called inside a business transaction.

Register your own GitHub **OAuth App** in GitHub developer settings. Use homepage
`http://127.0.0.1:8765` and the sole callback
`http://127.0.0.1:8765/auth/github/callback`; disable wildcard redirects and do not
add other callback URLs. Request no repository, email, refresh or offline scopes.
Obtain the intended human account's stable numeric GitHub ID from GitHub's public
user API or your own operator CLI lookup. A display login is never an allowlist
key. Bots and organizations are denied. There is no first-login enrollment.

In your ignored `.env`, set `FINANCE_GITHUB_CLIENT_ID`,
`FINANCE_GITHUB_CLIENT_SECRET`, and `FINANCE_GITHUB_ALLOWED_IDS` (comma-separated
positive integers), and explicitly set
`FINANCE_AUTH_LOOPBACK_DEVELOPMENT=true`. Never paste credentials into chat,
command history, logs or checked-in files. Load the file explicitly with
`uv run --env-file .env`; application code never reads `.env` automatically.
Missing any credential or the allowlist produces `authentication_setup_required`
at `/auth/status` and disables login. There is no gh, PAT, anonymous or test-auth
fallback.

Embedding example (save as an ignored local script; do not run a generic Uvicorn
CLI with access logging enabled):

```python
from app.config import Settings
from app.storage.db import open_database, migrate
from app.auth.github import GitHubOAuth
from app.auth.sessions import SessionService
from app.web import Services, serve

settings = Settings.from_env()
settings.data_dir.mkdir(parents=True, exist_ok=True)
conn = open_database(settings.data_dir / "pipeline.sqlite")
migrate(conn)
try:
    serve(settings, Services(oauth=GitHubOAuth(settings),
                            sessions=SessionService(conn, settings)))
finally:
    conn.close()
```

Open `/auth/login` in the browser. The five-minute, one-use state is bound to an
HttpOnly browser cookie and S256 PKCE. Pending handshakes are memory-only and
invalidate on restart. Only the synchronous GitHub exchange runs in a worker
thread; SQLite verification, revocation and session creation stay on the serving
event loop thread, so slow GitHub responses do not block logout/session checks. The callback discards GitHub tokens and rotates the local
session, then redirects to the setup status page. It does not approve anything.
`GET /auth/session` checks current identity and refreshes the CSRF cookie;
`POST /auth/logout` requires the session cookie, exact
`Origin: http://127.0.0.1:8765`, and `X-CSRF-Token` matching the `finance_csrf`
cookie. CSRF tokens are HMAC-bound to the opaque HttpOnly session, never persisted.
Restart changes the CSRF key; fetch `/auth/session` before a subsequent mutation.

Sessions expire after 1,800 seconds idle or 28,800 seconds absolute. DB rows store
only session-cookie SHA256, random server reference, numeric ID, timestamps and
revocation. Current allowlist membership is rechecked on every request and verifier
call; removal immediately denies the existing session. Display login, email,
GitHub response bodies, OAuth credentials, state, PKCE and CSRF are not persisted.

`serve` binds only `127.0.0.1:8765`, uses one process, disables proxy-header trust
and all Uvicorn access logging. The app rejects unexpected Host, scheme and all
forwarding headers, has no CORS middleware, disables automatic slash redirects (noncanonical callback
paths return 404), suppresses callback query data in its ASGI scope, and emits no authentication traces or application logs. Do not add
request/query/body logging, automatic HTTP/ASGI instrumentation or proxy wrappers
around this app. Cookies are HttpOnly and SameSite=Lax (the CSRF cookie is readable
by the same-origin UI). Non-Secure cookies are supported only by the explicit
HTTP loopback development mode; alternate origins/callbacks fail setup. No remote
hosting or HTTPS deployment is implemented in this slice.

The trust boundary is a local trusted machine. This does not protect against a
malicious OS administrator, access to the browser profile, modified local Python
code or direct writable SQLite access. Keep database files and `.env` private;
share only sanitized evidence exports. Never run this service on a shared or
untrusted workstation.

Mocked CI tests exercise OAuth/session security and inspect raw SQLite snapshots,
SQL exports, debug application/HTTP transport logs and an in-memory OTel exporter
for credential/private-identity sentinels. Real GitHub browser login requires
your OAuth app and has not been exercised by this implementation task.
