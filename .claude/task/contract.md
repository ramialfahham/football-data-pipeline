# Task contract — the design chain and the ruling log, in the file every session reads

objective: >
  `CLAUDE.md` is read at the start of every session and its "Authoritative docs" table is the map
  of what to read before deciding. That table names the data contract, the layer rules, the metric
  layer, ops, CI and the site IA — and mentions the DESIGN chain nowhere, and the CPO ruling log
  nowhere. Add both, and complete the design chain's own precedence statement so the map has
  something to point AT.

refs: >
  Measured, not asserted: `grep -c` over `CLAUDE.md` returns **0** for `wireframes`,
  `metrics_display`, `ui_design_brief`, `design-mocks` AND `escalations.log`.
  `docs/wireframes/00_overview.md` already declares a partial precedence (brief = look-and-feel,
  `site_architecture.md` = IA/URLs, wireframes = field binding) that omits
  `content_architecture.md`, `metrics_display.md` and the mock/issue layer.
  `docs/working_agreement.md` §11 designates `escalations.log` as the durable ruling record.
  `.claude/task/escalations.log` `2026-09-10 chore/authority-map-in-claude-md` — the CPO's
  instruction to fix the context engineering, his approval of the six-step plan ("go"), and the
  steps themselves. This is step 2; step 1 merged as `!169`.
  ⚠ That entry was written only after `scope-auditor` FAILed this branch for citing "the plan the
  CPO asked for" with nothing logged behind it — the third branch running to make the same mistake,
  this time disguised as citing a plan rather than a ruling.

scope_paths:
  - CLAUDE.md
  - docs/wireframes/00_overview.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log

impact_map: >
  writers: no code. Two markdown files.

  downstream: `CLAUDE.md` is loaded by every session and by Cursor; `00_overview.md` is read before
    any screen is designed or built. Nothing machine-reads either.

  blast_radius: no model, mart, export, site source, test or gate changes. No CI job reads these
    files. The change is what a human or an agent is TOLD to read, which is the whole point —
    the failure it addresses (a page rebuilt without reading its design) is not machine-detectable.

  deploy_order: none.

acceptance_criteria:
  - `CLAUDE.md`'s authority table names the design chain and points at ONE place for its precedence,
    rather than restating the precedence itself.
  - `CLAUDE.md` names `.claude/task/escalations.log` as the durable record of CPO rulings.
  - `docs/wireframes/00_overview.md`'s reading order covers every document that governs what a
    screen shows — `content_architecture.md`, `metrics_display.md`, the mock/issue layer, AND
    `ui_design_brief.md` §6, which is a per-screen FIELD contract and not look-and-feel — and
    restates the existing escalation rule without weakening it.
    ⚠ §6 was missed on the first pass and `bi-analyst-reviewer` FAILed it, with the concrete cost:
    `04_competition_hub.md` does not exist, so §6.5 is the ONLY live field contract for that screen,
    and a table calling the brief "look-and-feel" would send a reader straight past it.
  - The PRECEDENCE RULE is stated in exactly one file. Measured: `grep -ci 'which wins|beats
    every|on conflict'` returns 0 for `CLAUDE.md` and non-zero for `00_overview.md`.
    ⚠ Deliberately NOT "no fact appears twice" — the chain's member LIST does appear in both, and
    `decisions_taken` records why that trade was taken rather than hidden.
  - `grep -c` for each of the five terms over `CLAUDE.md` is non-zero.

decisions_taken: >
  THE PRECEDENCE LIVES IN `00_overview.md`, NOT IN `CLAUDE.md`. `CLAUDE.md` gets a row pointing at
  it. Stating it in both is the duplication this whole exercise exists to remove — a corrected
  precedence would then need sweeping in two places, which is how every stale claim on the last two
  MRs got there.

  ⚠ `00_overview.md` GOVERNS A DIFFERENT AXIS FROM THE MOCKS, and `bi-analyst-reviewer` corrected me
  on this during `!169`: it binds a screen's blocks to real exported FIELDS, while the mock/issue
  layer settles what the screen LOOKS like and which boards it carries. They do not conflict, so the
  statement must place the mock layer alongside rather than above or below the field binding.

  ⛔ "NOTHING IS DELETED" WAS FALSE, AND `scope-auditor` CAUGHT IT AS A §10 RULE CHANGE.
  `00_overview.md` said **"Conflicts escalate to the CPO."** — absolute. My replacement read "a CPO
  ruling beats every document here; below that, the more specific and more recent wins, and anything
  still unresolved escalates". That is not an addition. It invents an auto-resolution and narrows
  when the CPO is consulted, which is a rule extension and his alone. Reverted: the rule is restored
  verbatim in force, with no tie-breaker, and the only thing added is that a ruling ALREADY in
  `escalations.log` is not a conflict but the answer — which changes nothing about escalation.
  ⚠ The wording that slipped through is the kind that reads like tidying. "More specific and more
  recent wins" is a reasonable-sounding default in the abstract; it is a decision about who decides.

  Otherwise nothing is deleted: every existing row and sentence stands, and the rest of the change
  is addition where there was absence.

  ⚠ A DUPLICATION IS ACCEPTED ON PURPOSE, AND IT IS THE ONE A REVIEWER SHOULD PUSH ON. The chain's
  MEMBER LIST now appears twice: named in `CLAUDE.md`'s row and tabulated in `00_overview.md`. A
  document joining the chain therefore needs both updated. The alternative — `CLAUDE.md` naming only
  `00_overview.md` — was written first and reverted, because it made `metrics_display`,
  `ui_design_brief` and `design-mocks` return **0** on a grep of the always-loaded file, and a
  pointer only helps a reader who follows it. That is exactly what failed on #41: the wireframes
  were reachable and I did not reach them. What is NOT duplicated is the RULE — "which document
  wins" appears 0 times in `CLAUDE.md` and only in `00_overview.md`, verified by grep. A list of
  filenames going stale is visible; a precedence rule going stale in two places is the failure mode
  that cost this repo two MRs.

  ⚠ I TRIMMED MY OWN ADDITIONS BEFORE COMMITTING, and it is worth recording why. The first version
  put a six-line explanation of WHY these rows exist into `CLAUDE.md` — a file loaded on every
  session, where narrative costs tokens forever and git already holds the history. Cut to one
  sentence. Net: `CLAUDE.md` +5 lines. The same trim was applied to `00_overview.md`.

  THRESHOLD — NEW MECHANISM: none. No gate, no dependency, no CI change.
  THRESHOLD — RECURRING COST: none.

decisions_reserved:
  - ⏳ WHETHER `ui_design_brief.md` §6.1, §6.2 AND §6.4 SHOULD BE MARKED SUPERSEDED. All three have
    wireframes and carry no marker; §6.3 has one and points at `10_home.md`. Marking three sections
    superseded decides which document binds a screen — the CPO's, not mine. Surfaced by
    `bi-analyst-reviewer`, recorded rather than resolved.
  - Whether `CLAUDE.md`'s "Operational notes" section (65 lines of traps its own header says were
    moved out of `active_work.md` because that file overflows) should move somewhere else. It is
    the same disease and it is in this file, but relocating it is its own decision.
  - Steps 3-6 of the plan (splitting `escalations.log`, giving reviewers a non-code place to read
    reasoning, stripping decision history from code, memory + budgets).

done_when:
  - The five grep counts are non-zero and the precedence statement is complete.
  - The offline gate set is green (no code changes, so this is a formality — stated so it is run).

amendments:
  - none yet
