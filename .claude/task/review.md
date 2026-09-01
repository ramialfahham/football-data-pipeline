# Review — docs/nightly-lives-in-cloud-scheduler — 2026-09-01

> **Record where the nightly actually runs.** `CLAUDE.md` told every session that nothing refreshes
> the data on a timer, while a Cloud Scheduler job did exactly that each morning. Documentation
> only — no code, no config, no infrastructure. Branched from main `1e76078`.

diff_sha256: a6c966e8865a131a516f6f6a53be6c96292a473d7bf27a71e7fa10c7c4440215

rounds: 1

⛔⛔ **THIS MR IS A CORRECTION OF MY OWN REPORTING.** While attributing `!136`'s BigQuery spend I
found a daily 04:02 UTC pipeline, could not reconcile it with the docs, and reported it to the CPO
as **unexplained recurring cost**. It was neither unexplained nor unauthorised. His answer, verbatim:
*"We moved these two jobs to the cloud after your recommendation. We did this after I ran into CI
limitations with Gitlab."* Authorised, on my own earlier recommendation, and recorded nowhere — the
documentation gap was the only real defect.

**Three errors, each with the rule it earned:**

**(a) I named a culprit from a NAME.** I told the CPO GitHub Actions was running it, from two
circumstantial facts: the service account is `github-actions-dbt@…`, and
`.github/workflows/dbt-scheduled.yml` carries a matching `0 4 * * *` cron. He refused it in one
sentence — *"How is that possible, the account is suspended"* — and was right. The AUTH PATH settled
it in two queries: that SA has **zero user-managed keys** and exactly one `workloadIdentityUser`
binding (the `gitlab-pool`), so GitHub could never have assumed it.
⭐ **Identify a caller by how it AUTHENTICATES, never by what it is NAMED.**

**(b) I called it unexplained when it was merely undocumented.**
⭐ **Ask which of the two it is before reporting it.**

**(c) I quoted a rate from ONE sample** — ~$7/month, from a day that was the smallest of the previous
fourteen (37 GB against a 15–197 GB range), and before I had found `fdp-freshness` at all. Measured
over 14 days: **~129 GB/day ≈ 3.8 TiB/month ≈ $17–24**.
⭐ **Pull a RANGE before quoting a rate.** ⚠ And query `region-eu` — `region-us` returns a confident,
false "0 jobs, no cost".

## scope-auditor
VERDICT: PASS

risks_checked:
- **Append-only log verified structurally**: the `escalations.log` diff is a single hunk
  `@@ -7300,3 +7300,43 @@`, all `+` lines, **zero `-` lines**, with the prior `!136` entry sitting
  in unmodified context. The dated record of the mistaken belief survives intact — correcting it in
  place would have been falsifying the record.
- **Executable surface**: no `.gitlab-ci.yml`, no `.github/workflows/**`, no scheduler or IAM config
  anywhere in the diff or the excluded-but-listed file set, matching `protected_override`.
- **Authority use**: the CPO quote is cited as attribution of a past fact only, and nothing in
  `decisions_taken` converts it into a new ruling.
- **Cost figures consistent** across `contract.md`, `escalations.log` and `CLAUDE.md` — no inflation
  between documents, and the earlier wrong `~$7/month` figure is explicitly flagged along with the
  mechanism that produced it.
- **Reserved decisions correctly withheld**: `fdp-freshness`'s hourly cadence and the disabled GitLab
  schedule's fate are recorded as facts for the CPO, not acted on — recurring-cost decisions are his
  alone under §10.
- `scope_paths` reconciled against every touched file; Appendix A1–A6 anti-patterns checked and none
  match — a factual correction of infrastructure documentation, not a new mechanism.

## escalations

**None raised.** The CPO's statement is used as attribution for a factual correction, not as a new
ruling, and the new dated `escalations.log` entry records both the correction and how I got it wrong.

⛔ **RECORDED FOR THE CPO, DELIBERATELY NOT ACTED ON** — both are recurring-cost or infrastructure
calls, and this MR changes no infrastructure at all:
  - **Whether `fdp-freshness` needs to run hourly** (24×/day).
  - **Whether GitLab schedule `4379625` should be deleted** rather than left disabled and reading
    like the intended owner. ⚠ Enabling it without disabling `fdp-nightly` would run the build twice.

⚠ **CARRIED, untouched:** step 5's two follow-ups (the seed `description` column; the four chrome
strings including the hero x-axis); the `__team`/`__player` split with no live instance; the resolver
as a committed CI gate; **#99**, **#96**, **#87**, **#98**; `stash@{0}`'s parked value-equivalence
test.
