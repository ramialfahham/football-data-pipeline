# Review — feat/41-top-teams-block — 2026-09-10

diff_sha256: d9725221fbfe534541b62e918d32078cec0fac7610614d44fb03c9cd8a0b1e4b

rounds: 5

rounds_cap_override: The CPO said "OK, open the PR" after being shown the measured round-by-round
cost below and asked directly whether to run another round — his instruction to proceed to the MR,
given at round 3. ⚠ RECORDED PRECISELY, because it would be easy to overclaim here: he authorised
SHIPPING, and rounds 4 and 5 then happened anyway because the commit gate refuses a standing FAIL
verdict and the only alternative was to write a PASS the reviewers had not given. So the cap was
exceeded by taking the MORE conservative path inside his instruction, not by looping on an
unresolved disagreement — and it was worth it: round 4 caught a real defect (the evidence file
quoting superseded copy, and the block's own intro never evidenced from built output) that shipping
on the round-3 verdicts would have carried into the MR. **There are no open findings.** All four
reviewers PASS at the hash above.

Round 1: `analytics-engineer-reviewer` FAIL, `scope-auditor` FAIL, `bi-analyst-reviewer` FAIL,
`platform-reviewer` did not complete (the session crashed mid-round).
Round 2: `analytics-engineer-reviewer` PASS; `platform-reviewer` FAIL; `scope-auditor` FAIL;
`bi-analyst-reviewer` FAIL.
Round 3: `analytics-engineer-reviewer` PASS, `platform-reviewer` PASS; `scope-auditor` FAIL,
`bi-analyst-reviewer` FAIL.
Round 4 (governance reviewers only — no code had changed since round 3's two PASSes):
`scope-auditor` PASS; `bi-analyst-reviewer` FAIL.
Round 5 (`bi-analyst-reviewer` only, the last FAIL standing): PASS.

**All four reviewers PASS at the hash above.** The rounds exceeded the cap of 3; rounds 4 and 5
were each narrowed to the reviewers whose findings were outstanding rather than re-run in full.

⚠ THE PLAN AFTER ROUND 3 WAS TO SHIP WITHOUT A ROUND 4, and it did not survive contact with the
gates. Shown the cost breakdown below, the CPO said "OK, open the PR" — but the commit gate refuses
a standing FAIL verdict, and the honest options were to run the round or to write a PASS the
reviewers had not given. Recorded because the gate was right and the shortcut was mine: round 4
found a real defect (superseded copy quoted in the evidence file, and the block's own intro
sentence never evidenced from built output at all), which shipping on the round-3 verdicts would
have carried into the MR. The cap is a prompt to stop and ask, not a budget to spend down.

## What the rounds actually cost, measured

| round | code defects found | prose / evidence defects found |
|---|---|---|
| 1 | **2** — `boardTitle()` classifying a metric from its id string; unapproved §10 copy live on the built page | 1 |
| 2 | **0** | 3 |
| 3 | **0** | 2 (+2 more found by sweeping, not by a reviewer) |
| 4 | **0** | 1 — and a load-bearing one: the evidence file quoted SUPERSEDED intro copy and never quoted the block's own intro at all (+2 more found by sweeping) |
| 5 | **0** | 0 |

Round 1 earned its price: the `boardTitle()` defect would have shipped, and it was unsound as well
as misplaced. Rounds 2 and 3 found nothing wrong with the code.

**The cause is the diff's own comment volume.** These files carry 10-20 line comment blocks
narrating decision history, so every correction creates fresh stale surface in the prose AROUND it
and manufactures the next round's findings. `strings.ts`'s comment above `homeTopTeamsIntro` was
twelve lines justifying a string; when the CPO re-ruled the string, that one block became four
separate false claims. The reviewers were right each time — the comment genuinely told the next
reader the opposite of the truth — but this is the failure mode
`feedback_review_cost_discipline` already names: paying full adversarial-review price for prose.
The CPO has said the pattern itself is the next conversation.

## scope-auditor
VERDICT: PASS (round 4)
risks_checked:
- Round 1 FAIL — `contract.md` cited "authority: the CPO, in this session" for the competition-name
  scope amendment with no corresponding entry in `escalations.log`, the only file the working
  agreement treats as verifiable authority. It grepped for four distinct phrasings and got zero
  hits. Recorded as the fourth instance of that failure class. FIXED: the ruling is now logged
  under `2026-09-10 feat/41-top-teams-block` with the CPO's words verbatim.
- Round 2 FAIL — the intro's window phrase ("Current season.") was MY proposal, self-labelled
  "shipped pending his confirmation" in three artifacts, and live in the built HTML. A §10
  user-visible wording decision taken by the agent. It also noted the string was absent from
  `decisions_reserved`, so nothing routed it back. CLOSED by the CPO approving it — but closed by
  luck, and the reviewer's rule stands: an unapproved §10 string waits in `decisions_reserved` and
  stays out of the build.
- Round 3 FAIL — the MIRROR IMAGE: `10_home.md:450` and the `strings.ts` comment still said the
  copy was unapproved and "shipped pending his confirmation" after he had approved it, so the two
  documents a future reader trusts on copy status both understated a settled approval. Fixed.
- Round 4 PASS — its first on this branch. Checked two things specifically rather than on trust:
  that the `acceptance_criteria` list going from 10 bullets to 9 dropped no real criterion (the
  removed item was a note formatted as a bullet, which the acceptance gate had counted as an
  unevidenced criterion), and that `review.md` itself recorded the outstanding verdicts honestly
  rather than claiming a PASS the reviewers had not given.
- Verified across all three rounds: every changed file inside `scope_paths`; every user-visible
  copy string traceable to a quoted ruling; no new mechanism, dependency or recurring cost beyond
  the one declared query; credential sweep clean.

## analytics-engineer-reviewer
VERDICT: PASS (round 3)
risks_checked:
- Round 1 FAIL — `boardTitle()` read `metricId.endsWith("_per_match")` to decide whether to expand
  the `Ø` sigil. A taxonomy judgement made in the frontend, which `layering.md` §Consumption layer
  puts in the warehouse; its own test applies, since a second frontend would have to re-implement
  the regex to render the same heading. ⭐ It was also UNSOUND, which is the worse half and which
  the review did not have to point out for it to be true: an id's spelling is not a fact about the
  metric, and this catalogue proves it — `shots_on_goal_per_match` carries the label key
  `metrics.shots_on_target_per_match.label`, the same id/name disagreement `metrics_display.md`
  records causing a defect in #370. I had cited that mismatch as a reason to READ the label key,
  then built a guard on the naming I had just called unreliable.
- Rounds 2 and 3 PASS — verified the branch on its own terms rather than from the write-up: read
  the four catalogue rows to confirm `test_the_team_board_set_is_all_per_match_rates` is not
  vacuous (all four are `denominator_expr = count(*)`); confirmed no `endsWith` logic survives in
  shipped code; traced `_warehouse_competition_meta`'s overlay and confirmed the slug still comes
  from the registry only; confirmed `shape_home_top_teams` contains no sort or comparator and the
  ordering is the served `board_leader_order`; confirmed `mart_competition_index.sql` and
  `mart_team_leaderboards.sql` are untouched and publish every column the export reads.

## platform-reviewer
VERDICT: PASS (round 3)
risks_checked:
- Round 1 did not complete — the session crashed mid-round. Re-run from scratch in round 2.
- Round 2 FAIL, two findings, both correct and both prose: (1) `shape_home_top_teams`'s own
  docstring still said "NO SLUG AND NO LINK on a row" seven lines above the code that sets the
  slug, while `TopTeams.astro` wrapped every row in an anchor — the correction had been swept
  through the component, the tests and the contract and missed in the docstring of the function
  that emits the thing; (2) `contract.md`'s `THRESHOLD — RECURRING COST` claimed "No new pages are
  built, so the site build does not grow at all" while `blast_radius` in the same file said "team
  pages go 3 -> 60". Both fixed, and the same false "no new page" clause was corrected in the
  MECHANISM threshold in the same pass rather than only the sentence quoted.
- Round 3 PASS — re-read both and confirmed fixed. Independently re-derived the mutation claim from
  `metric_catalogue.csv` (`duels_per_match` = `count(*)` vs `duels_won_pct` = `sum(duels_total)`)
  rather than taking the write-up's word. Also checked the `_competitions_index` signature change
  for a silent positional-argument shift across all three call sites: none passes `registry_path`
  positionally, and the pre-existing offline test still exercises the `client=None` path.

## bi-analyst-reviewer
VERDICT: PASS (round 5)
risks_checked:
- Round 1 FAIL — the Top teams intro shipped the CPO's DRAFT, which `10_home.md` marks "Proposed,
  NOT yet approved (copy is always his call)", onto the built page. The contract disclosed the gap
  in prose while the code shipped the string anyway. Copy is §10; disclosure is not approval.
  CLOSED: the CPO has since ruled the sentence, and both home blocks now carry his words.
- Round 2 FAIL — same class on the remaining clause, found independently of `scope-auditor`.
  ⭐ IT ALSO RAISED A FINDING ABOUT MY METHOD, AND IT WAS RIGHT: `escalations.log` and
  `10_home.md` CHANGED CONTENT UNDER ITS READS mid-review, because I was logging the CPO's rulings
  while its round was in flight (and `10_home.md` appeared to REVERT — that was the stash-dance,
  which stashes `docs` while `contract.md` is amended, so the file really did vanish and return).
  It refused to treat text it had not seen at the start as authority. That is the correct instinct:
  a reviewer that accepts a record shifting beneath it can be walked to any verdict. THE LESSON IS
  TIMING, NOT STRUCTURE — rulings still get logged the moment they land, but the ROUND waits.
  Round 3 ran on a frozen tree and reported no such churn.
- Round 3 FAIL — the two stale approval-status passages, same as `scope-auditor`, found
  independently. Confirmed in the same pass that the shipped VALUES match the rulings word-for-word
  in all three locales; only the surrounding commentary was wrong.
- ⭐ Round 4 FAIL — THE MOST VALUABLE FINDING OF THE FIVE ROUNDS AFTER ROUND 1, and the one that
  justifies having run a round the plan had written off. `rendered_page_evidence.md` §3b quoted the
  intro copy as it stood BEFORE the CPO's 2026-09-10 ruling — captured after the competition-name
  fix, never re-captured after the copy changed — and `homeTopTeamsIntro`, this MR's actual
  deliverable and the string that FAILed rounds 1 and 2, was not quoted anywhere in the file. So
  the acceptance criterion "the intro sentence names exactly the leagues that appear on the boards"
  had no built-page evidence behind it for the Top teams block at all, and the file's own banner
  ("EVERY NUMBER HERE WAS RE-DERIVED") was false for precisely the most contested string on the
  branch. FIXED: §3b now quotes BOTH blocks in ALL THREE locales, complete sentences, read from
  `dist/{lang}/index.html`. The banner is replaced by a rule that cannot rot the same way —
  re-capture on every build this file quotes, with each quote naming the artefact it came from.
  ⚠ A sweep afterwards found TWO MORE of the same class the reviewer had not named: the DE and FI
  comments each cited the superseded players line as the shape they mirror.
- Round 5 PASS — verified §3b against `dist/{en,de,fi}/index.html` DIRECTLY rather than against
  `strings.ts`, which is the only way to check a claim about built output; swept the whole
  "superseded copy quoted as current" class across the source, the wireframes and the spec and
  confirmed every remaining hit is a diff removal or labelled historical narration; and
  corroborated the anchor counts from the built HTML (56 `.brow` rows = 28 player + 28 team).
- Verified across rounds: every field `TopTeams.astro` renders traced to a served mart column, none
  fabricated; the 20-id `.gitignore` allowlist matched one-for-one against the team ids actually
  referenced in the committed `landing.json`; board order and the locked board set against
  `10_home.md`; the heading rule against `metrics_display.md`; `landing.json`'s BL1 row showing
  `Bundesliga` rather than `1. Fußball-Bundesliga`.

## What the reviewers did NOT find, and the sweep did

Both round-3 reviewers named two stale locations. Re-grepping every changed file for the whole
class — not the two locations — found **two more of the same defect**:

- `strings.ts:195` still said "APPROVED WORDING, 2026-08-18" after the CPO re-ruled that string on
  2026-09-10.
- `10_home.md:468` still said the Top players line "still reads 'Season totals to date'" after it
  had been changed.

Recorded because it is the standing correction the repo has logged nine times and that prose has
never fixed: sweep the CLASS, not the instance the reviewer happened to name.

## escalations

Four CPO rulings landed during this branch and are all in `.claude/task/escalations.log`:

- `2026-09-09 feat/41-top-teams-block` — the standardised competition names must reach the frontend;
  the export was reading `docs/competition_registry.yml`, which is INPUT. 37 names identical,
  11 different.
- `2026-09-10 feat/41-top-teams-block` RULING 1 — "Season to date" rejected; the window phrase must
  hold during AND after a season.
- RULING 2 — the Top teams intro's second half, dictated verbatim in all three locales.
- RULING 3 — the window phrase, proposed by me and approved by him.
- RULING 4 — the Top players intro re-ruled, at his own instigation, superseding the 2026-08-18
  approval.

⛔ One FUTURE BLOCKER recorded and deliberately NOT fixed: DE `Der Top-Spieler` is grammatically
masculine and blocks a women's competition (CPO: "If we ever include women's football teams we have
to change it properly (at least in German)"). Scoped to that one string — `Die Top-Mannschaft` is
unaffected, and EN/FI have no grammatical gender. No women's competition exists in
`docs/competition_registry.yml`, so choosing a form for a case that does not exist would be
authoring §10 copy nobody has ruled on. Flagged in `strings.ts` at the string itself.
