# Task contract — MR5 of the description-drift programme

objective: >
  Build `scripts/check_description_hygiene.py` — the machine check that makes the description
  standard stick — with tests, and wire it into the three places that run the fast gates. It fails
  on any `description:` under `dbt_project/` that carries an issue ref, an ISO date, decision
  language, a severity emoji, a downstream-consumer claim, or a rendered length past BigQuery's
  own maximum — 1,024 for a column description, 16,384 for a model or seed. See amendment 3: that
  limit started as a flat 600 and the CPO ruled it to BigQuery's maxima.

  The point of the whole programme is that prose rules do not hold in this repo: of 50 past
  corrections, 33 were prose-only and 22 recurred, while every rule that got a machine check
  stopped recurring. MR1-MR4 wrote and applied the standard; this is the part that keeps it.

refs: >
  Authority: `.claude/task/escalations.log` — the 2026-08-20 programme entry (diagnosis, the
  definition of a good description, the six-MR split), MR3's and MR4's entries (the method), and
  THIS branch's entry, which records the CPO's protected-path approval. Plan file:
  `C:\Users\Rami\.claude\plans\jazzy-greeting-teacup.md`, Step 4.
  Standard: `dbt_project/docs/engineering_standards.md` §2. Model the script on
  `scripts/check_copy_gate.py`. MR4 merged as `!86`; branched from main `dc6d7eb`, no open MRs.

protected_override: >
  CPO, in chat 2026-08-20, verbatim "do both", recorded in `.claude/task/escalations.log` under
  `2026-08-20 feat/description-hygiene-gate` BEFORE this branch touched either file — GitLab #28 is
  that an override can otherwise claim a ruling nobody can check.

  It authorises exactly two edits, and nothing else:
    1. `.gitlab-ci.yml` — one line added to `validate:governance`'s script list.
    2. `.claude/hooks/stop_gate.py` — one entry added to `FAST_GATES`.
  No other change to either file, and no other protected path. `.claude/skills/validate-local/`
  is NOT protected but must move in lockstep, because
  `test_fast_gates_and_validate_local_agree` asserts set equality between its marked block and the
  hook's tuple.

impact_map: >
  A NEW GUARD, so the blast radius is "what can now fail that could not before", in three places.

  1. TURN END. `stop_gate.py` runs the fast gates when the tree is dirty and in scope, and blocks
     the turn once if any fails. Adding a gate there means a description defect ends a turn red.
     The gate must therefore be FAST and must not need network, a fetched base branch, or BigQuery
     — it parses YAML off disk, like its five siblings.
  2. CI. `validate:governance` gains one line, so a defect fails the pipeline. No `changes:` filter
     on that job, so it runs on every MR.
  3. LOCAL. `validate-local` documents the same set; the pinning test fails if the two disagree.

  ⚠ GREEN ON DAY ONE IS THE WHOLE REASON THIS MR IS FIFTH. MR3 and MR4 cleared all 453 descriptions
  in the five worst files. The remaining 14 files were measured healthy by the audit, but "healthy"
  was that audit's judgement, not this gate's rule — so the gate MUST be run against the whole
  repo before wiring, and any survivor fixed or the rule narrowed with a stated reason. A gate that
  goes red on main on day one is the `check_copy_gate.py` precedent inverted.

  ⚠ THE RULE MUST NOT FIRE ON ORDINARY PROSE, and this is measured, not hypothetical. On the
  finished MR3/MR4 text, a case-insensitive `CORRECTED` matches six legitimate uses of "the country
  corrections from the seed" and "derived from the corrected name"; an ISO-date rule would have
  matched `dim_date`'s calendar range before MR4 reworded it. Match the ANNOTATION forms, not the
  plain verb. Every banned pattern needs a reason recorded beside it, as `check_copy_gate.py` does.

  No dbt model, seed, mart, export or site file is touched, so the warehouse and the built site are
  untouched. `PyYAML` is already a dependency; no new dependency enters.

scope_paths:
  - scripts/check_description_hygiene.py
  - tests/test_description_hygiene.py
  - .gitlab-ci.yml
  - .claude/hooks/stop_gate.py
  - .claude/skills/validate-local/SKILL.md
  # Added by amendment 3 — the length rule it documents is being split.
  - dbt_project/docs/engineering_standards.md
  # Added by amendment 1 — the ten files the first full-repo sweep found dirty.
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/int_player_season__team.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

decisions_taken: >
  CPO, 2026-08-20, approving "the whole plan" — all six MRs, with MR5 as the gate.
  CPO, 2026-08-20, "do both" — the gate runs in CI AND at turn end. See `protected_override`.

decisions_reserved:
  - `persist_docs` and `dbt docs generate` are MR6. Not touched here.
  - ⚠ THIS BULLET WAS WRONG AS FIRST WRITTEN, and scope-auditor FAILed the branch on it. It said
    fixing a survivor was "in scope only as far as making the gate green". That is not the rule I
    followed and not the rule that is right: where the sweep touches a description, it applies §2
    IN FULL, not the gate's mechanical subset.
    WHY, because the distinction is the whole point of trap 1b: the gate's rules are deliberately
    narrower than §2 — they only match what a machine can decide with no taste. `mart_team_season
    composes` and `ratios live in mart_team_season_record` are §2-banned downstream-consumer
    claims that no regex here catches. A minimal token-deletion would have left them standing in a
    description it had just edited, which is the half-cleaned outcome this programme exists to
    remove, and would have left those ten files inconsistent with the five MR3/MR4 rewrote.
    ⚠ ONE OF THE THREE FLAGGED CHANGES WAS NOT §2-DRIVEN and is restored: dropping "Complement to
    int_team_momentum__metrics" from `int_team_season_record` was a sibling cross-reference, not a
    downstream claim, and losing it cost something for nothing.
    analytics-engineer-reviewer checked all ten files against their SQL and found no false claim,
    so the rewrites are sound; the defect was this bullet describing them wrongly.
  - The gate's rule set is mine to draft and the reviewers' to challenge. Any rule that would
    require a CPO judgement — banning something he has asked for — is escalated, not assumed.

done_when:
  - `scripts/check_description_hygiene.py` matches its six siblings: `main() -> int`, 0/1, no CLI
    args, findings accumulated then printed with a count, a census line on success.
  - It carries an anti-vacuous floor, as `check_copy_gate.py` does: if it finds implausibly few
    descriptions it fails loudly rather than passing green on a broken parser.
  - `tests/test_description_hygiene.py` drives `main()` against a synthetic offender for EVERY
    banned class and asserts exit 1, and proves the floor fires from inside the gate.
  - THE GATE IS SEEN RED. Break it deliberately, watch it fail, restore. A passing gate proves
    nothing (#904) — this is the repo's dominant failure and the acceptance evidence must show it.
  - Run against the WHOLE repo before wiring: zero findings on main's current content.
  - Wired in all three places, and `test_fast_gates_and_validate_local_agree` passes.
  - `python -m pytest tests/` green at the 829/1 baseline plus the new tests.
  - The five existing fast gates still pass, read from their OUTPUT not their exit code.
  - Handover updated in the SAME commit as the code.

amendments:
  - >
    1. TEN MORE FILES ADDED TO scope_paths, because the first full-repo sweep measured the gate
    red on main. 35 findings across 10 files that MR3 and MR4 never touched: 14 issue refs, 9
    over-length, 6 ISO dates, 4 decision-language, 1 severity emoji, 1 downstream-consumer claim.
    The plan assumed MR3+MR4 would leave the repo green; that assumption was wrong for a reason
    worth recording — the audit judged those 14 files "healthy" against its own reading, and this
    gate's rule is stricter than that judgement. So the audit's 83%-in-5-files figure is right
    about where the WORST text is and wrong as a completeness claim.
    Fixing them is the `check_copy_gate.py` precedent applied literally: clear the findings, THEN
    wire, so the default branch never goes red. It is not new editorial scope — the same six
    mechanical classes MR3 and MR4 removed, in the files that were out of their reach.
    ⚠ This makes MR5 two things in one MR: the last of the content sweep, and the gate. If a
    reviewer judges that unreviewable, the content half splits out and the gate follows it.
  - >
    3. THE LENGTH RULE BECOMES BIGQUERY'S OWN MAXIMA — 1,024 for a COLUMN description, 16,384 for
    a MODEL or SEED — measured on the RENDERED text, with `engineering_standards.md` joining
    scope_paths to say so.
    CPO-DIRECTED, in two steps. He challenged the flat 600 ("if 1024 is max why do we max at
    600?") and supplied BigQuery's limits: 16,384 table, 1,024 column, 300 column name. I then
    proposed 600 for columns and an EDITORIAL 1,024 for models, and he rejected that framing:
    *"we use bigqueries max which doesn't necessarily mean that we are exhausting it. it's just you
    who has a tendency tom massively bullshit and spam with text."*
    THE RULING, AND WHY IT IS RIGHT: the cap's only job is stopping `persist_docs` failing the
    build. A tighter number does not make me write less — it makes me shave words while still
    writing padding, which is what MR3 and MR4 actually cost. Brevity is a judgement and mine to
    exercise, not something to fake with a threshold. Using the maximum is not a licence to fill it.
    ⚠ THIS AMENDMENT DESCRIBED THE SUPERSEDED PROPOSAL UNTIL scope-auditor CAUGHT IT. It said
    "columns 600, models and seeds 1,024" and argued for 1,024-rather-than-16,384 as a deliberate
    editorial narrowing — a protection that was never built, while the shipped code and standard
    used the raw maxima. `objective:` still said a flat 600 as well: three numbers across three
    artifacts for one decision. Exactly the stale-claim class of GitLab #71, committed inside the
    MR that ships the gate against it.
  - >
    2. ONE RULE WIDENED DURING THE SWEEP, recorded because it changes what the gate catches.
    `stg_apif__lineups` claims "This model has NO consumer today" — the exact shape of the
    `display_group` claim that started this programme, and the first draft's
    `no dbt model reads` arm did not match it. The downstream rule is now written as a CLASS
    (no/zero/only/single reader-or-consumer, nothing downstream, feeds/enriches/powers a named
    model) rather than a list of the instances seen so far.
