# Task contract — <short title>

> Copy to `.claude/task/contract.md` BEFORE touching any file. The contract gate
> denies every edit outside `scope_paths`. Write it on a clean tree; state it to
> the CPO; amendments only on a clean tree with the CPO authority recorded.
> See docs/working_agreement.md §2 (contract), §10 (decision rights),
> §11 (blinded escalation), Appendix A (anti-patterns).

objective: >
  <1-2 lines: what this task builds and why>
refs: <#issue / GAP-nn / plan reference>

scope_paths:
  - <repo-relative path or glob — be surgical, no catch-all wildcards>

# Only for CPO-approved governance tasks that must edit the guards themselves
# (.claude/hooks/, .claude/settings.json, .github/workflows/). Quote the approval.
# protected_override: >
#   <CPO approval reference>

decisions_taken: >
  <what this contract pre-approves, quoting the CPO ruling it rests on>

decisions_reserved:
  - <every known ambiguity / CPO-class question (§10) that may surface;
     escalate each blinded (§11) — never decide>

done_when:
  - <mechanical verification steps: commands, tests, expected outputs>

amendments: (none)
# On amendment (clean tree only):
#   - <date>: + <path> — authority: <CPO answer / standing rule>; content: <what>
