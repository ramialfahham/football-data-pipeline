# North Star — Matchday IQ

## The product

A **fun, sticky pre-match companion for football fans** — the app you open in the sports bar before kickoff, share with your group chat, and argue over.

Not a statistics database. Not a betting tool. A product that makes fans feel smarter and more engaged before a match.

---

## Who it's for

Football fans who:
- Watch matches socially (sports bar, group chats, with friends)
- Want to know what's worth talking about before a match
- Are not analysts — they want the insight, not the spreadsheet

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

- **Landing**: Cards for each active competition. Shows competition name, current round label (e.g. "Spieltag 32", "Gruppenphase", "Achtelfinale"), next fixture date, number of upcoming fixtures. Tappable.
- **Fixture list**: All fixtures for the next round of that competition. Clean list — teams, kickoff time, subtle form signal. Tap to go deep.
- **Fixture detail**: The full pre-match analysis. Swipe left/right to move between fixtures in the same round.

---

## Competitions roadmap

| Phase | Competition | Status |
|-------|-------------|--------|
| Live | Bundesliga (D1) | ✅ |
| Next | WC 2026 + qualifiers | 🔜 |
| After WC | Premier League, La Liga, Serie A | 📋 |

**WC 2026 note**: Before the first match, form metrics use the last 5 qualifier matches per team (all confederation qualifiers + inter-confederation playoffs, filtered to WC 2026 participants). Once WC matches begin, qualifier data is dropped — current tournament games only.

---

## What makes it sticky

- Always something relevant — no dead states, no empty screens. If there's no current-season data, we use qualifiers or the previous season.
- Covers the competitions fans care about, not just one league.
- Fast to the insight — no drilling through menus.
- Shareable — a card or a link that works in a group chat.
- Multilingual: **German, English, Finnish** (browser locale default, manual switcher available).

---

## What we show (and what we don't)

**Show**: form-based metrics grounded in real data — goals, shots, pass accuracy, save rate, points capture, danger zone ratio, etc. over the last 5 matches.

**Don't show**: fabricated win probabilities, unmodelled KPIs, anything we can't back with warehouse data. Data honesty is non-negotiable.

**Future**: cool visualizations (radar charts, shot maps, trend lines), predictions (rule-based first, ML later), statistical analyses, social/sharing features.

---

## Technical north star

- Adding a new competition should require **only ingestion config + a staging model** — no changes to core or marts.
- `league_code` is the partition key on everything.
- Data quality is automated and enforced — the product must be trustworthy at all times without manual verification.
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
