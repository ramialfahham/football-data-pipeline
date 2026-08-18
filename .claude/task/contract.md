# Task contract — record the Top players block ruling (bookkeeping only)

objective: >
  Write down two CPO decisions made in conversation on 2026-08-18, at the time they were made,
  before any build starts. No code, no model, no page — the durable record only. This exists
  because the recurring failure this session was decisions living in chat and being re-derived or
  forgotten a few messages later.
refs: `10_home.md` §0 (the four-pool design) · GAP-27/28/30/31 in `99_gaps_register.md` ·
  `design-mocks/gen_top_players.py` (the mock whose placeholder data caused the ambiguity)

scope_paths:
  - .claude/task/escalations.log
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/10_home.md

impact_map: >
  writers: none. No BigQuery, no dbt model, no export, no site file. Documentation and the
    escalation log only.

  downstream: this CHANGES WHAT FUTURE WORK IS. GAP-31 (a pooled ranking across the pool) is
    withdrawn by the ruling — the block takes each league's existing rank-1 instead — so a session
    reading the register tomorrow would otherwise scope and build a ranking nobody wants.

  layer_rules: not applicable; nothing executable is touched.

  blast_radius: three documentation files.

decisions_taken: >
  Both from the CPO in conversation, 2026-08-18, recorded here rather than paraphrased later.

  1. THE BLOCK IS ONE PLAYER PER LEAGUE, NOT A POOLED RANKING. Asked "what is happening here? We
     show the no1 from each league and then we put all these no1s into one view", and on being
     shown that the spec said pooled while the mock rendered one-per-league, the CPO ruled: "One
     per league -> yes, it's not a leaderboard in the defined pool."

  2. THE INTRO COPY MUST BE REPHRASED. "Season totals to date. Ranked across pooled leagues: …"
     describes the pooled ranking that was just ruled out. CPO: "we just need to rephrase". The
     WORDS are not written here — copy is §10, always the CPO's. What the sentence must carry
     factually: each league's leader, season-to-date, and which leagues.

amendments:
  - 2026-08-18: `decisions_reserved`'s first item — the replacement wording — is DISCHARGED, not
    still reserved. Authority chain, in order: the CPO delegated the drafting ("you rephrase"), I
    proposed one string, he approved it ("yes, record it"). Delegation-then-ratification is the
    CPO exercising §10, not the builder taking it; the record in `10_home.md` names both halves so
    my authorship is never readable as a ruling. Recorded because scope-auditor correctly FAILed
    the diff for writing the wording while the contract still said "stops there" — the two files
    asserted contradictory states of the same decision.
  - 2026-08-18: the doc sweep GREW beyond the ruling — authority: bi-analyst-reviewer FAIL, and it
    is the same failure class as this morning's. Recording "four boards" inside `10_home.md` made
    visible that the file's own §0 still carried the NINE-board and SIX-board tables, a stale §10
    gap list naming the three VOID gaps, a "fifteen boards" open question, and a board-naming
    EXAMPLE that the reduction inverted. All are the 2026-08-10 reduction never having been swept
    into this file. Striking them is finishing the record this task exists to write, not new scope
    — but it is more than the objective's literal words, so it is recorded rather than absorbed.

decisions_reserved:
  - ~~The replacement wording itself.~~ DISCHARGED — see the amendment above.
  - Whether ordering the seven league-winners by value belongs in the mart or the page. The
    2026-08-16 Ruling 4 precedent ("the mart carries facts, the spec declares the ORDER BY") points
    at the page, but that ruling was about competitions, not players — not assumed, not decided.
  - Everything about BUILDING the block. This task writes nothing executable.

done_when:
  - `escalations.log` carries both rulings, dated, with the CPO's words.
  - GAP-31 is withdrawn in the register with the ruling as the reason, following the existing
    GAP-04 withdrawal convention (strikethrough + status + reason), NOT deleted.
  - GAP-27/28/30 confirmed still live, since the ruling does not touch them.
  - `10_home.md` no longer presents "pooled across the leagues of one pool" as current.
