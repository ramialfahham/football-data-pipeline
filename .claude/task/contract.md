# Task contract — data:build:mr must not bootstrap-ingest (#73)

objective: >
  Remove the bootstrap-ingest step from `data:build:mr`. It writes PRODUCTION raw from an
  unmerged branch (settings.py:31 defaults the dataset to `raw`; nothing overrides it in CI), it
  is redundant with the identical step already in `data:build:main`, and GitLab's protected-
  variable rule correctly refuses to give a feature branch the API key — which is what made MR
  !50 fail. Closes #33 item 13 for the MR path. Pin the removal with a test so the step cannot
  return silently.

  ⛔ SCOPE NARROWED BY THE CPO, 2026-08-16. An earlier revision of this branch ALSO tagged
  `assert_base_leagues_covers_active_competition_var` `prod_state` and excluded it from
  `data:build:mr`. All four routed reviewers FAILED that, and the CPO ruled it out in plain
  terms after asking whether the change was "a systematic fix or a hack": it was a hack. It is
  fully reverted here. The underlying cause — nothing records whether a league has been
  INGESTED, only that it SHOULD be — is filed as its own issue and is NOT addressed here.
refs: GitLab #73, #33 item 13, #72, !50

protected_override: >
  CPO approval 2026-08-16, in-thread, verbatim: **"yes, rewrite #73 to option 2 only and fix it"**,
  given after I laid out option 2 as "delete the bootstrap-ingest block from data:build:mr ...
  that's the professional, economic, secure answer". The same message rejected the unprotect-the-
  key option: **"it is 100% bullshit in terms of security."** `.gitlab-ci.yml` is a PROTECTED path
  (the file that decides what CI enforces), hence this override.

impact_map: >
  writers: `.gitlab-ci.yml` is not a data writer. The step being DELETED is the only thing in
    `data:build:mr` that writes raw tables — `python -m ingestion.api_football.main` with
    `API_FOOTBALL_LEAGUE_CODES` set. After this change `data:build:mr` writes ONLY `ci_*` datasets
    (via `dbt seed/build --target ci`) and reads prod via `--defer --favor-state`.

  what still ingests, and where: `data:build:main:597` runs the SAME
    `get_new_league_codes.py` + `python -m ingestion.api_football.main` sequence, BEFORE its
    `dbt build --selector staging/downstream --target prod` lines. `data:nightly` is the other
    prod writer. Neither is touched here, so a newly onboarded league is still ingested exactly
    once, post-merge, from a protected branch that legitimately holds the key. Verified by reading
    both job bodies in this file, not assumed.

  guards NOT touched, and the accepted consequence: NO dbt test is modified by this branch.
    Four singular tests — `assert_base_leagues` / `assert_base_teams` /
    `assert_base_fixtures_next` / `assert_fct_fixture` `_covers_active_competition_var` — assert
    "every code in `vars.active_competition_league_codes` has rows". All four are unconditional
    (`left join ... where null`); I read all eight `*_covers_active_competition_var` tests and the
    other four self-exclude via an `inner join base_apif__leagues` on a coverage flag. On an
    ONBOARDING MR those four now fail, because the var names the new league and this job no longer
    ingests it. That is ACCEPTED (CPO 2026-08-16): the tests are stating a true fact, and
    silencing them was rejected as a hack. Onboarding MRs show red here and are merged on
    judgement until the ingest-state issue lands.
    ⚠ REASONED FROM THE TEST BODIES, NOT OBSERVED (#904): `data:build:mr` on !50 died at the
    ingest step and never reached the dbt steps, so these four have not been SEEN failing for this
    reason. `dbt build` is never run locally (CLAUDE.md), so this branch's own pipeline is the
    first place it is exercised.

  layer_rules: `scripts/check_layer_contract.py` — untouched; no model, no layer, no
    materialisation changes. No new model, macro or SQL file. NO dbt file of any kind is in this
    diff.

  deploy_order: no warehouse migration. The CI change takes effect on the next pipeline. ⚠ Merge
    order matters for !50: this MR should merge FIRST, then !50 rebases onto it and its
    `data:build:mr` goes green. If !50 merged first instead, `data:build:main` would bootstrap
    BPL/TSL/EKS on main — also correct, just via the other path.

  blast_radius: no mart, no number, no row changes anywhere. One behaviour change:
    `data:build:mr` no longer ingests, so it no longer needs `API_FOOTBALL_API_KEY` and no longer
    runs a billed `SELECT DISTINCT league_code FROM RAW_APIF_FIXTURES_NEXT` per MR. No test's
    selection, severity or logic changes anywhere.

scope_paths:
  - .gitlab-ci.yml
  - tests/test_ci_data_job_invariants.py
  - .claude/task/escalations.log
  - .claude/active_work.md

decisions_taken: >
  CPO ruling 2026-08-16 (quoted in full under protected_override): fix via option 2 only, and the
  unprotect-the-key option is rejected on security grounds. The CPO also asked the framing
  question this task answers — *"Why do we always need to touch ingestion again and again?"* — and
  the answer encoded here is that we do NOT: no ingestion code changes, the fix is a CI job that
  should never have carried this step.

  NEW MECHANISM: none. Deleting a step, and adding an assertion to an EXISTING pytest module
  whose stated purpose is pinning exactly these CI invariants.

  RECURRING COST: strictly NEGATIVE (a saving). Removes one billed BigQuery `SELECT DISTINCT` per
  MR pipeline, plus the API-quota draw of any bootstrap ingest an unmerged branch would have run.
  Nothing is added.

  NO GUARD IS LOOSENED, because none is touched. The previous revision of this branch narrowed
  one and was FAILED by all four routed reviewers and then by the CPO. The standing rule held.

decisions_reserved:
  - Whether `data:build:mr` should ALSO be prevented from writing prod raw structurally (setting
    `API_FOOTBALL_BIGQUERY_DATASET` to a ci-scoped dataset) rather than only by removing the one
    step that did it. #33 item 13 is broader than the MR path; this task closes the MR path only
    and takes no position on the rest.
  - The ingest-state model itself (recording that a league HAS been ingested, not merely that it
    should be) is deliberately NOT designed here. It is the cause behind the four failing
    onboarding-MR tests AND behind `get_new_league_codes.py` having to rediscover that fact from
    BigQuery every run. Filed as its own issue per the CPO's instruction, "ship part 1 and file
    the state fix as its own issue".

done_when:
  - `data:build:mr` contains no `get_new_league_codes.py` call and no
    `python -m ingestion.api_football.main` invocation; `data:build:main` and `data:nightly` still
    do, unchanged.
  - The removal is explained in a `.gitlab-ci.yml` comment that names #73 and #33 item 13, so the
    step is not "restored as an oversight" later.
  - NO dbt file is modified: `git diff --stat` shows no path under `dbt_project/`.
  - A NEW test in `tests/test_ci_data_job_invariants.py` FAILS if `data:build:mr` ever invokes
    `ingestion.api_football.main` or `get_new_league_codes.py` again, and it is demonstrated RED
    first (per the standing rule that a passing test proves nothing until it has been seen fail).
  - `python -m pytest tests/test_ci_data_job_invariants.py` passes.
  - escalations.log records the #73 ruling and the rejected option.
  - MR opened against main; !50 rebases onto it afterwards.

amendments: (none)
