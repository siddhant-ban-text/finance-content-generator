# Finance Media Automation — Codex + Superpowers Blueprint

An evaluation-first blueprint for building a mostly autonomous finance/economics news-to-short-video workflow. It is designed to be implemented in small, reviewable slices with Codex and the Superpowers GitHub skills framework.

## Product constraints

- Niche: finance and economics; explain what happened, why it matters, and what could happen next.
- Goal: side income, not a venture-scale platform.
- Publishing: **human approval is mandatory**. No agent may publish or bypass the approval gate.
- Budget target: under USD/CAD 50 per month (confirm currency and hosting choices before deployment).
- Prefer local/open-source components; paid model APIs are optional adapters, never a hard dependency.
- Factual verification must use source evidence, not model memory.

## What is in this blueprint

- `docs/ARCHITECTURE.md` — system boundaries, contracts, state machine, data flow and deployment.
- `prompts/agents/` — one independent system prompt per content agent.
- `prompts/ORCHESTRATOR_PROMPT.md` — end-to-end system orchestration contract.
- `docs/EVALUATION_PLAYBOOK.md` — shared golden-dataset, eval, regression and monitoring lifecycle.
- `evals/golden/` — starter examples and dataset schema.
- `observability/` — Arize Phoenix + OpenTelemetry design and local compose starter.
- `superpowers/IMPLEMENTATION_PLAN.md` — staged implementation tasks suitable for Superpowers.
- `docs/superpowers/specs/2026-11-09-foundations-design.md` — approved foundation design and architecture decisions.
- `docs/superpowers/plans/2026-11-09-foundations.md` — detailed test-first foundation tasks and acceptance gates.
- `AGENTS.md` — durable Codex project rules.

## Recommended implementation order

1. Read `AGENTS.md` and `docs/ARCHITECTURE.md`.
2. In Codex, ask Superpowers to brainstorm and critique the design before implementation.
3. Ask it to convert `superpowers/IMPLEMENTATION_PLAN.md` into a task plan.
4. Implement one vertical slice at a time: contracts and durable state → tracing → evaluation framework → authenticated review → first agent.
5. Do not build every agent in parallel before shared schemas, tracing and eval interfaces exist.

## Local observability

Arize Phoenix is the recommended starting observability layer. It is open source and supports tracing, datasets, experiments and evaluators. Use one Phoenix instance with a distinct `project_name` per agent plus a shared orchestration project. Each span carries `agent.name`, `agent.version`, `prompt.version`, `model.name`, `dataset.version`, and `run.id`.

Start it with:

```bash
docker compose -f observability/docker-compose.yml up -d
```

Open the Phoenix UI at `http://localhost:6006` (verify the port against the Phoenix image/version you pin).

The compose file is a starter, not a production deployment. Pin a tested Phoenix image version before relying on it.

## Important caveat

This is a design and prompt pack, not a claim that the pipeline is already implemented or connected to your accounts. Codex should implement and test the components in stages. Platform publishing APIs, model availability, licensing, and platform monetization requirements must be checked against current official documentation before enabling them.
