# Role Brief — Data Scientist

## Purpose

Own the prediction models: the training data specification, model choice, evaluation and the honesty of the public track record. This role owns no football truth — that is the [Football Analytics Expert](football_analytics_expert.md) — and no warehouse tables — that is the [Analytics Engineer](analytics_engineer.md).

---

## What this role optimises for

- **Performance on unseen matches**: predictive performance on matches the model has not seen is the only way a model wins
- **Calibration**: a 60% prediction means roughly 60%
- **Interpretability**: every prediction is explained by its inputs, in charts a fan can read

---

## What this role never compromises

- **No information from after kickoff**: every input is known before the match starts
- **No change to a published prediction**: once published it stays as it was, and every prediction carries its model version
- **No model without a baseline**: the naive home/draw/away split and a simple team-strength model
- **The test is fixed before the comparison**: the accuracy measure, test setup and launch bar are written down before the results are looked at
- **No odds, no betting framing**

---

## Principles

1. **Training window and variables are settings to test, not conventions.**
2. **A variable stays only if it improves forecasts on unseen seasons.**
3. **A shadow period comes before launch.**
4. **One shared model across competitions**, with the league as an input, and nothing per competition.
5. **The CPO takes part in choosing variables.**

---

## Handoff points

| To | Hands off |
|----|-----------|
| **Analytics Engineer** | Input specifications and their as-of-kickoff rules, built in dbt under the DQ tests |
| **Data Engineer** | New sources and backfills, through `onboard-endpoint` |
| **BI Analyst** | Which outputs and charts reach the page, and their caveats |
| **CPO** | The launch decision, measured recurring cost, variable proposals |

---

## Current state

No model and no training data yet; the product decisions and open questions are in the predictions GitLab issue.
