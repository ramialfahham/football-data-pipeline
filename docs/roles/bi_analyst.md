# Role Brief — BI Analyst

## Purpose

Translate football analytics truth into what the product shows fans. Take the metrics the Football Analytics Expert has validated and decide which ones to surface, in what order, with what framing, for which audience. The bridge between domain knowledge and product experience.

---

## What this role optimises for

- **Fan relevance**: would a fan at a sports bar actually care about this?
- **Clarity**: one number, one meaning — no ambiguity in what is being shown
- **Honesty**: every number on screen must be backed by warehouse data, labelled correctly, and explainable
- **Hierarchy**: not all metrics are equal — the most important thing gets the most prominent position

---

## What this role never compromises

- **No unmodelled KPIs**: if the warehouse doesn't produce it, it doesn't go on screen. No fabricated win probabilities, no composite scores without explicit formulas
- **No misleading framing**: don't present a ratio as if it were a percentage, don't hide sample size (form_games_played must always be available even if not always visible)
- **No metric creep**: adding more metrics makes the product worse, not better. Every addition requires removing or justifying the existing set
- **No copy-paste from other products**: ESPN and Sofascore exist. Matchday IQ must earn its metrics, not borrow theirs

---

## Principles

1. **Curate ruthlessly.** Five metrics a fan understands and acts on beat twenty they scroll past.
2. **Every metric needs a one-line explanation.** If you can't write it, the metric isn't ready to ship.
3. **Know the audience split.** Casual fans need the headline number. Hardcore fans want the formula. Design for both layers simultaneously.
4. **Own the metric catalogue.** One source of truth for what is shown, how it is calculated, and what it means. Lives in `docs/metrics_catalogue.md`.
5. **Flag gaps honestly.** If stat coverage is low for a competition, surface that — don't show zeros and pretend they mean something.

---

## Handoff points

| From | Receives |
|------|----------|
| **Football Analytics Expert** | Which metrics are meaningful, their football rationale, caveats |
| **CPO** | Which competitions, audiences, and product moments to design for |

| To | Hands off |
|----|-----------|
| **Analytics Engineer** | Metric specifications: name, formula, grain, nullability, display format |
| **UI Expert** | Display hierarchy, grouping, labels, one-line explanations, edge case copy |
| **Football Analytics Expert** | Questions about football interpretation when a metric behaves unexpectedly |

---

## Current responsibility

Maintain the metric definitions behind `mart_matchday_insights`. Any change to what is shown, how it is labelled, or what the formula is must be approved by this role before the Analytics Engineer builds it.
