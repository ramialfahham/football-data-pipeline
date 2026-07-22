# Task contract — rewrite the handover as current state, not accumulated history

> Written on a CLEAN tree (branch `docs/handover-retrospective` off main @ 0ff5037).
> CPO-directed 2026-07-22 in a retrospective session that produced six conclusions, a
> licensing finding, and two product decisions. None of it exists anywhere outside that
> chat. See [[feedback-handover-discipline]] [[feedback-doc-clutter-discipline]].

objective: >
  `.claude/active_work.md` is 112,233 characters. The SessionStart hook that is supposed to
  deliver it caps its injection at 16,000 bytes, so even if it were wired (it is not — no
  SessionStart hook exists in `.claude/settings.json`, `.claude/settings.local.json`, or the
  user-level settings) it would deliver the first 14% and truncate silently. The Read tool
  hits the same wall. The single most important document in the project cannot be read by
  the mechanism meant to read it.

  Rewrite it as CURRENT STATE ONLY, under 16,000 characters, and record what this session
  settled: the retrospective conclusions, the API-Football licensing findings, the two
  product decisions (no player photographs; crests stay), the five launch groups that answer
  "where do we stand", and the agreed sequence of work.

  The ~85% that is explicitly labelled history is DELETED, not moved to an archive file.
  Git preserves it. An archive nobody opens is the same tier-three problem the retrospective
  identified, in a new file.

refs: >
  Verified this session at source, not recalled:
  - `wc -c .claude/active_work.md` -> 112233. `handover_in.py` MAX_BYTES = 16000.
  - No `SessionStart` key in either project settings file; the user-level
    `~/.claude/settings.json` has no `hooks` key at all. The hook script exists and nothing
    runs it. Empirically confirmed: this session did not receive the handover injection.
  - API-Football terms (read in full, 2026-07-22, last updated 2025-05-21): websites are an
    expected use ("create different projects such as applications, websites..."); the only
    hard prohibition is RESELLING the data; they grant no publication licence and direct
    users to the leagues/federations; logos and images are "solely for identification and
    descriptive purposes", they claim no rights over them, and use may require club
    authorisation; a rights-holder complaint lets them terminate API access immediately
    without refund.
  - `site_v2` DOES make third-party requests today: the committed sample data carries
    `media.api-sports.io` URLs for team crests and player photos, and `Crest.astro` +
    `PlayerRow.astro` render both as `<img src>`. An earlier claim in this session that it
    made none was WRONG (it grepped code files, not data files) and is corrected here.
  - Branch state: `docs/handover-reset` is merged (main @ 0ff5037); only PR #673 is open
    and it is superseded.

scope_paths:
  - .claude/active_work.md

decisions_taken: >
  (1) NO PLAYER PHOTOGRAPHS; CRESTS STAY. CPO 2026-07-22, verbatim: "OK no photos", answering
      the recommendation "ship without player photographs, keep crests". Rationale put to him
      and accepted: photographs carry image rights over real people on top of photo copyright,
      add the most legal exposure and the least information, and the player page is not
      designed yet so deciding now costs nothing; crests are woven through 13+ marts and the
      export, so removing them later is expensive, and the provider's own framing is
      "identification and descriptive purposes".
  (2) QUALITY OVER SPEED. CPO 2026-07-22: "I prioritize quality over speed. If me make it in
      3 weeks it's ok as well. But 2 weeks remains our goal."
  (3) THE WORK SEQUENCE, and it REORDERS the old plan. The superseded handover named "finish the
      player page design" as step 1. The new order is: licensing check (DONE this session) -> one
      governance task for the guards and agents -> build the TEAM page. The player page moves
      behind both. Authority: the sequence was put to the CPO in full ("First, the licensing
      check... Second, one governance task... Third, build the team page") and closed with "Give me
      a go on the sequence and I will put the licensing check into plan mode." CPO 2026-07-22
      answered: "go". The reorder follows from two things he settled the same day: build approved
      designs rather than produce new ones (the team page is approved and unbuilt; the player page
      mock is NOT approved), and the player page's open content questions are to be answered with
      the consultant agents, which do not exist yet.
  This task WRITES DOWN those decisions. It does not make any.

decisions_reserved:
  - Who the site operator is and what address the imprint carries. Blocks publication.
  - Hosting. GitHub Pages recommendation withdrawn; nothing chosen.
  - Whether the leagues/federations question needs a real lawyer before publishing.
  - The exact definition of "done" for each of the five launch groups.

done_when:
  - `.claude/active_work.md` is under 16,000 characters (`wc -c`).
  - It carries: the goal, the five launch groups with status, the 2026-07-22 decisions,
    the retrospective conclusions, the agreed sequence, and the standing do-nots.
  - No section labelled history or superseded remains.
  - Committed on `docs/handover-retrospective` and pushed with an explicit refspec; PR opened.

amendments: (none)
