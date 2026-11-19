# Task contract — the skill that researches the daily provider-error list

objective: >
  Issue #262, How step 1: a skill that holds the source rules, the allowed sites and the stop
  conditions for researching the rows of mart_competition_research_list. The skill reads the list,
  researches each match with two separate reads of allowed sites, compares the reads with each
  other and with the provider's own ids, and reports the proposed seed rows. It writes no seed
  file, commits nothing and opens no merge request: how a fix lands is not decided. A desktop-app
  scheduled task runs it each morning; this MR builds the skill only.

refs: >
  #262 What exactly boxes 3, 5 and 6 and How steps 1 and 4; source rules and the stopped sites:
  #176 (approved in chat, 2026-11-06); the trial of 2026-11-18 on matches already researched
  (error rate per source, tokens per read) reported to the coordinating session; how the routine
  runs: a Claude desktop app scheduled task, no CI job, no API key, no GitLab token (approved in
  chat, 2026-11-19).

scope_paths:
  - .claude/skills/research-provider-errors/SKILL.md
  - docs/agent_guardrails.md
  - .claude/task/262-research-skill/contract.md
  - .claude/task/262-research-skill/review.md
  - .claude/task/262-research-skill/review_input.patch

approved_design:
  - none: no page output changes; the skill is read by the research routine, not by the site

depends_on:
  - none: builds on the merged research list (mart_competition_research_list) only
shared_files:
  - none: no design baseline, chart manifest or chart pin changes

decisions_taken: >
  Ruled by the coordinating session on 2026-11-19 under #262. (1) The sites the skill may read
  are the five script-rendered sites read through the desktop app's browser (K League, Ligue 1,
  Premier League, Liga Profesional, Liga Portugal) and the sources read by plain fetch in the
  trial: the J League data site, tff.org, dfb.de, cafonline.com, concacaf.com and the news
  outlets read in the trial. Each site's terms and robots.txt were read once before its first
  read and none bans automated reading. fff.fr and conmebol.com refused the fetch with a 403 and
  are not read by any other route. Ekstraklasa and Veikkausliiga are left out until the CPO rules.
  The nine stopped sites of #176 are never read. (2) Two separate reads per match by two
  subagents of this session; reads that disagree go no further. A player's team and id come from
  the provider's own data for the match, never from a page's layout. (3) The routine runs as a
  scheduled task of the desktop app on the CPO's machine and the list is cumulative, so a missed
  day carries over. (4) A seed fix is reported as proposed rows; the steps that land a fix, and
  the steps for a standings row, are stubs that stop and report. (5) Aggregator-cited seed rows
  are not researched. (6) docs/agent_guardrails.md gains one row in its project-skills table
  that lists this skill; the exact text was approved in chat on 2026-11-19 and the edit adds no
  rule. Threshold declarations: no new mechanism is built here (the scheduled task
  is created after the merge, by the coordinating session, with the CPO's yes). Recurring cost:
  about 2.5M tokens a week on the Claude plan, measured in the trial; no API key; BigQuery about
  1 MB a day for the list read.

decisions_reserved:
  - How a seed fix lands without a merge by the CPO, and the change to the merge rule in docs/working_agreement.md that it needs: the CPO's, with the exact text approved first.
  - What a standings or points mismatch withholds, and so the research steps for a standings row.
  - How many matches a run researches: a cost decision, set by the CPO in the scheduled task's prompt.
  - Creating the scheduled task: not built here.
  - The weekly report of fixed and open items.

done_when:
  - The skill file passes tests/test_sentence_length_in_docs.py and tests/test_no_decision_history_in_docs.py.
  - The full pytest suite passes, bar the machine-only line-ending test.
  - The MR pipeline is green and `python scripts/merge_ready.py <iid>` says ready.
