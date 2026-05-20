# Agent Company Roadmap (Lean, Ambitious, Controlled)

## Purpose

Run Matchday IQ like an agent company: high automation, clear ownership, and minimal founder interrupts.

This roadmap is intentionally scope-controlled. New ideas enter only through the intake and decision gates below.

---

## Bookmark-first UI links

Replace `ramialfahham/football-data-pipeline` only if the repo moves.

### Product and data outputs

- Live app landing: `https://ramialfahham.github.io/football-data-pipeline/`

### Control plane

- Repository home: `https://github.com/ramialfahham/football-data-pipeline`
- Actions overview: `https://github.com/ramialfahham/football-data-pipeline/actions`
- Failed runs filter: `https://github.com/ramialfahham/football-data-pipeline/actions?query=status%3Afailure`
- Scheduled ingest + dbt workflow: `https://github.com/ramialfahham/football-data-pipeline/actions/workflows/dbt-scheduled.yml`
- Pages deploy workflow: `https://github.com/ramialfahham/football-data-pipeline/actions/workflows/pages-match-preview.yml`
- CI validate workflow: `https://github.com/ramialfahham/football-data-pipeline/actions/workflows/ci-validate.yml`
- Data build workflow: `https://github.com/ramialfahham/football-data-pipeline/actions/workflows/ci-data-build.yml`
- UI checks workflow: `https://github.com/ramialfahham/football-data-pipeline/actions/workflows/ci-ui.yml`

### Decision and review inboxes

- Open PRs: `https://github.com/ramialfahham/football-data-pipeline/pulls`
- Open issues: `https://github.com/ramialfahham/football-data-pipeline/issues`
- Decision-needed issues (create label): `https://github.com/ramialfahham/football-data-pipeline/issues?q=is%3Aissue%20is%3Aopen%20label%3Adecision-needed`

---

## Operating model (who does what)

- `CPO (you)`: approve only gated decisions.
- `Football Analytics Expert` + `BI Analyst`: metric truth and product framing.
- `Analytics Engineer` + `Data Engineer`: ingestion, dbt, tests, reliability.
- `UI Expert`: frontend implementation after approved spec.
- `QA`: release gate.
- `Data Scientist / ML Expert`: prediction design, model validation, explainability, and drift monitoring.
- `Product Ops / Portfolio Manager` (funnel owner): intake, scoring, sequencing, and anti-scope-creep enforcement.
- `CFO` + `Legal Counsel`: cost/licensing/compliance approvals.

Do not skip role order for product-facing changes:
1. Product/UX definition
2. Data validation
3. Frontend build
4. QA sign-off

---

## Idea funnel and working mode (how and when to bring ideas)

### Where ideas go

- Capture all ideas in GitHub Issues with label `idea`.
- Every idea includes: user value, target competitions, target languages, and expected cost impact (`low`/`medium`/`high`).
- No direct implementation from chat ideas; every idea must pass funnel stages first.

### Weekly funnel rhythm

1. **Collect** (continuous): ideas land in `idea` queue.
2. **Triage** (1x/week): funnel owner removes duplicates and clarifies scope.
3. **Score** (1x/week): apply intake score and budget screen.
4. **Select**: move only top items into `Next`; keep one objective in `Now`.
5. **Decide**: escalate only gate-triggering items to CPO.

### Capacity split (default)

- 60% reliability and data trust
- 25% product improvements (analytics content, UX polish)
- 15% exploration (predictions, new competitions, new languages)

If reliability degrades, exploration drops to `0%` until recovery.

### Intake template (required fields)

- Problem statement
- User value
- Competitions impacted (`league_code` list)
- Languages impacted
- Data dependencies
- Delivery risk
- Cost impact (Cursor/API/infra)
- "What we will not do" (scope boundary)

---

## Decision-needed gates (founder interrupt policy)

You are required only for:

1. Scope/cost changes:
   - history window
   - ingest profile
   - fanout and cost caps
2. Product gate failures:
   - data gate fail
   - UX gate fail
3. Legal/commercial risk:
   - API/data license uncertainty
   - tracking/privacy changes
   - branding/IP concerns
4. Stage transitions:
   - architecture spend step-up
   - new competition rollout with meaningful quota/cost impact
5. Prediction/ML decisions:
   - new model family choice
   - explainability method change
   - promotion from shadow mode to user-facing predictions

If none of the above is triggered, agents proceed autonomously.

---

## Anti-scope-creep protocol (non-negotiable)

### 1) One active objective

Keep exactly one `Now` objective at a time:
- Example: "Reliable daily ingest + match preview publish."

Everything else is `Next` or `Later`.

### 2) WIP limits

- Max 1 in-progress platform initiative.
- Max 2 in-progress tactical tasks.
- No third task starts before one closes.

### 3) Intake score (before work starts)

Every new idea gets a score from 1 (low) to 5 (high):
- User value
- Strategic fit (North Star)
- Cost impact
- Delivery risk
- Reuse potential

Only start items with:
- value >= 4
- strategic fit >= 4
- cost impact <= 3 (unless explicitly approved)

### 4) Definition of done freeze

Before implementation, freeze:
- exact outcome
- touched systems
- verification checks

No silent scope expansion mid-task.

### 5) Kill rule

Stop or defer any item that:
- adds complexity without measurable user value,
- requires budget increase without pre-approval,
- blocks critical reliability work.

---

## Budget guardrails (starting defaults)

Adjust numbers after one operating cycle.

### Cursor budget guardrails

- Soft cap: 3 substantial agent execution cycles per day.
- Hard cap: 5 cycles per day.
- Rule: if soft cap is hit, only reliability and release-blocking work continues.

### API budget guardrails

- Soft cap: 70 requests/day per key.
- Hard cap: 90 requests/day per key (assuming free-tier style constraints).
- Rule: when soft cap is hit, prioritize upcoming fixtures and defer archive fanout.

### Spend escalation trigger

Escalate budget only if both are true:
- reliability SLO is stable,
- at least one growth or retention signal improves after previous investments.

---

## Roadmap by stage (no calendar promises)

## Stage 0 - Autonomous reliability baseline

Goal: zero-surprise pipeline and predictable publish flow.

Deliverables:
- decision-needed label and issue template
- PR template with Data Gate and UX Gate checkboxes
- workflow health dashboard habit (Actions failures monitored daily)

Exit criteria:
- scheduled ingest/build/deploy are stable,
- founder interruptions happen only for gate events.

## Stage 1 - Product quality and trust

Goal: every surfaced metric is clear, tested, and explainable.

Deliverables:
- metric catalogue ownership enforced
- null/missing behavior explicit in product copy and specs
- stricter test coverage for critical marts

Exit criteria:
- no unresolved metric ambiguity in release PRs,
- quality gates pass consistently.

## Stage 2 - Explainable prediction foundation

Goal: ship prediction capability early, but transparently and safely.

Deliverables:
- `Data Scientist / ML Expert` role operating with Football Analytics + BI alignment
- baseline explainable models (e.g. calibrated logistic/Poisson-style approach) before complex black-box models
- feature and target definitions documented per competition
- prediction outputs include confidence and explanation fields
- shadow-mode validation before user-visible rollout

Exit criteria:
- prediction quality exceeds agreed baseline on holdout windows,
- explanations are readable by non-technical fans,
- legal/commercial and UX gates pass.

## Stage 3 - Lean growth instrumentation

Goal: measure usage and sharing without heavy overhead.

Deliverables:
- privacy-friendly event tracking for funnel steps
- share rate and retention reporting loop
- decision reports tied to product changes

Exit criteria:
- roadmap prioritization uses behavioral evidence, not intuition.

## Stage 4 - Scale preparation

Goal: prepare architecture and economics for larger reach.

Deliverables:
- explicit build-vs-buy decisions per subsystem
- API and infrastructure cost thresholds documented
- migration path for backend/API layer when static export is insufficient

Exit criteria:
- stage-transition decisions are evidence-based and financially bounded.

---

## Weekly founder control loop (lightweight)

1. Check Actions failure view.
2. Check decision-needed issue queue.
3. Approve, defer, or reject only gated items.
4. Re-confirm `Now` objective and WIP limits.
5. Move one `Next` item into `Now` only after closure.

Keep this loop short and strict.
