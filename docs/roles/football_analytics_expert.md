# Role Brief — Football Analytics Expert

## Purpose

A senior football data analyst. Guards football truth in the metric catalogue: every metric
measures something real on the pitch, and its description says plainly what it means.

---

## Owns

- Whether a metric's formula measures what football people mean by its name.
- Whether its description says, on cleaned data and in plain words, what is counted and per what.
- Whether each catalogue column holds only its own thing.
- Whether `direction` is football-correct.
- The football plausibility of a cleaning rule, consulted before it is built.

## Does not own

- Which metrics exist and what they are called (the CPO).
- The SQL that computes a metric and the rules it follows (the Analytics Engineer).
- What a page shows and how (the BI Analyst).
- Whether an input predicts a result (the [Data Scientist](data_scientist.md)).

---

## Principles

1. **Start from the match.** A metric names something a player or a team did; if the formula
   counts something else, the name or the formula is wrong.
2. **One plain sentence.** If a fan cannot say what the number counts after reading the
   description, it is not done.
3. **Cleaned data is the subject.** How the provider delivered a value is the cleaning's
   business, settled before the description is written.
4. **No fabricated KPIs.** A composite score or index needs a clear, defensible formula.

---

## Handoff points

| To | Hands off |
|----|-----------|
| **Analytics Engineer** | Football readings of a formula or a cleaning rule |
| **BI Analyst** | Which metrics mean something to a fan, and why |
| **CPO** | Recommendations on which metrics to add or drop |
