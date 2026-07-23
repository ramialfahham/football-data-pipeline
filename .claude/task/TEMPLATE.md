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
# (.claude/hooks/, .claude/agents/, .claude/commands/, .claude/settings.json,
# .claude/review_routing.json, .mcp.json, .cursor/mcp.json, .github/workflows/).
# Quote the approval. A protected path ALSO requires an impact_map below (2026-07-22):
# the override answers "may you", the map answers "do you know what breaks".
# protected_override: >
#   <CPO approval reference>

# REQUIRED when scope_paths touches the STRUCTURAL SURFACE — a raw writer
# (ingestion/**), a dbt model (dbt_project/models/**), consumption
# (scripts/export_*.py, site*/), or ANY PROTECTED PATH (.claude/hooks/,
# .claude/agents/, .claude/commands/, .claude/settings.json,
# .claude/review_routing.json, .mcp.json, .cursor/mcp.json, .github/workflows/ —
# added 2026-07-22, because a guard's blast radius is every future task in the
# repo, wider than most models). The contract gate DENIES the first such edit
# until this is present.
# For a PROTECTED path, trace what depends on the guard instead of table lineage:
# which events fire it, what else imports from it, what stops being enforced if it
# is wrong, and what happens on failure.
# The words "none", "n/a", "tbd" and a bare ">" do NOT satisfy it. Trace BEFORE you build, and paste EVIDENCE, not assertion
# (the actual `dbt ls --select <model>+` / dbt-MCP lineage output and the RAW count —
# do not claim them from memory). Trivial/leaf/cosmetic changes use a one-line
# evidenced short-form (e.g. "leaf mart; `dbt ls --select mart_x+` → no downstream
# models; cosmetic label change"). A dishonest "trivial" tag is a reviewer FAIL (A6).
# Omit this key entirely when no structural path is in scope.
# impact_map: >
#   writers: <every loader/model that writes the table/model being changed>
#   downstream: <lineage to marts/consumption — PASTE `dbt ls --select <model>+`
#     or the dbt-MCP get_lineage_dev output>
#   layer_rules: <the CI-enforced layer rules that apply (check_layer_contract)>
#   deploy_order: <shared-warehouse migration ordering — does this break the
#     deployed model until merge? how is it sequenced around the 04:00 nightly?>
#   blast_radius: <which marts/numbers change, or "none" + the RAW count / leaf evidence>

# NORM, not a gated field: on a structural change, gather the domain knowledge
# BEFORE building (a reviewer role, a doc, a data check) rather than discovering it
# in review. Note it in objective/refs if it shaped the work. (This was a machine-
# gated `consulted:` field for a few days and was demoted to a habit.)

decisions_taken: >
  <what this contract pre-approves, quoting the CPO ruling it rests on>

# decisions_reserved is MACHINE-CHECKED if this task publishes an Artifact (a mockup,
# a design, any page): the gate denies the publish unless this holds real content.
# The placeholder below and a bare `- none` BOTH fail it, deliberately — publishing a
# design IS the product decision, so "what does this page show" belongs here as a §10
# question, not in the drawing. If nothing is genuinely open, say so as a sentence
# someone can check: `- none: the design is CPO-approved as mock <id> and this
# publishes it unchanged`.
decisions_reserved:
  - <every known ambiguity / CPO-class question (§10) that may surface;
     escalate each blinded (§11) — never decide>

done_when:
  - <mechanical verification steps: commands, tests, expected outputs>

amendments: (none)
# On amendment (clean tree only):
#   - <date>: + <path> — authority: <CPO answer / standing rule>; content: <what>
