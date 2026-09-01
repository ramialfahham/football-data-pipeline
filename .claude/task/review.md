# Review — docs/nightly-lives-in-cloud-scheduler — 2026-09-01

> **Record where the nightly actually runs.** `CLAUDE.md` told every session that nothing refreshes
> the data on a timer, while Cloud Scheduler did exactly that each morning — and while
> `deploy/nightly/README.md` documented it correctly all along. Documentation only.
> Branched from main `1e76078`.

diff_sha256: 3309f89ef4bdf915c612276fdebe7dea3067f4eb1ae18a9921d3adc5762409db

rounds: 3

⛔⛔ **THIS MR IS A CORRECTION OF MY OWN REPORTING, AND IT TOOK THREE ROUNDS BECAUSE I KEPT MAKING
THE SAME SHAPE OF MISTAKE WHILE CORRECTING IT.** Five errors, one pattern: **reporting a conclusion
before checking the cheapest disconfirming source.**

  1. **Named a culprit from a NAME.** Told the CPO GitHub Actions ran the nightly, from the service
     account being `github-actions-dbt@…` plus a leftover workflow file with a matching cron. Both
     circumstantial, stated as fact. He refused it in one line — *"How is that possible, the account
     is suspended"* — and the AUTH PATH settled it in two queries: zero user-managed keys, one
     `workloadIdentityUser` binding to `gitlab-pool`. GitHub could never have assumed it.
     ⭐ **Identify a caller by how it AUTHENTICATES, never by what it is NAMED.**
  2. **Said "unexplained" when I meant "undocumented".** It was authorised, on my own earlier
     recommendation. ⭐ **Ask which of the two it is before reporting it.**
  3. **Quoted a monthly rate from ONE day** — the smallest of the previous fourteen, and before I had
     found `fdp-freshness` at all. Real figure: ~129 GB/day ≈ 3.8 TiB/month ≈ $17–24.
     ⭐ **Pull a RANGE before quoting a rate.** ⚠ And query `region-eu`; `region-us` returns a
     confident, false "0 jobs, no cost".
  4. **Said "recorded nowhere" without searching the tree** (caught before merge, round 2).
     `deploy/nightly/README.md` is a full runbook for this exact arrangement. I went from BigQuery
     metadata straight to `CLAUDE.md` and stopped at the first document that mentioned schedules.
     ⭐ **"Undocumented" is a claim about the WHOLE TREE — one `git grep` settles it.**
  5. **Corrected (4) everywhere except the record that matters most** (round-2 FAIL, below).

⭐ **The MR's shape changed because of (4).** The defect is **one stale document contradicting a
correct one**, not an undocumented decision — so `CLAUDE.md` now POINTS AT the runbook instead of
restating it. Duplicating it would have created a second document to keep in sync: the same failure,
one step later.

## scope-auditor
VERDICT: PASS

**Round 1 PASS. Round 2 FAIL. Round 3 PASS.**

⛔ **The round-2 FAIL is the one worth reading.** I corrected "never written down" in `contract.md`,
`acceptance_evidence.md`, `CLAUDE.md` and `active_work.md` — the living documents — and **left it
standing inside the `escalations.log` entry I had appended hours earlier**, which is the artifact a
later reader actually consults. `scope-auditor` caught it and made the sharpest possible point:
this MR's own `protected_override` states the rule it broke — *"escalations.log IS APPENDED TO,
NEVER REWRITTEN … the correction is a new dated entry."* **I wrote that rule into this contract and
then failed to follow it inside the same MR.** That is `feedback_corrections_replace`, and the place
I keep missing is the append-only record — precisely because fixing it needs a NEW write rather than
an edit to a document already open in front of me. Fixed by appending a dated correction-to-the-
correction; the stale entry stays verbatim, as the rule requires.

risks_checked:
- **The corrected framing verified at source**: read `deploy/nightly/README.md` in full and confirmed
  it documents the Cloud Run jobs, scheduler entries, service account, IAM bindings and the `gcloud`
  commands — so "recorded nowhere" was wrong and "one stale doc contradicting a correct one" is right.
- **`CLAUDE.md` checked for duplication vs deferral**: it states job names, crons, region, cost and
  the name trap inline (as `acceptance_criteria` requires), then points at the runbook for IAM and
  commands rather than repeating them. A pointer, not a maintenance trap.
- **Append-only mechanics**, both rounds: 0 removed lines; the `!136` entry and the first correction
  entry both untouched; each correction is a new dated append.
- **Nothing executable** in the diff across all three rounds — no workflow, `.gitlab-ci.yml`,
  scheduler config, IAM binding, credential or secret-shaped string.
- **Authority use**: the CPO's sentence is cited as attribution of a past fact, never inflated into a
  new ruling.
- **`scope_paths` reconciled** against every touched file; Appendix A1–A6 checked, none match.
- **Reserved decisions still reserved**: `fdp-freshness`'s hourly cadence and the disabled GitLab
  schedule's fate remain the CPO's, recorded as facts rather than acted on.

## escalations

**None raised.** The CPO's statement is attribution for a factual correction, not a new ruling.

⛔ **RECORDED FOR THE CPO, DELIBERATELY NOT ACTED ON:**
  - **Whether `fdp-freshness` needs to run hourly** (24×/day).
  - **Whether GitLab schedule `4379625` should be deleted** rather than left disabled and reading
    like the intended owner. ⚠ Enabling it without disabling `fdp-nightly` runs the build twice.
  - ⚠ **The service account's `displayName`/`description` are still unset/misleading.** The email is
    immutable, but those two fields are what `gcloud` and the Console show, and they would make the
    account self-identifying at the point of inspection. **I could not apply it — the session's
    permission gate refused the prod IAM write** — so the exact command was handed to the CPO
    instead. Not a defect in this diff; recorded so it is not lost.

⚠ **CARRIED, untouched:** step 5's two follow-ups; the `__team`/`__player` split with no live
instance; the resolver as a committed CI gate; **#99**, **#96**, **#87**, **#98**; `stash@{0}`'s
parked value-equivalence test.
