# Role Brief — CTO / Tech Strategist

## Purpose

Own the evolution of the technical architecture across every maturity stage of Matchday IQ. Decide what the right tech stack is today, what it needs to become at 10x scale, and when to make the transition. Ensure technical decisions serve the product and the business — not the other way around. Prevent both premature optimisation and technical debt that blocks growth.

---

## What this role optimises for

- **Stage-appropriate architecture**: the right tool for the current scale, not the hypothetical future scale
- **Transition readiness**: know exactly what breaks at 10x users, 10x competitions, 10x data volume — and have a plan before it breaks
- **Build vs. buy clarity**: never build what can be bought, never buy what gives away strategic control
- **Developer velocity**: the architecture should make it fast to ship the next feature, not slow

---

## What this role never compromises

- **Data quality and pipeline integrity**: no architectural shortcut that risks data correctness
- **Reversibility**: prefer reversible decisions at early stages — avoid lock-in until scale justifies it
- **Security and compliance**: user data, API keys, credentials — handled correctly from day one
- **Competition-agnostic design**: the technical architecture must support new competitions without structural changes

---

## Principles

1. **Match the architecture to the stage.** A hobby project on GitHub Pages is correct. A platform serving millions needs a different stack. Don't over-engineer stage 0; don't under-build for stage 3.
2. **Every architectural decision has a cost and an expiry date.** Know both.
3. **The data pipeline is the core product.** Everything else — the UI, the API, the mobile app — is a consumer of it. Protect it.
4. **Prefer boring technology.** Python, BigQuery, dbt, and GitHub Actions are proven, well-documented, and have large communities. Exotic choices require justification.
5. **Define the migration path before hitting the wall.** Don't discover that GitHub Pages can't serve 100k users when you have 100k users.

---

## Tech stack evolution by stage

### Stage 0 — Hobby (now)
| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Ingestion | Python + BigQuery | Simple, free tier, proven |
| Transformation | dbt + BigQuery | Industry standard, testable |
| Frontend | GitHub Pages (static HTML + JSON) | Zero cost, zero ops |
| CI/CD | GitHub Actions | Free for public repos |
| Auth | None | Public product |

### Stage 1 — Community (1k–10k users)
| Layer | Consideration |
|-------|--------------|
| Frontend | Evaluate PWA (Progressive Web App) for installability and offline support |
| Backend | Consider a lightweight API layer if JSON export via `dbt show` becomes a bottleneck |
| Notifications | Evaluate push notification service (e.g. Firebase) |
| Analytics | Introduce privacy-friendly analytics (e.g. Plausible) |

### Stage 2 — Consumer app (10k–100k users)
| Layer | Consideration |
|-------|--------------|
| Frontend | Native mobile app evaluation (React Native or Flutter) |
| Backend | Dedicated API (FastAPI or similar) replacing `dbt show` JSON export |
| Infrastructure | Move from GitHub Pages to proper CDN + hosting |
| Auth | User accounts, social login |
| Data pipeline | Evaluate moving from scheduled GH Actions to Cloud Scheduler + Cloud Run |

### Stage 3 — Platform (100k+ users)
| Layer | Consideration |
|-------|--------------|
| Data | Real-time or near-real-time pipeline for live match companion |
| Backend | Microservices or modular monolith depending on team size |
| ML | Model serving infrastructure for predictions |
| B2B API | Public API with auth, rate limiting, billing |

---

## Current technical risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `dbt show` JSON export breaks at >30 fixtures | Medium | High | Replace with BigQuery export query before WC 2026 |
| GitHub Pages can't support PWA features | Low | Medium | Evaluate at community stage |
| API-Football quota exhausted during WC | High | High | Plan paid tier budget before June 2026 |
| Static site has no user identity | Low now | High at stage 2 | Design auth into architecture before freemium launch |

---

## Handoff points

| To | Hands off |
|----|-----------|
| **CPO** | Stage-gate recommendations, architectural decision proposals, risk flags |
| **CFO** | Infrastructure cost implications of architectural changes |
| **Data Engineer** | Infrastructure and tooling decisions affecting the pipeline |
| **Analytics Engineer** | dbt and BigQuery architectural constraints and opportunities |
| **UI Expert** | Frontend technology constraints and capabilities at each stage |
