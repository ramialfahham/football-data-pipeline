# Review — <branch> — <date>

> The machine-checked review artifact (governance G3). Written in step 4
> (Lock) of the review cycle, AFTER staging and AFTER the blinded reviewers
> returned. The commit gate denies `git commit` unless: this file exists,
> `diff_sha256` equals the live staged diff hash
> (`python .claude/hooks/git_discipline.py --staged-hash`), every reviewer
> required by `.claude/review_routing.json` for the staged paths has a verdict
> section, no FAIL exists, every ESCALATE has a `CPO ANSWER:`, every PASS
> says what it examined (at least one entry under `risks_checked:` — it need NOT
> name a defect; CPO 2026-08-01), `rounds:` is present and within the cap
> of 3, every finding is `[blocking]` or `[nit]` with its class (a PASS carries
> no blocking finding, a FAIL at least one), and past round 1 `## fixes` names
> each fix's sweep and a test file the branch changes (`tests/**/test_*.py`,
> `dbt_project/tests/**.sql` or `site_v2/**/*.test.mjs`), or holds the one entry `- none: <why>` after a
> round of PASS verdicts. Commits touching only artifact paths
> (.claude/task/**, .claude/active_work.md) are exempt, and a branch of text paths
> needs no review.md. Stage with `git add`
> then plain `git commit` as the SOLE command in its own call — commit flags
> are allowlisted (message/quiet/verbose/sign only); any other flag, any
> pathspec, any git global option, and any chained sibling command is denied
> (each would commit content the hash never covered).

diff_sha256: <64-hex; run `python .claude/hooks/git_discipline.py --staged-hash` (covers code + contract.md, excludes bookkeeping artifacts; CI recomputes the same — F11/#409)>

rounds: <how many review rounds this issue has taken, across sessions; 1 on the first. A merge of main that leaves the review hash unchanged is not a round (docs/working_agreement.md §2). The gate caps it at 3; at the cap the work is split. A further round is the CPO's call: add `rounds_cap_override: approved in chat, <date>`.>

## <required-reviewer>
VERDICT: PASS
findings:
- [nit] <class>: <every place, file:line> — <what goes wrong>
risks_checked:
- <what you examined, and what you concluded — "checked X against Y, no defect"
  is a complete entry. One is enough. Do NOT invent a finding to fill a second.>

## <other-required-reviewer>
VERDICT: PASS
risks_checked:
- <what you examined, and what you concluded — "checked X against Y, no defect"
  is a complete entry. One is enough. Do NOT invent a finding to fill a second.>

## fixes
<!-- required when rounds: is above 1; one line per blocking class fixed, or the one
     line `- none: <why>` when the round followed only PASS verdicts -->
- <class> | sweep: <how every place was found> | test: <tests/file.py::test_name>

## escalations
(none)
<!-- or, per escalated question:
- question: <the blinded question as put to the CPO>
  CPO ANSWER: <where and when the CPO answered; never his words>
-->
