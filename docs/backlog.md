# Product Backlog

**Owner:** CPO
**Last updated:** 2026-05-03

Items are in priority order within each track. Status values: `not started` · `in progress` · `blocked` · `done`.

---

## Track 1 — WC 2026 pipeline (sequential)

| # | Item | Why | Status | Lead |
|---|------|-----|--------|------|
| W1 | Ingest WC26 fixtures + staging models | Prerequisite for everything WC26. Registry is `in_progress`. | not started | Data Engineer |
| W2 | WC26 participants seed (`seeds/wc26_participants.csv`, 48 teams) | Needed to filter qualifier form data to actual WC participants. Inter-confederation playoffs done — unblocked. | not started | Data Engineer |
| W3 | WC26 qualifier form ingestion (`/fixtures?team={id}&last=10` per team) | Pre-tournament form comes from qualifiers, not a single league. 48 API calls for initial backfill. | not started | Data Engineer |
| W4 | WC26 intermediate — form source transition logic | Switches from qualifier form to tournament form after the first WC match. Scoped to WC26. | not started | Analytics Engineer |
| W5 | Activate `statistics_fixtures` for WC26 when API makes it available | Not live as of 2026-04-27. Monitor coverage flag via `/leagues?id=1&season=2026` and flip when ready. | blocked on provider | Data Engineer |

---

## Track 2 — UI (parallel with Track 1)

| # | Item | Why | Status | Lead |
|---|------|-----|--------|------|
| U1 | Landing page — competition cards | Entry point for multi-competition. Must ship before BL1 season ends so WC26 gets a card automatically on go-live — no UI changes needed. | not started | UI Expert |
| U3 | Multilingual support (DE / EN / FI / ES / FR / IT / NL / PT) | North star requirement. Browser locale default + manual switcher. Must ship before WC26 goes live. | not started | UI Expert |
| U2 | Multi-competition routing for WC26 (fixture list + detail) | Current UI is hardcoded to BL1. WC26 needs its own fixture and detail views. | not started | UI Expert |

---

## Prerequisite for Big 5 + BL2 onboarding

| # | Item | Why | Status | Lead |
|---|------|-----|--------|------|
| P3 | `history_seasons` field in registry + ingestion honours it | Without prior season data the UI is empty on matchday 1. Rule: domestic league joining mid-cycle → `history_seasons: 1`; joining at season start → `history_seasons: 0`. At ~1,500–2,000 API calls per season, one previous season fits within the 7,500/day budget. Must be done before any Big 5 or BL2 onboarding starts. | not started | Analytics Engineer + Data Engineer |

---

## Planned — Big 5 leagues + BL2 (post WC26)

Onboarding order to be decided by CPO. All require P3 to be complete first.

| # | Competition | `league_code` | Registry status |
|---|-------------|---------------|-----------------|
| L1 | Premier League | PL | planned |
| L2 | La Liga | PD | planned |
| L3 | Serie A | SA | planned |
| L4 | Ligue 1 | L1 | planned |
| L5 | 2. Bundesliga | BL2 | planned |

---

## Planned — product features (post WC26)

| # | Item | Why | Status | Lead |
|---|------|-----|--------|------|
| U4 | Visualizations — radar charts, shot maps, trend lines | Makes the product feel premium and shareable. | backlog | UI Expert + Football Analytics Expert |
| U5 | Sharing — match card export / group chat integration | Core stickiness mechanism. | backlog | UI Expert + Growth Expert |
| P1 | Predictions — rule-based (form + home advantage) | North star future feature. Scope once WC26 is live. | backlog | Football Analytics Expert + Analytics Engineer |
| P2 | Live match companion | Real-time stats during matches. | backlog | UI Expert + Data Engineer |

---

## Notes

- **API budget:** 7,500 requests/day. Each domestic league season costs ~1,500–2,000 calls. Plan backfills accordingly — see `docs/operations_guide.md`.
- **WC26 history:** qualifiers serve as the history window. `history_seasons: 0` for the main tournament; qualifier form is handled via the team-based form endpoint (W3).
- **Competition registry** (`docs/competition_registry.yml`) is the authoritative source for status, API IDs, and form strategy. The backlog reflects product priority — the registry reflects technical readiness.
- **Never show empty states.** If a competition has no current matches, fall back to previous season data or qualifier data. The product must always have something relevant to show.
