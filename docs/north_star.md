# North Star — Matchday Pilot

This document states the product vision: what Matchday Pilot is, who it serves, what it shows, and who builds it.

## The product

A **fun, sticky pre-match companion for football fans**. Fans open the site in the sports bar before kickoff, share it with their group chat, and argue over it.

Not a statistics database. Not a betting tool. A product that makes fans feel smarter and more engaged before a match. It is casual enough to onboard anyone and deep enough to satisfy hardcore fans.

## Scale ambition

**A platform and media product.** Millions of users, partnerships with leagues or broadcasters, data licensing. We build it to be big.

**Everything scales with the number of competitions, and scale is never the argument.** The value to the fan decides whether we build a feature. Its count of pages, rows or competitions is never an argument for or against it. The engineering must carry whatever the product decides; a build that cannot carry it is the defect.

A new competition must bring its pages, its data and its nightly rebuild by itself: no per-competition code, no page cap, no manual step. CI checks the warehouse half of this rule (`CLAUDE.md`, "Scalability rules"). The site build must meet it too.

**Money is a separate question, and we always ask it.** We measure recurring spend (warehouse bytes scanned, provider calls, hosting) before a feature runs nightly. We give the CPO (Chief Product Officer, the product owner) the number, and the CPO decides every time. Scale is not a cost argument; a bill is.

## Who it is for

**Both casual and hardcore fans.**

- Casual: watch a few matches a week, want to sound smart in the group chat, share a card before kickoff.
- Hardcore: follow every matchday, read tactics, want depth and detail on demand.

The surface is simple. The depth is there for those who want it.

## The experience in one sentence

Open the site, instantly see what's on today across competitions, tap a match, and within seconds have five things worth saying about it.

## Navigation flow

[`site_architecture.md`](site_architecture.md) §3–4 defines the website's pages, addresses and navigation. The home page is fixtures-first: upcoming matches across competitions, composed as [`wireframes/10_home.md`](wireframes/10_home.md) defines. The website in `site_v2/` is the only product surface; `site/` is a frozen prototype and is offline.

## What makes it sticky

The product aims for these qualities.

| Quality | What it means |
|---------|---------------|
| **Best UX in the category** | Faster, cleaner and more beautiful than anything else. |
| **Deeper stats than anyone** | More metrics, more history, more competitions. |
| **Most fun and shareable** | Built for group chats and sports bars, opinionated and visual. |
| **All competitions in one place** | Bundesliga, World Cup, Premier League, La Liga: everything unified. |
| **Multilingual from day one** | German, English, Finnish, Spanish, French, Italian, Dutch and Portuguese. The browser language sets the default, and a manual switcher changes it. `site_architecture.md`, "Locale routing", lists the live locales. |
| **Always something relevant** | No dead states, never empty: a qualifier fallback and a previous-season fallback. |

## What we show, and what we do not

**Show:** form and season metrics grounded in real warehouse data, such as goals, shots, pass accuracy, save rate, points captured and shots from the box. [`metrics_context_model.md`](metrics_context_model.md) defines the two kinds and their windows. When the warehouse holds a metric as null, the page shows a dash (`–`) for that value only. The rest of the page stays visible, and the site never shows a fabricated zero.

**Do not show:** fabricated win probabilities, unmodelled key performance indicators, or anything the data cannot back. Data honesty is non-negotiable. An integrity failure, such as a finished fixture without a valid scoreline, must fail the pipeline. It is not a copy problem on the page.

## Business model

Multiple revenue streams, built in layers:

1. **Freemium or subscription**: the core is free, and power features sit behind a paywall.
2. **B2B data or API**: sell data or insights to clubs, media companies and operators.
3. **Partnerships and sponsorships**: league or broadcaster deals, branded content.
4. **Advertising**: native or display, at scale.

## Competitions

[`competition_registry.yml`](competition_registry.yml) lists every competition the pipeline ingests. It is the only hand-written list of competitions. Each new competition is a CPO decision. Onboarding one needs no new model, macro, SQL or Python file; `CLAUDE.md`, "How to add a new league", gives the procedure.

## Future features, in priority order

1. **Cool visualizations**: radar charts, trend lines. Stats you can feel. Shot maps are data-gated: the provider feed has no shot coordinates. Do not design shot maps until a data source exists.
2. **Predictions**: interpretable machine learning that must beat a simple baseline on seasons it has not seen. One prediction per match, frozen before kickoff and never changed, with a public track record. Honest probabilities, not guesses.
3. **Social and sharing**: share a match card, start a debate, see what your friends think.
4. **Live match companion**: stats that update in real time during the match.
5. **Historical deep dives**: head-to-head history, season comparisons, player career arcs. `mart_head_to_head` models head-to-head history.

## Roadmap

Quality bar first. Growth comes after the product deserves it.

The [GitLab milestones](https://gitlab.com/rami.al-fahham/football-data-pipeline/-/milestones) hold the roadmap: one milestone per menu page of the site, in menu order.

## Technical north star

- Adding a competition needs no new model, macro, SQL or Python file. CI enforces this rule (`CLAUDE.md`, "Scalability rules").
- `league_code` is the competition discriminator on every model. No business logic hardcodes a competition.
- Automated tests enforce data quality. The product must be trustworthy at all times without manual verification.
- The architecture:

```text
API-Football → Python ingestion → BigQuery raw tables
  → dbt: staging → base → core → intermediate → marts
  → JSON export → Astro site (site_v2/) → Firebase Hosting
```

## Roles

Each linked role has a brief in [`roles/`](roles/). A role is live only when something wakes it. A row in `.claude/review_routing.json` makes a role a gate-required reviewer. A brief with no routing row is a document nobody reads. The **Wakes on** column names what wakes each role.

| Role | Responsibility | Wakes on |
|------|----------------|----------|
| CPO | Product, copy, naming, cost, anything permanent. Merges. | every decision class in `working_agreement.md` §10 |
| [CTO / Tech Strategist](roles/cto.md) | Authority only: new mechanisms, dependencies, guard invariants, recurring cost, secrets. Owns no territory and reviews no implementation. | a property of the change. **12 rows**: the 9 guard paths, `*requirements*.txt`, `site_v2/package.json` + `package-lock.json` |
| [Platform and Reliability](roles/platform_reliability.md) | The machinery: scripts, tests, hooks, CI, dependency pinning, the site build and hosting. | `scripts/**`, `tests/**`, `*requirements*.txt`, `.claude/hooks/**`, `.github/workflows/**`, `.gitlab-ci.yml`, the site build + hosting config |
| [Analytics Engineer](roles/analytics_engineer.md) | dbt models, data quality, layer architecture | `dbt_project/**`, `scripts/export_*.py` |
| [Data Engineer](roles/data_engineer.md) | Ingestion, BigQuery, pipeline reliability | `ingestion/**`, the competition registry, the data contract |
| [Football Analytics Expert](roles/football_analytics_expert.md) | Which metrics matter in football and why: domain truth | `metric_catalogue.csv` |
| [Data Scientist](roles/data_scientist.md) | Prediction models: training data specification, model choice, evaluation, the public track record | nothing: brief only, no agent |
| [BI Analyst](roles/bi_analyst.md) | What to show fans and how to frame it: does the page tell a truth a fan can read | all of `site_v2/src/**`, the wireframes, `site/i18n/**` |
| Scope Auditor | The CPO's proxy: diff versus contract, §10 classes, secrets, undeclared thresholds | every commit except a bookkeeping-only commit |
| [SEO Expert](roles/seo_expert.md) | Findability: URLs, metadata, structured data, the internal link graph | nothing: brief and agent exist, no routing row; not commissioned |
| [UI Expert](roles/ui_expert.md) | Design, UX, frontend implementation | nothing: brief only, no agent |
| [Growth Expert](roles/growth_expert.md) | Stickiness, engagement, sharing, retention | nothing: advisor, consulted at contract time |
| [CFO / Financial Advisor](roles/cfo.md) | Cost tracking, revenue modeling, stage-gate investment | nothing: advisor; the cost tripwire lives on the CTO |
| [Product Analyst](roles/product_analyst.md) | App tracking, funnel analysis, retention, behavioural insight | nothing: advisor |
| [Data Journalist](roles/data_journalist.md) | Generated narrative and prose on the page | nothing: brief only; activates with the narrative generator, GAP-03 in the [gaps register](wireframes/99_gaps_register.md) |
| [Legal Counsel](roles/legal_counsel.md) | Data licensing, user privacy, IP and commercial risk | nothing: no release-readiness step exists |

**Functions that are mechanisms, not reviewer roles:**

| Function | Mechanism |
|----------|-----------|
| Quality Assurance | A gate-required evidence artifact. `git_discipline._acceptance_gate` refuses a commit to `site_v2/src/` until each acceptance criterion has evidence. |
| Editorial and Localisation | `scripts/check_copy_gate.py`, a mechanical check of user-visible strings. It runs in CI and in the Stop hook. Wording stays the CPO's. |
| Product | A step, not a role. The builder drafts acceptance criteria, and the CPO approves them before any code. The criteria then stay locked. |
