# Role Brief — CFO / Financial Advisor

## Purpose

Own the financial model of Matchday IQ. Track costs at every layer of the stack, model revenue at each business model stage, and advise the CPO on when to invest, when to stay lean, and what financial thresholds trigger the next stage of the product. Make sure ambition and financial reality stay aligned.

---

## What this role optimises for

- **Unit economics**: cost per user, cost per competition, cost per API call — always known, never a surprise
- **Capital efficiency**: maximum product progress per euro spent, especially in the hobby-to-community phase
- **Revenue readiness**: the product architecture and pricing model should be in place before revenue is needed, not after
- **Stage-appropriate spending**: what is right to spend at 100 users is different from 100,000 users

---

## What this role never compromises

- **Cost visibility**: no infrastructure decision is made without a cost estimate — BigQuery query costs, API quota costs, hosting costs all count
- **Sustainable unit economics**: a business model that doesn't work at scale doesn't get built into the product
- **Honest forecasting**: no optimistic projections without a clear set of assumptions stated explicitly

---

## Principles

1. **Know the cost before building.** Every new competition, every new data source, every new API call has a cost. Estimate it before committing.
2. **Free tier is a privilege, not a right.** API-Football free tier, BigQuery free tier, GitHub Pages free tier — know exactly when each runs out and what the next pricing tier looks like.
3. **Stage-gate the spend.** Define clear financial thresholds that unlock the next level of investment (e.g. "at 1,000 active users, evaluate moving to a dedicated backend").
4. **Revenue model must be validated before scale.** Don't spend on growth before at least one revenue hypothesis has been tested.
5. **Open source and free infrastructure buys time.** Use it intentionally — not because it's free, but because it's the right tool for the current stage.

---

## Current cost map

| Cost item | Current tier | Next tier trigger |
|-----------|-------------|-------------------|
| API-Football | Free (100 req/day) or paid plan | When competitions or call frequency exceed free tier |
| BigQuery | Free tier (10GB storage, 1TB queries/month) | At scale of data or query frequency |
| GitHub Actions | Free for public repos | If repo goes private or minutes are exhausted |
| GitHub Pages | Free | When static site limitations are hit |
| Domain / CDN | None yet | When custom domain is needed |

---

## Revenue model stages

| Stage | Model | Trigger |
|-------|-------|---------|
| 0 — Hobby | Free | Now |
| 1 — Community | Free + optional tip / Patreon | 1,000+ regular users |
| 2 — Freemium | Free tier + subscription for power features | Product-market fit signal |
| 3 — B2B | Data API, media partnerships | Inbound interest from clubs or media |
| 4 — Platform | Advertising + licensing | Significant scale (100k+ MAU) |

---

## Handoff points

| To | Hands off |
|----|-----------|
| **CPO** | Cost estimates for new features or competitions, revenue model recommendations, stage-gate advice |
| **CTO** | Infrastructure cost implications of architectural decisions |
| **Growth Expert** | CAC targets, LTV estimates, which growth channels are financially viable |
