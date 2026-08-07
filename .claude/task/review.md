# Review — chore/mark-github-dormant — 2026-08-06

branch: chore/mark-github-dormant
diff_sha256: 55126e3e72b158ad33f4e9b585a4e9c73d002ec17aac4f8e2efb0dd740065a0a

rounds: 2

> Marks the dormant GitHub Actions tree as dormant WITHOUT touching it, corrects `CLAUDE.md`, and
> moves the operational notes out of the 16,000-char-capped handover into a file that is always
> loaded and never truncated.
>
> THREE FINDINGS, ALL IN THE PROSE, AND THE FIRST TWO WERE IN THE ONE PART THAT MATTERS.
> `.github/workflows/README.md` exists to stop a costly mistake, and its first version got the
> mistake wrong in both directions: it under-counted the production BigQuery writers, and it told
> the reader re-activation is a deliberate act when an ordinary push re-arms it. A warning
> document that is wrong is worse than none, because it is believed.

routing:
  - scope-auditor — `always`
  - cto-reviewer + platform-reviewer — `.github/workflows/**` (guard path → OPUS floor)

  `.github/workflows/README.md` matches `.github/workflows/**` because `fnmatch`'s `*` crosses
  `/`. That is why a markdown file drew two opus specialists, and it is the correct outcome:
  the prefix is a PATH rule, not a judgement about whether a given file executes.

## scope-auditor

VERDICT: PASS

rounds: PASS (1, full — 19 tool calls)

risks_checked:
- `.github/` diff scope — confirmed only the new `README.md`; grepped the eleven `*.yml` and the
  three in `_paused/` on disk to verify none was touched, matching `protected_override`'s narrow
  "one non-executing file" authority and `done_when` item 1.
- README factual accuracy, re-derived rather than read: 11 workflows + 3 paused, exactly the 7
  named carrying `push: branches: [main]`, the 3 prod-writers, both cron times, and the `#667`
  concurrency comment quoted verbatim from `ci-data-build.yml:57-61`.
- `decisions_reserved` honoured — the README states dormancy and gives pre-reactivation safety
  instructions but proposes no archiving, mirroring, deletion or future use, and does not merge
  the two dormancy categories.
- Amendment honesty — verified `handover_in.py:46` `MAX_CHARS = 16000` matches the stated cap, and
  that the handover's pointer names the same items now present under `CLAUDE.md`'s new section, so
  nothing was dropped in the move.
- Thresholds — no hook, CI, script or config file added or modified outside the declared files.
- Credentials — only prose references to the `validate:secrets` job name.

## cto-reviewer

VERDICT: PASS

rounds: FAIL (1, full) · PASS (2, full re-read)

Round 2 REFUSED the delta framing — its brief sanctions a delta only after a prior PASS, and
round 1 was a FAIL — and re-read all 605 lines rather than judging through a keyhole.

risks_checked:
- **R1 FINDING — the README named TWO production BigQuery writers when there are THREE.**
  `ci-data-build.yml` was missing, and it is the most expensive of them: `dbt seed` +
  `dbt build --selector staging` + `--selector downstream` + `dbt test --target prod` on any
  non-`pull_request` event, plus a bootstrap ingest that spends API-Football calls. The file's own
  comment names the count — *"the three prod-writers never MERGE the bare prod tables
  concurrently (#667)"*. A reader working the checklist would have concluded `ci-data-build.yml`
  was not a cost surface. FIXED; the table now has three rows and distinguishes profile-level
  `target: prod` from the CLI `--target prod` whose profile default is `ci`.
- **R1 FINDING — "treat re-activation as something you do, not something that happens" was
  FALSE**, and the reasoning inverted. SEVEN of the eleven trigger on `push: branches: [main]`, so
  the first ordinary sync push to a reactivated remote re-arms them — running a full prod
  warehouse build and republishing the product retired 2026-07-21. Two crons are still in the
  files, untouched. FIXED: the section is rebuilt around "dormant, not disabled", lists the seven
  and both cron times, states that GitHub's concurrency group does not protect across platforms,
  and ends with a prescribed action.
- Round 2 verified the correction UPWARD — the builder found seven where the reviewer had said
  six, and the reviewer re-counted the `on:` blocks itself and confirmed seven, recording its own
  round-1 undercount.
- The prescribed mitigation was checked rather than assumed: moving a workflow to `_paused/`
  disables it only because GitHub Actions does not scan subdirectories, which the repo already
  relies on for three files — so the advice uses an existing convention, not a new mechanism.
- The override judged correct rather than generous: `PROTECTED_PREFIXES` is a path prefix, so the
  gate would refuse the write regardless of the file being inert, and parking it one level up in
  `.github/` to evade the prefix would have moved the marker away from what it marks.
- `done_when` item 1 verified against the patch, not trusted. `.github/workflows/**` is in neither
  `review_exclude_paths` nor `review_summarise_paths`, so a workflow edit could not have been
  hidden from review.
- The operational-notes move verified bullet by bullet — every one restates an existing mechanic
  with a source; no new rule written under cover of a move.
- Thresholds: no new mechanism, dependency, external surface, credential or guard edit. The
  README itself cannot trigger the data build — `ci-data-build.yml`'s path filter is
  `.github/workflows/ci-*.yml`.

## platform-reviewer

VERDICT: PASS

rounds: FAIL (1, full) · PASS (2, full re-read)

Round 2 also declined the delta framing on the same grounds and re-read all 605 lines.

risks_checked:
- **R1 FINDING — `CLAUDE.md:11` told every session to run `gh pr list --state open` as session-start
  step 5**, against a suspended account, citing `working_agreement.md` §3a which already said
  `glab mr list`. The sharpest part: THIS DIFF CREATED THE CONTRADICTION. The file was uniformly
  (if wrongly) GitHub before; adding "use `glab`, open MRs not PRs" 146 lines below left a
  session's FIRST executed instruction contradicting the file's own stack section, and defeated
  the contract's own `done_when` ("so a session cannot infer either one wrongly"). FIXED at both
  sites — step 3 also listed `gh`. Swept repo-wide afterwards; the only surviving hit is the
  removed line inside this diff.
- The new cross-file claim ("§3a says the same") was CHECKED rather than accepted: same command,
  same two questions, same order at `working_agreement.md:261-264`. It is now verifiable in both
  directions instead of divergeable.
- Every factual claim in the rewritten warning section independently re-derived: the seven
  push-triggered workflows by name and line, both crons, the three prod writers and their two
  different mechanisms, and that GitHub's `concurrency:` groups are repository-scoped so two
  independent queues sit over one BigQuery dataset.
- The GitLab equivalence table checked row by row against `.gitlab-ci.yml`'s own `# was:` comments
  — all eight mappings and all three "none" rows hold; eleven rows for eleven workflows.
- The two precision edits verified: the `needs.changes.outputs.data` gate at
  `ci-data-build.yml:63-65`, and all three paths named in the caveat genuinely present in the
  filter.
- Re-run safety, tests owed, dependencies, credentials, permissions, build size, duplicated
  enforcement — none engaged; nothing in the diff executes.

## escalations

none.

## Known and deliberately not fixed

1. **`contract.md`'s `decisions_reserved` bullets under-describe the artifact.** Bullet 1 says the
   README "says nothing about … re-activating", but the round-2 README does prescribe an action at
   re-activation, including conditionally moving workflows to `_paused/`. `cto-reviewer` raised it
   as an ADVISORY and explicitly declined to fail it: in substance the reservation holds — the
   README takes no position on what GitHub is FOR, and its advice is conditional on an event that
   cannot occur while the account is suspended. It applied the precedent it set on the previous
   task (a contract edit voids every verdict for a round) rather than inventing an exception.
   Correct if the contract is opened for any other reason.

2. **"the eleven `.yml` files here were last edited 2026-07-28"** — neither opus reviewer had shell
   access to verify it, and both said so rather than counting it as evidence. Builder-verified:
   `git log -1 --format=%ad --date=short -- .github/workflows/` → `2026-07-28`. Recorded here so
   the claim's provenance is visible rather than implied.

## Process note

Both opus reviewers were sent a delta brief after a FAIL and both refused the framing, on the
correct ground that a delta is sanctioned only after a prior PASS. Neither refused the ROUND —
each re-read the full patch and said so explicitly. That is the third and fourth time in this
session's work that the keyhole condition has been exercised, against one earlier instance where
a delta was accepted with zero tool calls and certified the builder's summary instead of the
change.

Worth recording about this task specifically: the two most consequential findings were in PROSE,
in a documentation file, on a branch that changes no executable line. The reviewers' value here
was not code review — it was checking a warning against the thing it warns about.
