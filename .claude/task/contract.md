# Task contract — add the SEO Expert role (brief + reviewer agent)

> Written on a CLEAN tree, branch `feat/seo-expert-role` off `main` (`6266b8f`).
> Adds a role brief and its reviewer agent. Routing is NOT changed here — that is a separate
> governance ask (see decisions_reserved).

objective: >
  Create the missing SEO Expert role as two artefacts: the role brief (docs/roles/seo_expert.md) and
  its adversarial reviewer agent (.claude/agents/seo-expert-reviewer.md), matching the shape of the
  existing briefs (docs/roles/bi_analyst.md, growth_expert.md) and agents
  (.claude/agents/bi-analyst-reviewer.md). The brief owns organic acquisition: URL/IA structure,
  indexation, metadata uniqueness, structured data, the internal-link graph, anti-thin-content and
  crawlability. It explicitly bounds against growth_expert.md, which owns retention and sharing.

refs: >
  CPO, 2026-07-27, this session: "It seems we need an expert SEO role in the project, that helps
  achieveing the goal. No dead document." and, on the proposal to write the brief + agent and bring
  the routing change as a governance ask: "go ahead".

  The gap is concrete and verified this session: site_architecture.md opens by describing v2 as a
  "programmatic content platform" producing "tens of thousands of SEO-relevant pages", and §6 defines
  a whole SEO surface owned by #369 — yet none of the 11 existing role briefs owns SEO.
  growth_expert.md, the closest, covers retention/sharing/habit/word-of-mouth and does not mention
  organic search once.

  "No dead document" is the operative constraint: review_routing.json's own _doc names three briefs
  as "dormant-but-undefined" (ui-expert, data-journalist, legal-counsel) — briefs that exist and
  never fire. Routing is what makes a role live, and routing is a PROTECTED file.

scope_paths:
  - docs/roles/seo_expert.md
  - .claude/agents/seo-expert-reviewer.md

protected_override: >
  `.claude/agents/**` is a PROTECTED governance path (the guards themselves). The CPO approved
  creating this agent explicitly and specifically, in this session, answering the proposal
  "Want me to write the brief and the agent now, and bring you the routing change as the governance
  ask?" with "go ahead".

  SCOPE OF THE OVERRIDE — deliberately narrow. It authorises creating ONE new agent file,
  `.claude/agents/seo-expert-reviewer.md`. It does NOT authorise editing any existing agent, and it
  does NOT authorise touching `.claude/review_routing.json`, which the same CPO message kept as a
  separate governance ask that is still outstanding. The new agent is therefore INERT on merge: it
  is absent from the routing table, so the commit gate never requires its verdict and it fires on
  no diff. Making it live is the follow-up governance ask.

impact_map: >
  Blast radius of adding ONE file to `.claude/agents/` (traced, not assumed):

  1. **`tests/test_governance_hooks.py::test_every_reviewer_brief_carries_the_identical_delta_section`
     — the real dependency, and it BITES.** It globs the live `.claude/agents/*.md` directory (a
     deliberate choice over a hand list, review-economics 2026-07-22), asserts at least 6 briefs,
     and asserts that the text following `## Delta re-review` is **byte-identical across every
     brief**. Adding a 7th file makes it a participant immediately. A paraphrased delta section
     turns CI red. Mitigation: the new agent's delta section is copied byte-for-byte from an
     existing brief and verified by running the test before commit — not retyped.
  2. **`.claude/hooks/task_contract_gate.py`** lists `.claude/agents/` in `PROTECTED_PREFIXES`, which
     is what gated this edit. Adding a file does not change the gate's behaviour for any other path.
  3. **`scripts/check_task_artifacts.py` + the commit gate** compute the REQUIRED reviewer set from
     `.claude/review_routing.json` — **not** from the agents directory. An agent absent from routing
     is therefore never required by any commit or CI run. This is why the new file is inert: it
     changes no required reviewer set on any existing or future diff.
  4. **The harness** discovers agent types from this directory, so `seo-expert-reviewer` becomes
     selectable by the Agent tool. Nothing invokes it automatically.

  **What stops being enforced if it is wrong: nothing.** The file is inert until routed, so a
  mistake in it cannot weaken an existing guard or let a bad diff through. The failure mode is the
  opposite one — a red CI via dependency 1.

  **On failure:** the test fails on the PR before merge; no runtime, pipeline or site impact; no
  reviewer set changes anywhere. Revert is deleting one file.

decisions_taken: >
  None that are product decisions. The brief RECORDS existing locked constraints (site_architecture
  §2 no-thin-pages, §3 slug stability and locale prefixing, §6 SEO surface; content_architecture §5
  navigation graph) and states a three-part test for when a view earns its own URL. That test is
  written as this role's PRINCIPLE for judging, not as a ruling on any current page — the live
  tab-vs-URL question is explicitly recorded as OPEN in the brief's "Current responsibility".

decisions_reserved:
  - **Routing is NOT touched here.** Adding seo-expert-reviewer to .claude/review_routing.json is a
    governance event on a PROTECTED file and needs CPO approval with protected_override. Without it
    the role is a dead document by construction — this is the follow-up ask, not an omission.
  - Whether a tab earns its own URL (site_architecture §3 + content_architecture §2 define one URL
    per entity; wireframes 12/13 define /stats/ and /career/ sub-paths — the two CONTRADICT). The
    brief records the conflict; it does not resolve it. Resolving it amends a locked scheme (§10).
  - Whether the tab sets reconcile to content_architecture §4 (Player = Overview/Matches/Stats/
    Career; Team = Overview/Matches/Stats/Squad/History) versus the three shipped/designed. Recorded
    as open in the brief, not decided.

done_when:
  - docs/roles/seo_expert.md exists, matches the established brief shape, is specific to THIS project
    (cites the real locked constraints and the real open conflicts), and bounds against growth_expert.
  - .claude/agents/seo-expert-reviewer.md exists, matches the established agent shape (frontmatter
    name/description/tools/model/effort; Inputs; hunt list; verdict rules; exact output format;
    delta re-review clause), and is read-only.
  - ONE commit; review cycle run (these paths are not artifact-exempt); pushed with an explicit
    refspec; PR opened.
  - The routing change is brought to the CPO as an explicit governance ask, not applied.

amendments:
  - 2026-07-27: contract rewritten from the previous task (handover bookkeeping, merged as PR #837)
    to this task, on a clean tree at main 6266b8f. CPO authority: "go ahead" (this session), on the
    proposal to write the brief and the agent and bring routing separately.
