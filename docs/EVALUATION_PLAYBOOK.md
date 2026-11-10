# Evaluation & Continuous Quality Playbook

## 1. Evaluation layers

Every agent uses the same lifecycle, with agent-specific metrics and thresholds.

| Layer | Purpose | Examples |
|---|---|---|
| Contract tests | Ensure predictable interfaces | Pydantic validation, required fields, allowed enums |
| Deterministic evals | Catch objective failures | Arithmetic, claim IDs, URL/date parsing, state gates |
| Golden-set evals | Compare quality against curated examples | Retrieval relevance, factual entailment, script quality |
| Holdout evals | Estimate generalization | Untouched examples from distinct events/time periods |
| Production monitoring | Detect drift and operational issues | Latency, failures, overrides, quality labels |
| Human review | Adjudicate ambiguous/critical cases | Factuality, originality, visual QA |

Use code-based evaluators wherever possible. LLM-as-judge is a secondary signal for subjective dimensions and must be calibrated against human labels.

## 2. Golden dataset creation workflow

### A. Collect candidate examples
Sources:
- Historical story runs and source snapshots/metadata.
- Public official datasets and press releases.
- Human editor corrections, rejects and revision requests.
- Synthetic edge cases for malformed inputs, conflicting sources and adversarial prompt injection.

Do not include private credentials, personal data, or copyrighted full-text articles. Prefer short excerpts, metadata, stable URLs and claim-level evidence locators.

### B. Define labels before sampling
For each agent, define:
- input schema and output schema
- target behavior
- label taxonomy
- objective checks
- subjective rubric and anchor examples
- critical failure definitions
- acceptance thresholds

### C. Annotate and adjudicate
- Two independent labels for critical fact-checking examples where feasible.
- Record labeler, date, rationale and confidence.
- Resolve disagreements with an editor; store adjudicated label and disagreement history.
- Do not treat an LLM judge output as ground truth.

### D. Split by event/time, not random rows alone
- `train/dev`: prompt iteration and evaluator calibration.
- `holdout`: locked, never used for prompt tuning.
- `prod_regression`: curated production failures for regression tests.
- Keep near-duplicate stories and the same event in one split to avoid leakage.

### E. Version and govern
Dataset version is immutable after release. Add examples by creating a new version with a changelog. Store source references and rights/retention notes. Each example has stable `example_id`, `agent_name`, `dataset_version`, `split`, `input`, `reference`, `labels`, `severity`, `source_refs`, `adjudication`.

## 3. Standard eval run

1. Pin code commit, agent version, prompt version, model/provider and parameters.
2. Load a fixed dataset version.
3. Run each example at least once; use repeated runs for nondeterministic outputs.
4. Run deterministic validators.
5. Run calibrated rubric evaluators.
6. Log per-example scores, explanations, traces and aggregate metrics to Phoenix.
7. Compare against last approved baseline and locked holdout.
8. Review critical failures and representative disagreements.
9. Approve or reject the candidate version; record reviewer and decision.
10. Keep the exact experiment configuration for reproducibility.

## 4. Promotion gates

Universal gates:
- 100% schema/contract pass.
- 100% deterministic policy invariants pass.
- Zero critical safety/factuality false accepts on golden and holdout.
- No unexplained regression in any critical metric.
- All evals executed and visible in Phoenix (or documented offline export if Phoenix unavailable).
- Human approval of prompt/model release.

Suggested initial quality targets (calibrate after baseline data exists):
- News Scout: duplicate precision ≥0.95; metadata validity =100%.
- Novelty Analyst: weighted score arithmetic =100%; false-advance rate ≤0.05.
- Researcher: material claim evidence coverage ≥0.98; source reference validity =100%.
- Fact Checker: critical false-accept rate =0; claim status coverage =100%.
- Scriptwriter: approved-claim coverage =100%; unsupported-claim rate =0; duration compliance ≥0.90.
- Producer: licensed-asset compliance =100%; render success ≥0.98.
- Growth Analyst: metric arithmetic =100%; fabricated metrics =0.

Targets are initial guardrails, not claims of achieved performance.

## 5. Production monitoring

Monitor per agent and per prompt/model version:
- request count, success/error rate, retry rate
- p50/p95 latency
- input/output tokens and estimated cost when available
- schema failure rate
- evaluator scores and failure categories
- human override/rejection rate
- drift by topic/source/platform and time window

Critical alerts:
- Any unverified material claim reaches script/approval queue.
- Any publishing attempt without valid human approval.
- Any unlicensed asset is included.
- Sudden schema or source-fetch failure spike.
- Critical eval metric falls below threshold.
- Telemetry/eval pipeline outage.

## 6. Production-to-golden feedback loop

1. Sample traces across all outcomes, not only successful outputs.
2. Human annotator labels failure category and severity.
3. Adjudicate high-severity or ambiguous examples.
4. Redact secrets and remove copyrighted body text/private data.
5. Add as candidate example; do not silently modify released golden sets.
6. Version dataset; rerun all affected agent evals.
7. Track whether the fix improves the regression set without degrading holdout.

## 7. Evaluator design per agent

| Agent | Deterministic evaluators | Rubric evaluators |
|---|---|---|
| News Scout | schema, URL/date, duplicate pair labels, source metadata | relevance, summary fidelity |
| Novelty | weighted score, threshold, decision schema | novelty, audience payoff, angle distinctiveness |
| Researcher | source refs, metadata, numeric units, claim coverage | source quality, contradiction handling |
| Fact Checker | statuses, source IDs, caveat preservation, zero unsupported approval | entailment, calibration, skepticism |
| Scriptwriter | claim ID mapping, duration, prohibited advice terms | clarity, originality, hook accuracy, caveat retention |
| Producer | duration, aspect ratio, subtitle timing, license manifest, media probe | readability, pacing, brand consistency |
| Growth Analyst | arithmetic, metric windows, denominator checks | diagnostic usefulness, causal restraint |

## 8. Phoenix operating model

Use one Phoenix instance, but one project per agent and one for orchestration. This keeps per-agent dashboards and experiments independent while preserving distributed trace context across the whole run.

For each agent:
- Send OpenTelemetry spans to Phoenix.
- Create a Phoenix dataset for its golden examples.
- Run experiments with code-based and rubric evaluators.
- Attach human annotations to production traces.
- Compare prompt/model variants side by side.
- Use trace metadata to filter by prompt, model, topic, source and release.

Do not assume a single Phoenix project automatically creates the dataset or evaluators; implement explicit dataset/experiment registration and CI commands using the Phoenix SDK version pinned in the project.

## 9. Minimal CI/release commands (target interface)

```bash
pytest
python -m app.evals.run --agent news_scout --dataset golden --split dev
python -m app.evals.run --agent news_scout --dataset golden --split holdout
python -m app.evals.compare --agent news_scout --baseline approved
python -m app.release.check --agent news_scout
```

The commands above define the desired interface; implement them in later slices and test each command.
