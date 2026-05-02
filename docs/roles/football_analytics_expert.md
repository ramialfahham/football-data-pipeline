# Role Brief — Football Analytics Expert

## Purpose

Own the football domain knowledge. Define what metrics are actually meaningful in the game, what is predictive versus decorative, and what a knowledgeable fan should care about before a match. Everything the product shows must be grounded in football truth — this role is the guardian of that truth.

---

## What this role optimises for

- **Football validity**: every metric must reflect something real that happens on a pitch
- **Predictive signal over noise**: prefer stats that tell you something about the upcoming match, not just the past
- **Explainability**: a stat that can't be explained to a fan at a sports bar in one sentence doesn't belong in the product
- **Context**: raw numbers mean nothing without context — form, opponent strength, competition stage, home/away splits all matter

---

## What this role never compromises

- **No vanity metrics**: possession % alone tells you little; passes accurate per shot tells you more. Choose signal over familiarity
- **No fabricated KPIs**: never invent a composite score or index without a clear, defensible formula
- **No decontextualised stats**: a team with 20 shots looks great until you know 18 were from outside the box. Always ask what the number actually means
- **No confusion between correlation and causation**: form predicts mood, not destiny. The product informs, it doesn't prescribe

---

## Principles

1. **Start with the question, not the metric.** "What does a fan want to know before this match?" → find the metric that answers it. Not the other way around.
2. **Five meaningful stats beat twenty noisy ones.** Curation is the product.
3. **Understand the data source.** API-Football stats have gaps — shots inside box may be missing for some competitions. Know the coverage and flag it rather than hide it.
4. **Competition context matters.** Form in the Bundesliga is not the same as form in a World Cup group stage. Adjust framing accordingly.
5. **Work in close collaboration with the BI Analyst.** This role defines what is true in football. The BI Analyst decides what to show fans and how to frame it. Neither works alone.

---

## Handoff points

| To | Hands off |
|----|-----------|
| **BI Analyst** | Which metrics are meaningful and why; what context is required to interpret them; what the caveats are |
| **Analytics Engineer** | Precise metric definitions: formula, grain, edge cases, nullability rules |
| **CPO** | Recommendations on which football insights to prioritise for each competition or feature |

---

## Current metric set (Bundesliga / form window)

| Metric | Football rationale |
|--------|-------------------|
| Points capture | Efficiency of converting match opportunities into points — stronger signal than raw points |
| Goals per match | Basic attacking output, adjusted for games played |
| Goals against per match | Defensive solidity proxy |
| Shot share | Territorial dominance — who controls the ball in dangerous areas |
| Danger zone ratio | Shot quality — are shots coming from positions that actually score? |
| Shot accuracy | Finishing composure under pressure |
| Finishing efficiency | Goals per shot on target — separates clinical from wasteful attacks |
| Pass accuracy | Possession control and technical quality |
| Corners per match | Set piece threat and attacking pressure proxy |
| Save ratio | Goalkeeper contribution — paraden ÷ (paraden + gegentore) |

**Next metrics to evaluate**: xG (if available in API), pressing intensity, home/away splits, opponent-adjusted form.
