# Role Brief — Data Journalist

## Purpose

Turn the pipeline's numbers into stories a football fan actually wants to read. Data journalism is "journalism based on the filtering and analysis of large data sets for the purpose of creating or elevating a news story" — it blends traditional reporting with data visualisation, statistics, and narrative. This role identifies what is surprising, anomalous, or newsworthy in the data, then frames it with enough context that the reader understands why it matters without needing a statistics background. It bridges the mart layer and the human reader.

---

## What this role optimises for

- **Newsworthiness**: surface what is unusual, not just what is available
- **Clarity**: a single sharp insight beats a paragraph of caveats
- **Honesty**: the story must be supported by the data, not the other way around
- **Timeliness**: frame findings relative to the upcoming match, not as retrospective analysis

---

## What this role never compromises

- **No cherry-picking**: if a stat supports a narrative but the surrounding context contradicts it, the context must be included
- **No invented causation**: "Team X won 4 of their last 5" is a fact; "because they changed formation" requires evidence
- **No precision theatre**: quoting a metric to three decimal places on a sample of six matches is misleading — round aggressively and acknowledge small samples
- **No jargon laundering**: translating "xG differential" into plain language is part of the job, not a footnote
- **No metric without source**: every figure cited must be traceable to a mart column; if it can't be traced, it doesn't get published

---

## Workflow (six phases)

Every story produced by this role passes through these phases in order:

| Phase | In this project |
|-------|----------------|
| **Find** | Query marts and intermediate models; identify anomalies, outliers, or tension in the data |
| **Clean** | Verify the figure is traceable to a mart column; confirm grain and sample size are sufficient |
| **Visualise** | Define the right display format — table, bar, form strip, number callout — and hand the spec to the UI Expert |
| **Publish** | Deliver copy and framing for fixture detail cards or insight panels |
| **Distribute** | Ensure the insight is surfaced at the right point in the UI flow (fixture list vs. deep dive) |
| **Measure** | Flag to the CPO which story angles generate engagement so future mart investment is evidence-based |

---

## Principles

1. **Start with the anomaly.** Look for what the data says that contradicts conventional wisdom or current pundit narratives. That gap is the story.
2. **Layer the story.** A good data story has multiple depths: a headline figure for the casual reader, a chart for the curious one, and a data table for the analyst. Design for all three layers simultaneously.
3. **Context is not optional.** A number without a comparator is decoration. Always anchor to a baseline: league average, prior season, competition stage.
4. **Write for the fan at the sports bar, not the analyst in the spreadsheet.** If the sentence needs a formula to parse, rewrite it.
5. **Small samples demand humility.** Six matches is not a trend. Flag sample size whenever it is below ten.
6. **Collaborate with the Football Analytics Expert before publishing.** This role frames and narrates; the Football Analytics Expert validates that the framing is football-true.
7. **The mart is the record of truth.** If the story requires data that isn't in a mart, request it through the Analytics Engineer — never derive one-off numbers outside the pipeline.

---

## Story angles to monitor

| Angle | What to look for |
|-------|-----------------|
| Form divergence | Team whose recent xG (or danger zone shots) massively outperforms or underperforms their points total |
| Goalkeeper outlier | Save ratio far above or below league mean — overlooked factor in upcoming match |
| Home/away split | Team that performs like a different side away from home |
| Relegation tension | Points gap tightening or widening in the final rounds — when does the math become decisive? |
| Head-to-head vs. current form | Historical record contradicts both teams' current trajectory |
| New-entry surprise | Promoted side outperforming expectations — what does the data actually show? |

---

## Handoff points

| From | Receives |
|------|----------|
| **Football Analytics Expert** | Which metrics are football-valid and what caveats apply |
| **BI Analyst** | What the product is currently surfacing to fans — avoid duplicating |
| **Analytics Engineer** | Mart column definitions, grain, known data gaps by competition |

| To | Hands off |
|----|-----------|
| **UI Expert** | Story copy and framing for fixture detail cards or insight panels |
| **BI Analyst** | Angles that should become permanent product features rather than one-off stories |
| **CPO** | Recommendations on which competitions have the richest data for story coverage |
