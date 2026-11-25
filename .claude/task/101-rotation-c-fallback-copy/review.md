# Review — claude/101-rotation-c — 2026-11-25

diff_sha256: f279671898f3dd3fad6834c651fc2279a262c26316773debb00567290c63bcac

rounds: 1

## bi-analyst-reviewer
VERDICT: PASS
findings:
- [nit] verification-gap: acceptance_evidence.md, strings.ts:662, 667, 1114, 1119 — the longer DE and FI fallback intros were not measured at 280-375px; the Explainer is plain paragraph text with no new markup or CSS, so the risk is low.
- [nit] comment-placement: strings.ts:190-206 — the approved-copy comment blocks above the intros now sit next to the new fallback keys and do not say whether they cover them; cosmetic.
risks_checked:
- i18n parity: both fallback keys exist in EN, DE and FI, each with one {season} and one {leagues}; t() replaces every param, so none is left raw.
- Branch on fallbackSeason in TopPlayers.astro and TopTeams.astro is a truthy ternary; with the prop absent or empty the original call runs unchanged, so the in-season text is byte-identical.
- Nothing is computed on the frontend: the season is a served string passed through; the league list is built as before, so its order is the same in both variants.
- Types and spec: fallback_season is optional on Landing, passed to both components, both keys listed in index.spec.json; no other readers of the intro keys.
- fallback_season is in no sample file and not yet emitted by the export; the branch stays dormant until part B, so nothing is fabricated.
- Rendered evidence in acceptance_evidence.md read as text evidence for EN, DE and FI; in-season text unchanged.
