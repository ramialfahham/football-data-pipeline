# Review — chore/gitlab-ci-manual-prod-build — 2026-08-06

branch: chore/gitlab-ci-manual-prod-build
diff_sha256: 90027a64f2122ebfbdea5a71a84ec5585681f5c65387739a503bc94a0547a64f

rounds: 2

> FOUND BEFORE IT COST ANYTHING, which is the only reason this branch exists. The CPO
> asked for `data:nightly` to be run manually. Evaluating the rules before triggering —
> rather than reading the bill afterwards — showed that a web dispatch also auto-started
> `data:build:main`, a full prod warehouse build, because a web pipeline is on main and
> GitLab evaluates `changes:` as TRUE on any non-push pipeline. Asking for a nightly would
> silently have bought a third prod build that day, right after the CPO twice objected to
> that spend.
>
> This is the same mechanic Phase 3 guarded against for SCHEDULES. It was not re-checked
> for `web`, because `data:build:main`'s `if: web` clause predates it and meant "I want a
> full prod build now" — reasonable until `data:nightly` gave web dispatch a second
> purpose and conflated the two intentions.

## scope-auditor
VERDICT: PASS
risks_checked:
- ESCALATED FIRST, then withdrawn on argument — recorded because the reasoning matters more
  than the verdict. The reviewer held that classifying this was itself a CPO decision under
  the §10 meta-rule. The builder challenged rather than forwarding, on one point the
  escalation had not addressed: §10's cost reservation is DIRECTIONAL. It exists to stop a
  builder committing the CPO to unapproved spend. This change cannot increase spend in any
  context (push identical, schedule unchanged, web auto -> button) and removes no
  capability. If §10 also covered changes that only ever REDUCE unrequested spend, the
  reservation would protect the outcome it exists to prevent. The reviewer accepted and
  re-issued PASS. No CPO attention was spent, which was the point — this CPO has twice
  said they do not want decisions of this size brought to them.
- Scope: every file in the diff is within `scope_paths`, declared before the edits.
- Authority: the `protected_override` is narrow and says so — "ok do it" authorised RUNNING
  the nightly, not this edit; the edit is justified as a precondition to executing that
  instruction without unrequested spend.
- Nothing asserted beyond its evidence: no pipeline has run, and no cost figure is quoted
  (the CPO instructed the cost tooling not be run).
- `decisions_reserved` correctly keeps the broader question — whether merge-to-main should
  build prod at all — OUT of this task; it is filed as GitLab issue #2 with evidence.

## platform-reviewer
VERDICT: PASS
risks_checked:
- BOTH HALVES OF THE FIX ARE NECESSARY, traced by hand rather than accepted: before the
  fix, a web dispatch matched the bare branch clause FIRST and ran `on_success` before the
  web-scoped clause was ever reached — so adding `when: manual` alone would have looked
  right and changed nothing. Adding `$CI_PIPELINE_SOURCE == "push"` to the branch clause is
  what actually closes it.
- A PUSH to main still auto-builds prod. Verified explicitly, and pinned by an assertion in
  the new test — a "fix" that silently stopped prod rebuilding would be worse than the
  defect, since prod is the baseline every MR's `state:modified+` defers to.
- `$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH && $CI_PIPELINE_SOURCE == "push"` is valid rules
  syntax and `push` is the correct source value for an ordinary push.
- `_CONDITION_TRUTH` checked entry by entry against real GitLab semantics, including that
  `CI_COMMIT_BRANCH` is unset on MR pipelines. A wrong entry would silently invalidate
  every test built on it.
- FALSE POSITIVE IN MY OWN TEST, caught and fixed before review: the first version of
  `spends_warehouse_money` substring-matched `"dbt build"` and flagged `deploy:site-v2`,
  which runs npm and firebase and no dbt — because `.gcp_auth`'s ERROR MESSAGE contains the
  words "dbt build". A detector that reads prose as commands produces false positives that
  get "fixed" by weakening the real config.
- NOTED AT PASS AND THEN CLOSED, recorded because it changed the diff after the verdict:
  the anchored regex tolerated only a single `cd x && ` prefix and covered only
  `build|test|seed`, so a chained command or `dbt run`/`dbt snapshot` would have slipped
  past — while the docstring claimed nothing could dodge it. The regex now matches dbt in
  COMMAND POSITION (line start or after `&&`/`;`/`|`) and includes `run` and `snapshot`,
  making the docstring's claim true rather than narrowing it. Verified against nine cases
  including the chained form and the prose false-positive.
- ALSO NOTED BY THIS REVIEWER, outside its remit and fixed anyway: `protected_override`
  quoted CPO dialogue that appeared in no durable record — the exact failure class
  `scope-auditor` failed the Phase 3 contract on. Now recorded in `escalations.log` with
  the authority explicitly bounded, and the contract reduced to a pointer.
- Stale comments swept; no dependency, credential, hooks or hosting change in this diff.

## cto-reviewer
VERDICT: PASS
risks_checked:
- REQUIRED BY ROUTING, and this reviewer was initially skipped on the builder's judgement
  that "no new mechanism means no CTO review". The commit gate refused and was right:
  routing is PATH-based, not judgement-based, and `.gitlab-ci.yml` is one of exactly three
  paths carrying both opus specialists. Recorded because the builder's reasoning was the
  kind that sounds sensible and quietly drops a required reviewer.
- Rule evaluation traced by hand for all four pipeline sources; both `done_when` claims
  hold and the push path is genuinely untouched — no regression in the direction that
  matters, prod going silently stale.
- The "both halves are needed" claim re-derived independently against first-match-wins
  semantics rather than accepted from the contract.
- The load-bearing premise — that GitLab evaluates `changes:` as TRUE on any pipeline that
  is not a push or an MR — re-derived from documented behaviour rather than taken on faith
  from the file's own comment, since the whole fix rests on it.
- The new pin read line by line: it flags exactly the three warehouse-writing jobs and no
  others (`validate:governance`'s `dbt deps && dbt parse` correctly excluded), so
  `checked >= 3` is not a vacuous pass, and it would have failed pre-fix.
- No new mechanism, dependency or secret anywhere in the diff.
- §10 JUDGED INDEPENDENTLY, having been asked directly whether `scope-auditor` was talked
  out of a correct position: the directional reading holds on inspection — the change
  cannot increase spend in any traced context, removes no capability, and is declared
  openly rather than absorbed silently. Conclusion: the reviewer was not talked out of a
  correct position.
- Authority record checked against `escalations.log` directly rather than the contract's
  paraphrase: the quotes are verbatim, and the contract's disclaimer that this authorises
  a precondition-fix rather than the edit itself is accurate and not stretched.
- PRE-EXISTING GAP FOUND, outside this task's scope and NOT introduced by it:
  `data:build:main`'s `if: $CI_PIPELINE_SOURCE == "web"` clause carries no branch
  restriction, so a web dispatch from ANY branch can run a prod-target build of that
  branch's code. It came whole from MR !4 and this diff makes it strictly safer (one
  manual click instead of automatic). Filed as a follow-up issue rather than widened into
  this task — fixing it here would be the under-scoping this migration has already been
  ruled on once.

## escalations
(none outstanding — the one raised was withdrawn on argument, and is recorded above and in
`.claude/task/escalations.log` under the §10 CLASSIFICATION entry.)
