# Review — <branch> — <date>

> The machine-checked review artifact (governance G3). Written in step 4
> (Lock) of the review cycle, AFTER staging and AFTER the blinded reviewers
> returned. The commit gate denies `git commit` unless: this file exists,
> `diff_sha256` equals the live staged diff hash
> (`python .claude/hooks/git_discipline.py --staged-hash`), every reviewer
> required by `.claude/review_routing.json` for the staged paths has a verdict
> section, no FAIL exists, every ESCALATE has a `CPO ANSWER:`, every PASS
> says what it examined (at least one entry under `risks_checked:` — it need NOT
> name a defect; CPO 2026-08-01), and `rounds:` is present and within the cap
> of 3. Commits touching only artifact paths
> (.claude/task/**, .claude/active_work.md) are exempt. Stage with `git add`
> then plain `git commit` as the SOLE command in its own call — commit flags
> are allowlisted (message/quiet/verbose/sign only); any other flag, any
> pathspec, any git global option, and any chained sibling command is denied
> (each would commit content the hash never covered).

diff_sha256: <64-hex; run `python .claude/hooks/git_discipline.py --staged-hash` (covers code + contract.md, excludes bookkeeping artifacts; CI recomputes the same — F11/#409)>

rounds: <how many review rounds this branch has taken; 1 on the first. The gate caps it at 3 — past that, STOP and bring the open findings to the CPO instead of looping. To proceed anyway on the CPO's say-so, add `rounds_cap_override: <their reason>`.>

## scope-auditor
VERDICT: PASS
risks_checked:
- <what you examined, and what you concluded — "checked X against Y, no defect"
  is a complete entry. One is enough. Do NOT invent a finding to fill a second.>

## <other-required-reviewer>
VERDICT: PASS
risks_checked:
- <what you examined, and what you concluded — "checked X against Y, no defect"
  is a complete entry. One is enough. Do NOT invent a finding to fill a second.>

## escalations
(none)
<!-- or, per escalated question:
- question: <the blinded question as put to the CPO>
  CPO ANSWER: <the CPO's recorded answer, verbatim or referenced>
-->
