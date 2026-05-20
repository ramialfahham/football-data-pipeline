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

```
Landing page
  └─ Competition cards (one per active competition, sorted by next kickoff)
       └─ Fixture list (next round / matchday only)
            └─ Fixture detail (deep dive — the analysis carousel)
```

- **Landing**: Cards for each active competition — competition name, current round label (e.g. "Spieltag 32", "Gruppenphase", "Achtelfinale"), next fixture date, number of upcoming fixtures.
- **Fixture list**: All fixtures for the next round. Clean list — teams, kickoff time, subtle form signal.
- **Fixture detail**: Full pre-match analysis. Swipe left/right between fixtures in the same round.

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

| Phase | Competition | Status |
|-------|-------------|--------|
| Live | Bundesliga (D1) | ✅ |
| Next | WC 2026 + qualifiers | 🔜 |
| After WC | Premier League, La Liga, Serie A | 📋 |
| Future | All major competitions | 🌍 |

**WC 2026 note**: Through Group Stage Matchday 1, form uses **all** finished qualifier matches for each team across the confederation + inter-confederation competitions linked to WC 2026 in the registry. From Group Stage Matchday 2 onward, only **WC** `league_code` matches count — **all finished tournament games so far** (cumulative).

---

## Future features (in priority order)

1. **Cool visualizations** — radar charts, shot maps, trend lines. Stats you can feel.
2. **Predictions** — rule-based first, ML eventually. Honest probabilities, not guesses.
3. **Social / sharing** — share a match card, start a debate, see what your friends think.
4. **Live match companion** — stats updating in real time during the match.
5. **Historical deep dives** — head-to-head history, season comparisons, player career arcs.

---

## Next milestone

**Make it so good I'm proud to show anyone.**

Quality bar first. Growth comes after the product deserves it.

---

## Technical north star

- Adding a new competition requires **ingestion config, per-endpoint staging models, and one `ref()` line per base UNION** (mechanical, CI-checked via `assert_base_*_covers_active_competition_var` + `scripts/check_registry_var_sync.py`). **No changes to core, intermediate, or marts** once the endpoint surfaces exist in unified bases.
- `league_code` is the partition key on everything. Never hardcode a competition.
- Data quality is automated and enforced. The product must be trustworthy at all times without manual verification.
- Architecture: Python ingestion → BigQuery raw → dbt (staging → base UNION ALL → core → marts) → GitHub Pages UI.

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
