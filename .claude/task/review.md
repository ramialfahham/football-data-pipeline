# Review — fix/team-cleaning-and-generated-metrics — team side cleaned in base, forfeits by the rule, team metric SQL generated from the catalogue

diff_sha256: 05ac9f2436ab2df40d47990a88dc715855dcd234ee49481ff67b00a1a5cb03db

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 finding 1 (readings written into decisions_taken without CPO authority): the amendment now quotes the CPO's dated delegation and lists the readings it covers (own-goal correction of the box split, shots held to the open-play goals, possession outside the blank rule, the 20% limit and its 20-line floor).
- Round 1 finding 2 (forfeit goals out of contribution_player_pct with no doc sync): the amendment quotes the issue's What exactly line 2 verbatim; the catalogue description and the team_goals_season doc block now say the goals the club scored on the pitch.
- decisions_reserved line 2 against the catalogue edits: a dated CPO quote scopes the supersession to the description column; the diff changes no id, label, formula, format, direction or tier.
- New mechanisms and cost: the generated pass accuracy on mart_team_fixture_stats keeps the shipped value and is pinned by the formula test; no new service, hook, library, workflow step or cadence.
- Doc-sync, impact map, secrets and escalations.log: the mart header and shared.yml no longer claim a pure projection; nothing widens the impact map; no credential-shaped string; no new log entry.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 finding (hand-written pass accuracy in mart_team_fixture_stats): resolved; the generated block in match_rates is a registered Surface, the formula test checks the column against the fact at match level, a 0-100 range test is added, and the mart's descriptions are corrected.
- The edited formula test's Jinja: the CTE chain and the union are well formed; the final comparison uses is distinct from, so a NULL on either side is caught.
- Same-window rule on the new surface: a constant false awarded flag over a one-row window; the join on the unique grain adds no fan-out.
- The opponent-line watermark term reads a valid alias and only widens the re-merge trigger.
- Catalogue governance and layer placement: description column only; a generated formula in a mart is not a forked definition; no competition identifier added. Header and yml cuts remove restatements only; no test deleted or weakened.

## cto-reviewer
VERDICT: PASS
risks_checked:
- New mechanism: the mart surface is one more Surface line in the existing marker-block generator; the tests use dbt_utils.expression_is_true and the existing pytest module.
- Authority: the generated mart value implements decisions_taken; the description rewrite and the contribution wording rest on dated CPO quotes in the amendments.
- Guard invariants, dependencies and secrets: no guard path, package file, credential or workflow permission in the delta.
- Cost tripwire: no schedule or run change; the mart window and the wider watermark are marginal and fall under the declared condition that the measured nightly bytes go to the CPO before the merge.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 advisory (a): FORFEIT_COUNTED is now pinned to its literal tuple; widening it fails the test.
- Round 1 advisory (b): the watermark takes the opponent line's fetch from the deduplicated delivered CTE; greatest() only moves up, so the re-merge settles and is safe to re-run.
- Round 1 advisory (c): sqlfluff is builder-reported (dbt templater, 23 changed models, exit 0); not re-run by the reviewer.
- New surface: no duplicate is_awarded_result column; a window, not a group by, so the one-to-one join keeps row counts; the export reads the same column name and type.
- Test coverage: the pytest drift check loops over every Surface; the singular test's match-level check is well formed and outside the member floor; the range test is severity error.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- CPO authority: the dated description ruling and the verbatim forfeit line are quoted in the contract; round 1 point on unquoted wording closed.
- Round 1 findings on corners, saves, shots inside the box, cards, the per-match averages and saves_pct: the stale caveats are gone and no remaining description contradicts the unchanged formulas.
- finishing_efficiency_pct "In [0, 1]": true on cleaned data, since base raises shots on target to the open-play goals and blanks beyond a gap of 2.
- deserved_points and deserved_points_gap "played matches", and contribution_player_pct "on the pitch": each matches the SQL that computes it.
- Direction, composites and football validity: no id, label, format, formula, tier or direction changed; no composite added; mart pass accuracy equals the catalogue formula over one team-match.

## escalations
(none)
