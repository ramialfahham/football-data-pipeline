# Task contract — the football reviewer becomes a senior football data analyst; plain language in section 9

objective: >
  How step 2 of the issue "Metric layer: every rule in one place, plain descriptions, a map an AI
  can read" (#190), a governance MR. The football reviewer's brief and its role doc are replaced by
  the versions the CPO approved: a senior football data analyst who judges whether a metric is real
  on the pitch, whether its description says plainly what it means on cleaned data, and whether
  each changed catalogue column holds only its own thing. working_agreement.md section 9 gains the
  plain-language line.

refs: >
  #190, approved by the CPO in chat on 2026-10-03 ("yes"), with the brief and role doc shown to him
  for a yes, as its checklist asks; its standards lines approved the same day ("yes"). #190's step 1
  is !243 (the rule blocks this brief names as an input).

acceptance_criteria:
  # The issue's checklist lines this MR delivers, verbatim.
  - "`working_agreement.md` section 9: explanations, issues and MR heads follow ISO 24495-1 (plain language): the reader finds, understands and can use what they need."
  - "The football reviewer is a senior football data analyst: is the metric real on the pitch, does its description say plainly what it means, does each changed column hold only its own thing. Brief and role doc for the CPO's yes."

scope_paths:
  - .claude/agents/football-analytics-expert-reviewer.md
  - docs/roles/football_analytics_expert.md
  - docs/working_agreement.md
  - .cursor/rules/agent-behavior.mdc
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

protected_override: >
  `.claude/agents/football-analytics-expert-reviewer.md` is a protected path. Authority: the CPO's
  "yes" in chat on 2026-10-03 to #190 and to the new brief and role doc shown to him for that yes
  (#190: "Brief and role doc for the CPO's yes"). The brief keeps its name, tools, model, trigger,
  verdict rules, output format and delta re-review section; its intro, inputs and hunt are the
  approved text. The MR head's Locked files line repeats this.

impact_map: >
  A protected path, so what depends on the guard: the routing row in .claude/review_routing.json
  sends dbt_project/seeds/metric_catalogue.csv to football-analytics-expert-reviewer, by the name in
  the brief's frontmatter, which does not change; tests/test_governance_hooks.py pins that route and
  tests/test_no_decision_history_in_docs.py pins the brief at 2 dated lines, both kept in the
  unchanged verdict and delta sections. The next catalogue change (#190 step 3, the 89
  descriptions) is judged under the new hunt. The brief names
  dbt_project/models/docs/metric_rules.md as an input, which reaches main with !243, so this MR
  merges after it. docs/agent_guardrails.md and platform-reviewer.md name the agent by name only.
  No model, data, export or CI change.

decisions_taken: >
  The brief and role doc as the CPO approved them on 2026-10-03. Readings, under the CPO's
  delegation in chat on 2026-10-02 ("Readings of approved rules are yours; apply the most plausible
  one and state it in one line"): the Cursor rule .cursor/rules/agent-behavior.mdc mirrors
  working_agreement.md (CLAUDE.md, "Cursor integration"), so the section 9 line goes there too;
  the role doc's old metric table and its "next metrics" line go, because the approved role doc
  does not carry them and which metrics exist is the CPO's (#177).

decisions_reserved:
  - The routing of the football reviewer does not change.
  - Which metrics exist, their names and labels stay with #177; what a high or low value means
    stays with #187.

done_when:
  - The governance gates, pytest and the Markdown history pin pass.
  - The review cycle passes with every routed reviewer, review.md bound to --staged-hash.

amendments: (none)
