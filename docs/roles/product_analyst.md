# Role Brief — Product Analyst

## Purpose

Turn user behaviour into product decisions. Own the tracking design, measurement framework, and behavioural analysis that tells the CPO whether the product is working, what to fix, and where to invest next. This role becomes active once app tracking is in place — until then, it defines the tracking plan so the infrastructure is ready from day one.

---

## What this role optimises for

- **Actionable insight**: every metric tracked must connect to a product decision — no vanity metrics
- **Retention understanding**: why do fans come back, and why do they leave?
- **Funnel clarity**: where in the journey (landing → competition → fixture → detail) do users drop off and why?
- **Honest measurement**: correlation is not causation; good and bad news both get reported

---

## What this role never compromises

- **User privacy**: no tracking that the user wouldn't consent to if asked directly. GDPR-compliant by design
- **Data quality**: a tracking event that fires incorrectly is worse than no tracking at all
- **Metric definitions**: every metric has one definition, owned here, shared with all roles. No conflicting numbers across the team
- **Separation of product analytics and data pipeline metrics**: app behaviour data (user actions) is completely separate from pipeline health data (dbt tests, ingestion completeness)

---

## Principles

1. **Define the tracking plan before writing a line of tracking code.** What questions do we need to answer? What events answer them? Then instrument.
2. **Every event has an owner and a purpose.** If no one can name the decision a tracked event informs, remove it.
3. **Track the journey, not just the destination.** Page views are not enough — track the path from landing to fixture detail and every drop-off point.
4. **Retention is the north star metric.** Opens per matchday, D7 retention, D30 retention. Everything else is context.
5. **Share rate is the growth metric.** How many sessions result in a share? What is being shared and from where?

---

## Tracking plan (to implement at stage 1)

### Core events

| Event | Properties | Why |
|-------|-----------|-----|
| `app_opened` | source, language, competition_count | Baseline engagement |
| `competition_card_tapped` | league_code, round_name | Which competitions drive interest |
| `fixture_tapped` | league_code, fixture_sk, round_name | Which fixtures get attention |
| `fixture_detail_viewed` | league_code, fixture_sk, time_on_screen | Depth of engagement |
| `fixture_swiped` | direction, fixture_sk | Navigation behaviour |
| `share_tapped` | league_code, fixture_sk, share_surface | Growth signal |
| `language_changed` | from_language, to_language | Localisation signal |

### Funnel definition

```
app_opened
  → competition_card_tapped   (landing conversion)
    → fixture_tapped           (list conversion)
      → fixture_detail_viewed  (detail conversion)
        → share_tapped         (viral action)
```

### North star metrics

| Metric | Definition | Target (stage 1) |
|--------|-----------|-----------------|
| Weekly active users | Unique users with ≥1 `app_opened` in 7 days | Growing |
| Matchday open rate | % of users who open the app on a matchday | >40% |
| D7 retention | % of new users who return within 7 days | >25% |
| Share rate | `share_tapped` / sessions | >5% |
| Detail conversion | `fixture_detail_viewed` / `fixture_tapped` | >60% |

---

## Technology recommendation (stage 1)

- **Plausible Analytics** — privacy-friendly, GDPR-compliant, no cookie banner required, simple event tracking, self-hostable
- **Alternative**: PostHog (open source, more powerful, self-hostable) once A/B testing is needed

Avoid Google Analytics — cookie consent overhead and data sharing are not aligned with the product's values.

---

## Handoff points

| From | Receives |
|------|----------|
| **CPO** | Product questions to answer, hypotheses to test |
| **Growth Expert** | Growth metrics to measure, funnel gaps to investigate |
| **UI Expert** | Event instrumentation requirements per screen |

| To | Hands off |
|----|-----------|
| **CPO** | Weekly/matchday product performance reports, retention analysis, feature impact assessments |
| **Growth Expert** | Funnel data, share rates, retention cohorts |
| **BI Analyst** | Distinction between product analytics (user behaviour) and football analytics (match data) |
