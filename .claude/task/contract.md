# Task contract — the design check sees the search box; the handover leaves the branches

objective: >
  Two fixes the CPO asked to ride together as one cleanup. (1) The measured design check renders a
  third, wide screen (1010px, where the header's search field appears) and measures the search
  field and the small search button, so a broken search box fails `validate:ui`; whether the
  header fits its row is measured too, reported and not failing. (2) The session handover moves
  out of the repository into GitLab issue #157, read at session start by the session-start hook,
  so it no longer rides whichever branch is checked out. No page, route, payload, mart or rule of
  the site changes.

refs: >
  The CPO's session-opening message, 2026-09-23: "the measured design check only renders 375 and
  700 px, and the search box only exists on desktop, so the check has never seen it. A broken
  search box would pass." and "my session handover travels with whatever code branch is open, so
  it goes stale when a sibling branch merges. It cost a dropped commit on 2026-09-23. Give it a
  home that does not ride a feature branch." Both "can ride along as one cleanup, not their own
  ceremony".
  The plan he approved the same day chose the home (a GitLab issue, kept closed, with the last
  fetched copy saved on this machine for when GitLab is down) over the alternative (a file on
  this machine outside git), and named the width, the three measurements and the cost (about 50%
  more renders).
  Both gaps were recorded on !219 and in the handover: `.searchbox` hidden at both widths the
  check measures; `!218`'s handover commit dropped in a rebase for naming both MRs as open.

scope_paths:
  - scripts/design_inventory.py
  - scripts/check_design_inventory.py
  - tests/test_design_inventory.py
  - tests/fixtures/design_inventory/green.html
  - tests/fixtures/design_inventory/red.html
  - docs/wireframes/block_standard.md
  - design-mocks/README.md
  - .claude/skills/validate-local/SKILL.md
  - .claude/hooks/handover_in.py
  - .claude/commands/status.md
  - tests/test_governance_hooks.py
  - tests/test_no_dead_issue_refs.py
  - design-mocks/check_handover.py
  - design-mocks/section_sizes.py
  - scripts/sync_metric_docs_blocks.py
  - .claude/active_work.md
  - .gitignore
  - CLAUDE.md
  - docs/agent_guardrails.md
  - scripts/snapshot_tracker.py
  - docs/tracker/gitlab_snapshot.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

protected_override: >
  Two protected paths, `.claude/hooks/handover_in.py` and `.claude/commands/status.md`. The
  approval is quoted with its date and source in decisions_taken below, and repeated on the MR
  head's Locked files line.

impact_map: >
  THE HOOK. `.claude/hooks/handover_in.py` fires on every SessionStart (`.claude/settings.json`,
  the only SessionStart entry; `settings.json` itself is untouched). Nothing imports it; it is run
  by path. It enforces nothing: it injects context, and today it reads
  `<CLAUDE_PROJECT_DIR>/.claude/active_work.md` from the working tree, so the handover a session
  sees is the checked-out branch's copy. After: it reads the description of issue #157 through
  `glab api projects/85168767/issues/157` (the numeric project id, so the coming group move does
  not break it), with a timeout, decoding UTF-8 bytes itself (the cp1252 trap); writes that text
  to the gitignored `.claude/handover.cache.md`; and when GitLab or `glab` is unavailable, injects
  the cache labelled with the time it was saved, or says plainly that no handover could be read.
  The 16,000-character cap and the truncation warning are kept. On failure it still fails open
  (no output, exit 0). What breaks if it is wrong: a session starts without its handover, which
  the no-handover message makes visible. `glab auth` is only read, never touched.
  EVERY OTHER MENTION OF THE OLD FILE, from `grep -rn active_work` over the whole tree outside
  `.venv/`, `docs/tracker/` and `.claude/task/` (round 1 claimed this sweep and missed three;
  scope-auditor found the first). Changed here: `.claude/commands/status.md` (`/status`, now
  `glab issue view 157`); `design-mocks/check_handover.py` and `design-mocks/section_sizes.py`
  (manual tools that read the file, now a path argument or the cache);
  `scripts/sync_metric_docs_blocks.py:419` (a comment citing the handover as the record of a
  finding, reworded to state the finding); `tests/test_no_dead_issue_refs.py` (asserts the file
  exists; the handover leaves the repo, so it leaves the list and CLAUDE.md stays covered);
  `tests/test_governance_hooks.py` (the hook's tests). Knowingly left, each harmless:
  `.gitlab-ci.yml:1123`, a protected file this contract does not open, whose comment says an owed
  follow-up is "recorded ... in `active_work.md`": the follow-up (setting the
  `deploy-nightly-image` resource group to `oldest_first`, still `unordered` on 2026-09-23 by the
  resource_groups API) had already left the handover before this branch, so the comment was
  already pointing at nothing; it is carried into issue #157 at this session's end, and the
  comment is named on the MR head. `.gitlab-ci.yml:455-456` says the check renders "375px and
  700px in EN and FI", stale on both counts, same protected file, same disclosure.
  `.claude/review_routing.json` (protected; the path stays in its artifact lists, which simply
  never match again); `tests/test_materialisation_policy.py:278` and
  `tests/test_governance_doc_parity.py:137` (exclusions for a path that no longer exists);
  `docs/working_agreement.md:233` (names the path among exempt artifacts, still true of the
  routing); `tests/test_governance_hooks.py` routing and review-patch tests (they write the path
  into a temporary repo); `docs/portable_guardrails/**` (the copy-out archive, deliberately left
  alone by `docs/agent_guardrails.md`); `CLAUDE.md:140`, `docs/wireframes/10_home.md:113,843`,
  `docs/audits/2026-06_alignment_audit.md` (history). The dbt-agent-kit plugin's plan-back gate
  keys on the file's presence and stops firing here; it is advisory and not this repo's hook.
  WHAT STOPS CHECKING THE HANDOVER (cto-reviewer round 1). As a tracked file, every tool write to
  it passed `host_fingerprint_gate.py` (a public network address is refused), and CI's
  `test_no_host_fingerprint_in_tree.py` and gitleaks scanned it. Written to a GitLab issue, no hook
  sees it, and the project's issues are public. The replacement: `design-mocks/check_handover.py`
  imports the gate's own `flagged_lines` and exits non-zero on a hit or on a draft over the
  16,000-character cap, and the one documented write is
  `python design-mocks/check_handover.py <draft> && glab issue update 157 ...`, so the check runs
  on the only path the procedure names. It is a step in a command, not a hook: a session that
  writes the issue another way skips it, and CI still catches a leak afterwards when the tracker
  backup, which carries closed issues, is next committed. Stated on the MR head.
  `.claude/active_work.md` is deleted from the tree and added to `.gitignore` beside the cache, so
  an old branch's copy cannot be re-added by accident. Checking out an older branch restores its
  stale copy on disk; nothing reads it any more.
  THE CHECK. `DEFAULT_VIEWPORTS` gains 1010 and is the only width list (`--viewports` defaults to
  it; `validate:ui` passes no flag, so `.gitlab-ci.yml` is untouched). An assertion may carry a
  width condition, `[>=1010px]` or `[<1010px]`, parsed fail-closed; measure_page skips an
  assertion outside its range. Three element rows: Search field `.header-actions .searchbox`
  (ruled), Search button `.iconbtn.search-m` (ruled), Header row `.header-in` `fits` (proposed:
  reported, never failing, because every page at 700px scrolls sideways today, the known defect).
  The mocks carry no header, so the rows are absent there and skip. The RED proof's fixtures gain
  the site header; the red one hides the field and shows the button at 1010px.
  PRESENCE (platform-reviewer round 1). A `visible=` assertion is measured only when the selector
  finds something, so a search field REMOVED from the page, rather than hidden, passed. The Pages
  table's Expect column, which already fails a page that shows none of an element, now accepts
  the same width condition, and every built page expects `Search field [>=1010px]` and
  `Search button [<1010px]`. A RED case runs the check on a built page with the field deleted.
  The text-line counter (`one-line`) now counts lines of text only: an icon beside the text sat
  at its own top and counted as a second line.
  blast_radius: `validate:ui` renders about 50% more (94 to about 141); every built page is
  measured at a desktop width for the first time, so a desktop-only defect elsewhere would now
  fail, measured before commit. No site file changes.

decisions_taken: >
  The approval for the two protected paths, quoted: the CPO's opening message of 2026-09-23 in
  this session, "Give it a home that does not ride a feature branch.", and the plan he approved
  the same day, which said of this change: "This edits the locked session-start step. Approving
  this plan is the approval for that edit." The plan named the home as a GitLab issue read at
  session start with a local fallback; `/status` reads the same issue because it read the same
  file.

  The width is 1010px because that is where `system.css` shows the search field (`@media
  (min-width: 1010px)`), the narrowest desktop layout and so the tightest; a test ties the two.
  Tuning a guard toward the rule it exists for is the builder's; the three new rows cite
  `docs/wireframes/09_chrome.md`, which already specifies the field at that width.

  The Header row is `proposed`, not `ruled`: it reports the 700px sideways scroll on every page
  without failing, because fixing the header is the CPO's call and a gate that is red on arrival
  gets ignored.

  The hook writes its cache through a temporary file and a rename, so an interrupted write never
  leaves a half copy, and an empty cache counts as none. Its GitLab read has a 15-second timeout,
  tested with a `glab` that hangs.

  The pre-publish check reuses the host-address gate's own patterns rather than a copy, and
  reuses the handover checker that already existed; no new tool, no new hook.

  The tracker backup (`docs/tracker/gitlab_snapshot.md`) keeps its one writer and its checksum;
  it stops riding a handover commit and is refreshed in whichever change is committed next,
  because it is read only when GitLab is down.

  Threshold declarations: the hook's source of truth changes (a mechanism change, CPO-approved as
  quoted); the hook calls GitLab once per session start (seconds, no billed service); the design
  check's run grows by about 50%, stated to him in the plan. No new dependency.

decisions_reserved:
  - Fixing the header's sideways scroll at 700px. Reported by the new proposed row, not fixed.
  - Whether the Header row becomes `ruled` once that is fixed.

done_when:
  - "`python -m pytest tests/test_design_inventory.py -q` passes, including a test that fails when `DEFAULT_VIEWPORTS` loses the width `system.css` shows the search field at, and the RED proof failing on Search field and Search button."
  - "`python scripts/check_design_inventory.py --dist site_v2/dist` on a fresh build: 3 viewports, 0 failures; the Header row's warnings named."
  - "A mutation hiding `.searchbox` at 1010px in `system.css` turns the check red on the built site; reverted."
  - "`python -m pytest tests/test_governance_hooks.py -q -k handover` passes: the issue is injected and cached; the cache is injected with its time when GitLab is unreachable; a plain message when neither exists; truncation announced; the multibyte case not truncated; the hook asks for issue 157 of project 85168767."
  - "A built page with the search field deleted from its header fails the check at 1010px on `Search field`; seen RED in `tests/test_design_inventory.py`."
  - "A `glab` that hangs longer than the timeout leaves the hook injecting the saved copy; an empty saved copy gives the no-handover message; the fail-open test never reaches the real `glab`."
  - "`python design-mocks/check_handover.py <draft>` exits non-zero on a draft carrying a public network address or over 16,000 characters, and zero on the current handover; tested."
  - "`echo {} | python .claude/hooks/handover_in.py` in this repo injects issue #157's description."
  - "`.claude/active_work.md` is gone from the tree and ignored; `pytest tests/` green."
  - "Routed reviewers PASS (scope-auditor; platform-reviewer and cto-reviewer at opus for the hook; bi-analyst-reviewer for the block standard); MR open with the Locked files line."

amendments:
  - 2026-09-23, round 2, on a clean tree: + `design-mocks/section_sizes.py` (reads the old file)
    and `scripts/sync_metric_docs_blocks.py` (a comment citing it). Authority: the approved change
    itself, moving the handover out of the repo; these are two more readers of the file it
    deletes, which round 1's sweep missed. The impact map now lists every mention with its
    disposition, the host-address coverage the move loses and its replacement, and the presence
    requirement for the search field. Raised by scope-auditor, platform-reviewer and cto-reviewer
    in round 1.
