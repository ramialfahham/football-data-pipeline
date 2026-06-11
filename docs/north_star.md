# North Star — Matchday IQ

## The product

A **fun, sticky pre-match companion for football fans** — the app you open in the sports bar before kickoff, share with your group chat, and argue over.

Not a statistics database. Not a betting tool. A product that makes fans feel smarter and more engaged before a match — casual enough to onboard anyone, deep enough to satisfy hardcore fans.

---

## Scale ambition

**Platform / media product.** Millions of users, partnerships with leagues or broadcasters, data licensing. This is built to be big.

---

## Who it's for

**Both casual and hardcore fans.**
- Casual: watch a few matches a week, want to sound smart in the group chat, share a card before kickoff
- Hardcore: follow every matchday, read tactics, want depth and detail on demand

The surface is simple. The depth is there for those who want it.

---

## The experience (in one sentence)

Open the app, instantly see what's on today across competitions, tap a match, and within seconds have five things worth saying about it.

---

## Navigation flow

**v2 — the website (target, epic #361):** defined in [`site_architecture.md`](site_architecture.md) §3–4. Hybrid IA: browse by competition group (Leagues / Cups / Continental club / National teams) **and** by country hub; programmatic pages for every competition, fixture, team and player under locale-prefixed URLs. Home is **fixtures-first** — upcoming matches across competitions — with browse, storylines and stats below.

**Legacy MVP (live until cutover, #377):** the card-based mobile app — Landing (competition cards) → Fixture list (next round only) → Fixture detail (analysis carousel). It stays fully functional until v2 reaches parity and the CPO signs off the switch.

---

## What makes it sticky

- **Best UX in the category** — faster, cleaner, more beautiful than anything else
- **Deeper stats than anyone** — more metrics, more history, more competitions
- **Most fun and shareable** — built for group chats and sports bars, opinionated and visual
- **All competitions in one place** — Bundesliga, WC, PL, La Liga — everything unified
- **Multilingual from day one** — German, English, Finnish, Spanish, French, Italian, Dutch, Portuguese (browser locale default, manual switcher)
- Always something relevant — no dead states. Qualifier fallback, previous season fallback. Never empty.

---

## What we show (and what we don't)

**Show**: form-based metrics grounded in real warehouse data — goals, shots, pass accuracy, save rate, points capture, danger zone ratio, and more. **In-season** domestic leagues: a **rolling window of up to the last five finished matches** in the current competition; **before the season starts**, the **full previous season** for that league. **WC:** through Group Stage Matchday 1, **all** relevant qualifier matches; from Group Stage Matchday 2 onward, **all finished WC matches so far** (cumulative, no five-game cap). When the warehouse exposes a metric as null (optional stat missing or undefined rate), the **mobile-first** match preview shows **“-”** for that value only — cards and fixtures stay visible; we do **not** fabricate zeros.

**Don't show**: fabricated win probabilities, unmodelled KPIs, anything we can't back with data. Data honesty is non-negotiable. **Integrity failures** (e.g. finished fixture without a valid scoreline) must **fail the pipeline** — they are not a UX copy problem.

---

## Business model

Multiple revenue streams, built in layers:

1. **Freemium / subscription** — core free, power features behind a paywall
2. **B2B data / API** — sell data or insights to clubs, media companies, operators
3. **Partnerships / sponsorships** — league or broadcaster deals, branded content
4. **Advertising** — at scale, native or display

---

## Competitions roadmap

**45 competitions are onboarded and active** — domestic leagues, cups, continental club and national-team competitions across confederations. The single source of truth is [`competition_registry.yml`](competition_registry.yml); adding a competition is one registry entry and nothing else (the zero-file rule, CI-enforced).

| Phase | Status |
|-------|--------|
| Bundesliga pilot | ✅ done |
| WC 2026 + linked qualifiers | ✅ ingested (tournament runs summer 2026) |
| Major European leagues + cups | ✅ live |
| Onboarding waves 1–5 (→ 45 competitions) | ✅ live |
| Further competitions | registry decision per competition (CPO), zero-file onboarding |

**WC 2026 note**: Through Group Stage Matchday 1, form uses **all** finished qualifier matches for each team across the confederation + inter-confederation competitions linked to WC 2026 in the registry. From Group Stage Matchday 2 onward, only **WC** `league_code` matches count — **all finished tournament games so far** (cumulative).

---

## Future features (in priority order)

1. **Cool visualizations** — radar charts, trend lines. Stats you can feel. (Shot maps are **data-gated**: the provider feed has no shot coordinates — do not design them until a data source exists.)
2. **Predictions** — rule-based first, ML eventually. Honest probabilities, not guesses.
3. **Social / sharing** — share a match card, start a debate, see what your friends think.
4. **Live match companion** — stats updating in real time during the match.
5. **Historical deep dives** — head-to-head history (✅ modelled: `mart_head_to_head`), season comparisons, player career arcs.

---

## Next milestone

**Make it so good I'm proud to show anyone.**

Quality bar first. Growth comes after the product deserves it.

---

## Technical north star

- Adding a new competition requires **a single entry in `docs/competition_registry.yml` and nothing else** — the zero-file rule, CI-enforced (`check_layer_contract.py`, `check_registry_var_sync.py`). Raw tables are unified with a `league_code` discriminator; staging models are generic (one per entity, never per competition); **no changes to staging, base, core, intermediate, or marts**.
- `league_code` is the partition key on everything. Never hardcode a competition.
- Data quality is automated and enforced. The product must be trustworthy at all times without manual verification.
- Architecture: Python ingestion → BigQuery raw → dbt (staging → base → core → marts) → GitHub Pages UI.

---

## Roles

| Role | Responsibility | Brief |
|------|----------------|-------|
| CPO | Product decisions, priorities, vision | — |
| [Football Analytics Expert](roles/football_analytics_expert.md) | Which metrics matter in football and why — domain truth | |
| [BI Analyst](roles/bi_analyst.md) | What to show fans and how to frame it — product translation | |
| [Analytics Engineer](roles/analytics_engineer.md) | dbt models, data quality, layer architecture | |
| [Data Engineer](roles/data_engineer.md) | Ingestion, BigQuery, pipeline reliability | |
| [UI Expert](roles/ui_expert.md) | Design, UX, frontend implementation | |
| [Growth Expert](roles/growth_expert.md) | Stickiness, engagement, sharing, retention | |
| [CFO / Financial Advisor](roles/cfo.md) | Cost tracking, revenue modeling, stage-gate investment decisions | |
| [CTO / Tech Strategist](roles/cto.md) | Tech stack evolution, stage-appropriate architecture, build vs. buy | |
| [Product Analyst](roles/product_analyst.md) | App tracking, funnel analysis, retention metrics, behavioural insight | |
| [Legal Counsel](roles/legal_counsel.md) | Data licensing, user privacy, IP and commercial risk | |
