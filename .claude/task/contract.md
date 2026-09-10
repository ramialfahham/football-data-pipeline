# Task contract — design mocks into the repo, and their rulings into the wireframe

objective: >
  Bring the design-mock GENERATORS and CHECKS into the repo, and transcribe the CPO's 2026-08-10
  home-page rulings out of a Python docstring and into the wireframe that governs the page. The
  generated HTML stays out.

refs: >
  `design-mocks/README.md` (outside the repo) — the mock store and its own account of what it is.
  `docs/wireframes/10_home.md` §0 — the home page composition; already cites the generators.
  `docs/wireframes/99_gaps_register.md` GAP-24 — VOIDED on the authority of a file outside the repo.
  `.claude/task/escalations.log` `2026-09-10 chore/design-mocks-into-the-repo` — the two CPO
  rulings this task rests on: the generators come into the repo, and the team boards have ONE value
  column. ⚠ That entry was written only after `scope-auditor` FAILed the branch for citing his
  "yes" and "fix it" with nothing logged behind them — the same defect as the previous MR, and
  worse here because one of the citations was in a permanent checked-in README rather than a task
  contract.

scope_paths:
  - design-mocks/*.py
  - design-mocks/*.csv
  - design-mocks/README.md
  - .gitignore
  - docs/wireframes/10_home.md
  - docs/wireframes/99_gaps_register.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log

impact_map: >
  writers: no dbt model, seed, macro or test. No mart, no export, no site source. The generators
    READ `dbt_project/seeds/metric_catalogue.csv` and `site_v2/src/styles/system.css`; they write
    only their own HTML.

  downstream: nothing consumes the generators. Three repo documents CITE them
    (`10_home.md:150`, `10_home.md:184`, `99_gaps_register.md:35`); after this the citations point
    at in-repo paths and at the transcribed rulings.

  blast_radius: the site build, the export and CI are untouched — no file any job reads changes.
    `.gitignore` gains one line so the ~950 KB of generated HTML cannot be committed. The repo
    grows by ~330 KB of Python.

  deploy_order: none.

acceptance_criteria:
  - Every `.py` and `.csv` in the mock store is tracked in the repo, and no `.html` is.
  - `python design-mocks/gen_top_players.py` and `gen_top_teams.py` RUN — today both hard-fail on a
    missing catalogue path — and `check_players.py` / `check_teams.py` pass against their output.
  - The regenerated mocks are byte-identical in structure to the reviewed ones: 4 boards, 28 rows,
    28 value cells each.
  - Every 2026-08-10 ruling now in a generator docstring is stated in `docs/wireframes/10_home.md`,
    with its reason where the docstring gives one.
  - `99_gaps_register.md`'s GAP-24 void cites the wireframe, not a file outside the repo.
  - No generator docstring still claims team boards carry two value columns.
  - `python -m pytest tests/ -q` and `cd site_v2 && npm test` stay green (nothing they read changes).

decisions_taken: >
  GENERATORS AND CHECKS IN, GENERATED HTML OUT. The Python is source and is COUPLED to the repo —
  it reads the metric catalogue and `system.css`. That coupling is what broke: versioned apart from
  its dependency, the dependency moved and the tooling died. The HTML is build output.

  THE `REPO` CONSTANT POINTS AT THIS REPO. It currently points at `D:/Projects/fdp-product`, which
  is not a git repository and has no `dbt_project/` at all — so every generator raises
  FileNotFoundError today, verified by running one. The README's claim that the mocks "cannot drift
  from the shipped design system or invent a metric label" has been false since the store was saved.
  Resolved by deriving the path from the file's own location instead of hardcoding it.

  THE RULINGS MOVE, THE MOCKS DO NOT. A ruling recorded in a script's docstring is unfindable even
  when the script runs. `10_home.md` is where someone looks.

  THE TWO-COLUMN CONTRADICTION IS A STALE SENTENCE, NOT A DESIGN DIVERGENCE.
  `gen_top_teams.py:84` says "two value columns throughout"; line 311 of the same file says one.
  The reviewed mock settles it: 28 rows, 28 value cells, 4 boards — ONE value column, matching what
  shipped. The sentence is a leftover from the draft the same-day ruling replaced. Nothing built
  needs changing.

  ⚠ "NOT IN THE REPO, AND DELIBERATELY SO" WAS MINE, NOT THE CPO'S. The README says it and I cited
  it back to him as his decision; he did not make it, and the README's own next sentence says
  "committing them is a separate decision". Recorded because attributing an unmade ruling is the
  failure this repo has logged repeatedly, and this time it nearly settled a question in the wrong
  direction.

  THRESHOLD — NEW MECHANISM: none. No new gate, dependency, route or CI job. A directory of
  design tooling that runs by hand.
  THRESHOLD — RECURRING COST: none. Nothing new runs on a schedule or in CI.

decisions_reserved:
  - Whether the mock CHECKS should run in CI. They are hand-run today and stay that way here;
    wiring them to a job is a new gate and its own decision.
  - Whether the older surfaces' rulings (#47, #50, #52, #54 — competitions index, competition hub,
    next-matches block, interaction standard) also need transcribing. This task covers the home
    page, which is the one with a live citation and a voided GAP depending on it.

done_when:
  - Both home generators run from a clean checkout and their checks pass.
  - `git status` shows no untracked `.html` under `design-mocks/`.
  - The offline gate set is green.

amendments:
  - none yet
