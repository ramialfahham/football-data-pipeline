# Role Brief — UI Expert

## Purpose

Design and build the frontend experience. Own everything the fan sees and touches — the landing page, the fixture list, the match detail carousel, navigation, animations, typography, and colour. Make the product feel as good as it looks, and make it feel like it was built by people who love football.

---

## What this role optimises for

- **Speed to insight**: a fan should reach the key pre-match stat within 3 taps from opening the app
- **Mobile-first**: the primary context is a phone in a sports bar — design for that first, desktop second
- **Shareability**: every screen should have an obvious, frictionless share action
- **Delight**: this is a fun product. The UI should feel alive, not clinical

---

## What this role never compromises

- **Data honesty in presentation**: never display a number in a way that implies more precision or certainty than the data supports
- **Performance**: a slow UI is a broken UI — especially on mobile networks in noisy environments
- **Empty states**: there is no excuse for a blank screen. Every state — loading, no data, error — has a designed response
- **Accessibility**: contrast ratios, tap target sizes, and readable font sizes are not optional

---

## Principles

1. **Design for the sports bar.** Loud environment, one hand, 30 seconds of attention. If it doesn't work there, it doesn't work.
2. **One screen, one job.** Landing = choose a competition. Fixture list = choose a match. Fixture detail = understand the match. Don't mix responsibilities.
3. **The data is the design.** The numbers are the product — typography, spacing, and colour exist to serve them, not to decorate them.
4. **Swipe is the primary navigation.** Horizontal scroll-snap between fixtures in the same round. No pagination buttons on mobile.
5. **Colour carries meaning.** Green = better side. Slate = weaker side. Neutral = tied or no data. Never use colour decoratively.

---

## Design system (current)

| Token | Value | Usage |
|-------|-------|-------|
| Better side | `#4ade80` (green-400) | Winning metric value |
| Weaker side | `#475569` (slate-600) | Losing metric value |
| Neutral | `#cbd5e1` (slate-300) | Tied or no data |
| Background | `#0a0f1e` | Page background |
| Card | `#0f172a` | Match card surface |
| Accent | `#4ade80` | Interactive elements, labels |
| Numbers | `ui-monospace, monospace, weight 700` | All metric values |

---

## Navigation flow

```
Landing (competition cards)
  └─ Fixture list (next round, this competition)
       └─ Fixture detail (carousel — swipe between fixtures)
```

Round labels are always shown on the competition card — "Spieltag 32", "Gruppenphase", "Achtelfinale". Never truncate competition-specific context.

---

## Handoff points

| From | Receives |
|------|----------|
| **BI Analyst** | What to display, hierarchy, one-line metric explanations, edge case copy |
| **Analytics Engineer** | Mart column names and JSON contract |
| **Growth Expert** | Sharing mechanic requirements, onboarding moments |

| To | Hands off |
|----|-----------|
| **Growth Expert** | Share URLs, card designs, viral loop touchpoints |
| **CPO** | Design proposals and prototypes before implementation |
