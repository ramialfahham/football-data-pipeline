# Task contract — #153, step one: the four review generators and their data pulls into `design-mocks/`

objective: >
  The four renders the CPO approved on #129 on 2026-09-16 (`competition-overview`,
  `competition-matchdays`, `competition-rankings`, `home`, all `_2026-09-16_01.html`) were made by
  four generators in a session scratchpad, reading five BigQuery pulls that live only there.
  Bring the generators and the pulls into `design-mocks/`, where they version with the stylesheet
  and the catalogue they read, so the approved design is reproducible from the repo. This is the
  last checklist item of #153 and the first thing #153 asks for; the mechanism (the inventory,
  the check, the lint, the naming rule) is planned separately after this lands.

refs: >
  #153 (the last "What exactly" item: the four renders and their generators brought into
  `design-mocks/`); #129 (the approved design they render); `.claude/active_work.md` "#153
  brings them into `design-mocks/`; do that before anything else is rendered";
  `design-mocks/README.md` "Anything that reads the repo has to version with the repo".

scope_paths:
  - design-mocks/gen_competition_matchdays.py
  - design-mocks/gen_competition_teams.py
  - design-mocks/gen_overview_after_teams.py
  - design-mocks/gen_home_with_rules.py
  - design-mocks/bl1_fixtures.json
  - design-mocks/bl1_md3_shots.json
  - design-mocks/bl1_team_metrics.json
  - design-mocks/bl1_team_cards.json
  - design-mocks/bl1_player_metrics.json
  - design-mocks/competition-overview_2026-09-16_01.html
  - design-mocks/competition-matchdays_2026-09-16_01.html
  - design-mocks/competition-rankings_2026-09-16_01.html
  - design-mocks/home_2026-09-16_01.html
  - design-mocks/README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  The generators are copied as they ran, with four adaptations and nothing else: the repo root
  derived from the file's own location instead of a hardcoded drive path (the README's rule for
  every generator in the folder); the comment lines carrying a date or the product owner's
  title rewritten to say only what the line is for (the comment-history gate and
  `tests/test_no_decision_history_in_code.py` hold the tree at zero such lines), which also
  takes the date out of the Overview mock's `<title>` and out of one CSS comment in the Home
  overlay; the eight findings of CI's `ruff` job removed (two unused imports, five unused
  locals, one lambda made a `def`) together with one dead function the Rankings generator no
  longer called (`deserved_html`, the boards that moved to the Overview) and its payload read;
  and the Rankings generator's docstring, which still said "Teams tab" and described those
  moved boards, rewritten to what the file renders. None of this changes a rendered byte
  except the title and the comment. The data pulls are
  committed as the JSON the `bq` CLI wrote, unchanged. The four renders of record are copied
  onto disk beside them; `design-mocks/*.html` is gitignored, so they are not in the commit —
  whether review renders are tracked is the naming-rule item of #153 and is put to the CPO in
  that plan, not decided here. The README gains a section naming the four generators, the
  five pulls (what each holds and that they are real prod data of 2026-09-16), how to run them,
  and corrects its closing paragraph, which says nothing in the folder was run against
  BigQuery. No new mechanism, no recurring cost, no protected path.

decisions_reserved:
  - none: nothing here is a design decision — the design is approved on #129 and the generators
    render it unchanged; the one open question this raises (tracking review renders in git) is
    reserved for the #153 plan, where it is put to the CPO with a recommendation.

done_when:
  - Each of the four generators runs from `design-mocks/` and writes a file; the Matchdays and
    Rankings outputs are byte-identical to the renders of record; the Overview output differs
    from its render of record only in the `<title>` line and the Home output only in one CSS
    comment line.
  - `python -m pytest tests/test_no_decision_history_in_code.py -q` green; `ruff check
    design-mocks --config .ruff-ci.toml` clean.
  - `python .claude/hooks/comment_history_gate.py` flags no line in the four generators.
  - The offline gates (`validate-local`) green; the MR open against `main` with `Closes` not set
    (this is one item of #153, not the whole issue).

amendments: (none)
