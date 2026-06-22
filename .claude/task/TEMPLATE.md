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

# REQUIRED when scope_paths touches the STRUCTURAL SURFACE — a raw writer
# (ingestion/**), a dbt model (dbt_project/models/**), or consumption
# (scripts/export_*.py, site*/). The contract gate DENIES the first structural edit
# until this is present. Trace BEFORE you build, and paste EVIDENCE, not assertion
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
