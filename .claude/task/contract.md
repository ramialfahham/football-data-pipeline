# Task contract — a Python linter, so reviewers stop finding what a machine finds free

> Branch `chore/add-python-linter` from `main` (`ddf8010`). TWO protected paths, so
> `protected_override` AND `impact_map` are present, and `.gitlab-ci.yml` carries the OPUS floor.
> `ingestion/**` is on the structural surface, which also requires the `impact_map`. No
> `site_v2/src/` path, so no `acceptance_criteria`.

objective: >
  Add `ruff` with a correctness-only ruleset, wire it into CI, and fix the 12 violations it
  reports, so mechanically-decidable defects stop consuming adversarial review rounds.

  ⚠ THE PROBLEM, CORRECTED IN ROUND 1 AFTER THIS FIELD GOT IT WRONG. It first read "This repo has
  NO linter and none pinned", from grepping `requirements*.txt` alone. FALSE: `.pre-commit-config.yaml`
  configures ruff `v0.7.4` over `ingestion|scripts|tests|dbt_project/macros|dbt_project/seeds`, and
  the hook is installed. What is actually true, and is a STRONGER argument: that hook is LOCAL-only
  with no CI backstop, it does not cover `.claude/hooks/` at all, and NINE F401s inside its own
  file pattern survived it (the tenth, `git_discipline.py:197`, was never in its jurisdiction) — a
  hook whose own args are `--fix, --exit-non-zero-on-fix`, so it evidently is not being run. On #25
  the same day, `platform-reviewer` at opus spent
  ~125k tokens finding a duplicate module-level function name — pyflakes F811, reported in
  milliseconds — and three of the four defects across #25's three rounds were mechanically
  decidable.

  THE ONE THAT SETTLES IT. `ruff` finds an unused `import subprocess` at
  `.claude/hooks/git_discipline.py:197` that **!19 introduced earlier the same day**, when the git
  call moved into `_staged_stat`. It survived three review rounds and two opus reviewers and is on
  `main` now.

  ⚠ THE PREMISE WAS WRONG ON DEFAULT SETTINGS, AND THE VERIFICATION IS WHAT CAUGHT IT. This
  contract first claimed F811 would have caught #25's duplicate `_review_patch`. Run before being
  believed, it does NOT: ruff exempts underscore-prefixed names via `dummy-variable-rgx`, so `f`
  and `review_patch` are flagged while `_f`, `_review_patch` and `__x` pass silently. Every test
  helper in this repo is underscore-prefixed by convention, so on defaults the linter would have
  been inert against the exact class that justified it — a guard that looks strong and is nearly
  inert, which is the failure `tests/test_materialisation_policy.py` already records.

  THE FIX, MEASURED: `dummy-variable-rgx = "^_+$"` narrows the exemption to BARE underscores.
  `_review_patch` redefinition is then flagged, `for _ in range(3)` and `a, _ = (1, 2)` still pass,
  and the repo-wide count is UNCHANGED at 12 — the setting adds no noise. Verified all three ways
  before this contract was updated.

  THE PRINCIPLE. LLM reviewers are the most expensive check available and should be spent on
  judgement, not on facts a grep settles. This pays the review ceremony ONCE and removes the class.

refs: >
  Follows !18 (#29) and !19 (#25), both merged 2026-08-07. Arises from the CPO's question, *"What
  would an experienced software developer who has defined 100 AI guardrails do in this situation?"*,
  under his stated constraint: pragmatic mechanisms that improve collaboration WITHOUT red tape that
  slows work and burns tokens. Not a numbered issue — it is the answer to that question.

scope_paths:
  - requirements-dev.txt
  - .ruff-ci.toml
  - tests/test_lint_config.py
  - .gitlab-ci.yml
  - .claude/hooks/git_discipline.py
  - ingestion/api_football/seasons.py
  - tests/test_batch_fixtures.py
  - tests/test_fixture_scheduling.py
  - tests/test_fixtures_cache_skip.py
  - tests/test_injuries_coaches.py
  - tests/test_per_team_completeness.py
  - tests/test_season_inference.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

protected_override: >
  CPO instruction, conversation 2026-08-07: **"ok, do it"**, approving a plan that named the new
  dependency, the `F`/`E9` ruleset, the `.gitlab-ci.yml` step and the opus floor explicitly.

  RECORDED IN FULL at `.claude/task/escalations.log`, entry
  `## 2026-08-07 chore/add-python-linter`. That entry and this field were written in the SAME
  action, which is GitLab #28's class fix.

  THE AUTHORITY IS FOR THESE TWO FILES, NOT A STANDING ONE. It covers `.gitlab-ci.yml` (adding one
  lint step) and `.claude/hooks/git_discipline.py` (deleting one dead import). It does NOT
  authorise editing `.claude/review_routing.json`, `.claude/settings.json`, the reviewer briefs, or
  any guard's logic. Naming the files literally rather than pointing at `scope_paths` is deliberate:
  GitLab #18 is open on exactly that self-reference.

impact_map: >
  writers: none. No raw table, no dbt model, no mart. `ingestion/api_football/seasons.py` is in
  scope for a ONE-LINE deletion of an unused import (`effective_season_max`, F401) — no call site,
  no behaviour, no column, no payload.

  events that fire the protected files: `.claude/hooks/git_discipline.py` runs as PreToolUse on
  EVERY Bash tool call (`.claude/settings.json`, matcher `Bash`) plus two CLI modes.
  `.gitlab-ci.yml` decides what CI enforces on every push and MR.

  what changes in them: `git_discipline.py` loses ONE dead `import subprocess` inside
  `_review_patch_bytes`. The module's other `import subprocess` statements, inside `_staged_stat`,
  `_staged_paths` and `_cumulative_diff`, are untouched and are the ones actually used — verified by
  `ruff` flagging only line 197. No guard logic, no predicate, no message changes.
  `.gitlab-ci.yml` GAINS one `lint:python` job in the existing `test` stage and changes nothing
  existing.

  what stops being enforced if it is wrong: nothing. A wrong lint config fails the new job loudly
  and blocks the MR. ⚠ THIS FIELD CLAIMED A LINT CONFIG "cannot weaken an existing gate" AND THAT
  WAS FALSE — round 1 disproved it: an auto-discoverable root config IS adopted by the pre-commit
  hook, and the first version of this branch would have switched E4/E7 off there. Round 3 removes
  the mechanism rather than the wording: the config is named `.ruff-ci.toml`, which ruff does not
  auto-discover, and CI passes it with `--config`. Deleting the dead import cannot change
  behaviour, and the 660-test suite covers the module.

  blast radius: `ruff` is dev-only, pinned in a NEW `requirements-dev.txt`, and is NOT added to
  `requirements.txt`, so it cannot reach the runtime image or the ingestion container.

  deploy_order: not applicable. No warehouse object. `requirements-dev.txt`, `.ruff-ci.toml` and the
  test files are absent from `data_paths`; `.gitlab-ci.yml` IS in `data_paths` (GitLab #2), so
  MERGING THIS WILL TRIGGER `data:build:main`. Stated rather than discovered, per the handover's
  standing warning.

decisions_taken: >
  THRESHOLD DECLARATIONS, stated because no gate parses this field.

  NEW DEPENDENCY — YES. `ruff`, pinned, dev-only. A CTO threshold in its own right.

  RECURRING COST — YES. One extra CI step per MR, seconds, no new service and no schedule. Set
  against three review rounds on #25 alone. Note separately that merging this fires
  `data:build:main` once, via `data_paths`.

  NEW MECHANISM — NO. A linter is a standard tool in an existing CI stage, not a governance
  mechanism: it grants no authority, gates no decision and changes no verdict rule.

  GUARD INVARIANT — UNCHANGED, and round 3 is what makes that true rather than merely asserted.
  No guard's logic is edited; `git_discipline.py` loses a dead import only. The pre-commit hook is
  NOT touched at all — `.pre-commit-config.yaml` is byte-identical to `main`, so neither its ruff
  `rev` nor `ruff-format` moves. ⚠ ROUND 2 BRIEFLY BUMPED THAT `rev` to align versions, and
  `cto-reviewer` FAILed it: the same `rev` governs `ruff-format`, which rewrites files on every
  local commit, and across v0.7.4 to v0.16.2 **75 files would be reformatted**. Measured, not
  estimated.

  RULESET CHOSEN BEFORE THE COUNT WAS KNOWN, deliberately, so the rules could not be picked to
  flatter the number. The measurement came second: 12 violations. ⚠ THE RULESET ITSELF CHANGED IN
  ROUND 1, from `F` + `E9` to ruff's exact default `["E4","E7","E9","F"]`, because the narrower set
  would have switched E4/E7 off in the pre-existing pre-commit hook. It is now the DEFAULT set and
  not one rule more.

  WHY NO STYLE RULES. On an existing codebase, style and import-sorting rules produce a large
  mechanical diff that no reviewer can meaningfully read, which is the opposite of the point.

decisions_reserved:
  - "⚠ REWRITTEN IN ROUND 3; this bullet reserved widening beyond `F`/`E9` while the branch had
    already widened to ruff's default set, which is the opposite of what shipped. What IS reserved:
    widening beyond ruff's DEFAULT `[\"E4\",\"E7\",\"E9\",\"F\"]` — style, import order, complexity,
    type-checking. Each is a new class of enforced opinion across the whole tree and a fresh
    decision. Narrowing below the default is equally reserved, because it would enforce less in CI
    than the local pre-commit hook already does."
  - "Whether SQLFluff and `ruff` should share one `lint:` stage rather than `ruff` joining `test`.
    Left alone: moving an existing job is a CI-topology change beyond this objective."

done_when:
  - "`ruff check . --config .ruff-ci.toml` exits 0 on the final tree, output pasted. ⚠ THIS
    CRITERION READ `ruff check . --select F,E9` UNTIL ROUND 3, which was worse than stale: a CLI
    `--select` OVERRIDES the config file, so the named acceptance command bypassed the very config
    it was meant to verify, and would have passed on a tree where E4/E7 were red or where the
    config failed to load at all. Caught by `platform-reviewer` at opus. The command here is now
    the same one CI runs."
  - "RED BEFORE GREEN on the real defect: `ruff` demonstrably reports F811 for the exact duplicate
    `_review_patch` definition that cost #25 a review round. If it does not catch that, the linter
    is not worth adding (`feedback_verify_the_test_fails.md`)."
  - "All 12 violations fixed, none suppressed: no `# noqa` added, and no rule removed from `select`
    to make the build pass — that would be the never-loosen-a-guard failure applied to a guard on
    its first day. ⚠ THIS CRITERION ALSO FORBADE `per-file-ignores` UNTIL ROUND 3, while the branch
    ships four. The bar it should have stated, and now does: E402 in the four `sys.path`-shim
    scripts is DECLARED per file in one auditable table, which is narrower and more visible than
    scattered `# noqa: E402` and far narrower than dropping E402 from `select`. Every other shim
    site in the tree already carries a pre-existing `# noqa: E402`, so the list is complete at four
    (counted independently by `platform-reviewer`). Left as written, the criterion would have told
    a future maintainer that per-file-ignores are banned, whose cheapest reconciliation with the
    tree is dropping E402 repo-wide — the exact loosening this branch exists to prevent."
  - "`python -m pytest tests/ -q` clean, collected count MEASURED with `pytest --collect-only -q`,
    and pytest's OWN exit code read directly rather than through a pipe — piping through `tail`
    masked a 4-test failure earlier today."
  - "The five offline gates pass, and `check_task_artifacts.py` runs BARE."
  - "CI green with `lint:python` visible in the job list."

amendments: >
  ONE amendment, 2026-08-07, after review round 1. TWO PATHS ADDED: `.pre-commit-config.yaml` and
  `tests/test_lint_config.py`.

  AUTHORITY: CPO instruction **"do it"**, conversation 2026-08-07, against a stated recommendation
  naming the ruleset change, the `per-file-ignores`, the pre-commit version alignment and the fact
  that `.pre-commit-config.yaml` sits outside the approved scope. Recorded at
  `.claude/task/escalations.log`, same entry, block `⚠ ROUND 1: THE PREMISE WAS FALSE`. That block
  and this amendment were written in the SAME action.

  ⚠ WHY IT WIDENED — THE OBJECTIVE'S PREMISE WAS FALSE. This contract claimed "This repo has NO
  linter and none pinned". `.pre-commit-config.yaml` has configured `astral-sh/ruff-pre-commit`
  `rev: v0.7.4` all along, over `ingestion|scripts|tests|dbt_project/macros|dbt_project/seeds`, and
  `.git/hooks/pre-commit` is installed, so it fires on every local commit. The claim came from
  grepping `requirements*.txt` only and reporting that scoped result as a general one — the #904
  class, and the THIRD instance from this builder in two days. Found by `cto-reviewer` and
  `platform-reviewer` independently, at opus.

  ⚠ AND THE CHANGE AS APPROVED WOULD HAVE LOOSENED AN EXISTING GUARD. Ruff walks up for config, so
  a NEW root `ruff.toml` is read by the pre-commit hook too. MEASURED over that hook's own file
  set: ruff's defaults (`E4,E7,E9,F`) report **10** violations, all E402; the approved
  `select = ["F","E9"]` reports **0**. Shipping it would have silently stopped E4 and E7 being
  enforced on every local commit — never-loosen-a-guard, committed inside an MR justified as
  strengthening guards.

  WHAT CHANGES. `select` becomes `["E4","E7","E9","F"]`, ruff's default, so NOTHING is narrowed
  anywhere. The 10 E402s are declared in `per-file-ignores` rather than fixed: all four files use
  the deliberate `sys.path.insert(...)`-then-import shim, where the import genuinely must follow the
  path setup. `.pre-commit-config.yaml`'s `rev` moves to `v0.16.2` to match the pinned CI version,
  because both now read the same `ruff.toml` and every measurement here was taken on 0.16.2.
  `tests/test_lint_config.py` pins `select` and `dummy-variable-rgx`, closing `platform-reviewer`'s
  finding that the load-bearing setting had nothing stopping its removal.

  BOUNDED: this does NOT change what CI runs beyond the ruleset, does not touch SQLFluff's
  pre-commit entry, and adopts no style, import-sorting or formatting rules. `select` is now exactly
  ruff's default and not one rule more.

  SECOND AMENDMENT, 2026-08-07, after review round 2. NET EFFECT: ONE PATH ADDED (`.ruff-ci.toml`),
  TWO REMOVED (`ruff.toml`, `.pre-commit-config.yaml`). Written in the SAME action as its
  `escalations.log` block.

  AUTHORITY: the same CPO instruction **"do it"** (2026-08-07). This amendment does not widen the
  task — it NARROWS it, giving back a path the first amendment took. Both round-2 FAILs are fixed
  by touching strictly less than round 2 did.

  ⚠ WHY: the two round-2 FAILs pulled in OPPOSITE directions. `cto-reviewer` FAILed the
  `.pre-commit-config.yaml` `rev` bump, because the same `rev` governs `ruff-format` and across
  v0.7.4 to v0.16.2 **75 files would be reformatted** — measured, and exactly the unreviewable
  mechanical diff this branch argues against. But NOT aligning the versions leaves two ruff versions
  reading one config, which was `platform-reviewer`'s round-1 finding. Aligning or not aligning both
  lose.

  THE FIX DISSOLVES BOTH RATHER THAN TRADING THEM. Ruff auto-discovers only `ruff.toml`,
  `.ruff.toml` and `pyproject.toml`. Naming the file `.ruff-ci.toml` and passing `--config` in CI
  means the pre-commit hook never reads it: no shared config, so no version alignment is owed, so
  `ruff-format` never moves. VERIFIED both ways before adopting: with the file present and no
  `--config`, a redefined `_f` is NOT flagged (config not discovered); with `--config .ruff-ci.toml`
  it IS.

  `.pre-commit-config.yaml` is therefore byte-identical to `main` and leaves `scope_paths`.

  ALSO IN ROUND 3, all text-only and all found by review: the false "no linter" premise removed from
  `.gitlab-ci.yml` and the config's own comments (it survived round 2 verbatim in both PERMANENT
  artifacts while only the contract was corrected — corrections must replace, not accumulate); the
  `done_when` command that bypassed its own config; the `done_when` bar that forbade the
  `per-file-ignores` the branch ships; `decisions_reserved` reserving a widening already taken; the
  `impact_map`'s disproved "cannot weaken an existing gate"; and "ten F401s" corrected to NINE
  inside the hook's file pattern.
