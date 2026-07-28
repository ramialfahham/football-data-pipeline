# Review — chore/rename-brand-sweep — 2026-07-28

> Machine-checked review artifact (governance G3). **Three rounds, at the cap. Round 1 was 3 FAILs
> out of 4, and every one was the same shape: I fixed the instance a reviewer named instead of the
> class it belonged to.**
>
> **Round 1 — analytics-engineer FAIL.** I "corrected two false lines" in `site_architecture.md`.
> There were six. Patching two left the file contradicting ITSELF: §2's locked row said "no
> cutover" while §7 still described a legacy export "keeping running until #377" and §8's decisions
> log still marked "Current MVP stays live until parity cutover" as **locked**. A doc that
> contradicts itself is worse than one uniformly stale.
>
> **Round 1 — bi-analyst FAIL** on the chrome wireframe's ASCII box. Its diagnosis was wrong and its
> proposed fix would have made things worse: measured against `main`, the misalignment PREDATED this
> branch and spanned 8 rows, and my edits had held every row's original width. Shrinking only the
> row it named would have broken that row against its own block. It re-derived this independently in
> round 2 and retracted the finding — the fix is right because it was challenged, not because I was.
>
> **Round 1 — cto FAIL, and this is the one that matters beyond this PR.** `.github/workflows/` is a
> PROTECTED prefix requiring `protected_override:` in the contract. The field was absent and the edit
> went through anyway. I reproduced why: **two independent guard holes.** `_SED_I`
> (`task_contract_gate.py:81`) anchors its filename group on `$`, so it cannot match
> `for f in …; do sed -i '…' "$f"; done` — the `; done` breaks the anchor, and the target is a shell
> variable it could not resolve regardless. Worse, `_gate_bash_post` — the documented "ironclad net"
> — flags a file only when `not _matches_scope(...)`, so **a PROTECTED file that is IN scope with no
> override is structurally invisible to the backstop.** Both re-derived independently by cto. Filed
> as #863; NOT fixed here, because `.claude/hooks/**` is itself protected and needs its own
> CPO-approved contract.
>
> **Round 2 — scope-auditor FAIL, and it was right.** It ruled that amendments 3 and 4 had grown the
> scope in response to reviewer FAILs rather than returning to the CPO, and that the branch "cannot
> be assessed as a delta anymore". **I did not argue it into a PASS.** It went to the CPO as three
> options — split into two PRs (my recommendation), authorise the wider scope, or drop the
> corrections — and he **authorised the wider scope**, naming "the whole MVP-status class plus the
> ASCII realign". Amendment 6 records it; the contract's title and objective were restated so the
> widening is stated, not implied by amendment archaeology.
>
> **Round 3 — all four PASS.**
>
> ## Correction to my own claim, recorded because it is the session's real lesson
>
> Amendment 7 states the surviving hits of the false-claim sweep are `site_architecture.md:218` (the
> struck-through SUPERSEDED row) and `ci-site-v2.yml:4` (deferred, protected). **That was incomplete,
> and analytics-engineer caught it in round 3.** My sweep ran with
> `--include="*.md" --include="*.yml" --include="*.py"`, so `site_v2/src/layouts/Layout.astro:25` and
> `site_v2/src/lib/href.ts:3` were unfindable **by construction** — the filter, not the pattern, was
> the defect. Both are in `site_v2/**`, which this contract's `done_when` excludes on every hash, and
> both predate this branch. Filed as **#864** for C2, which owns that surface.
>
> That is the **third** instance of one shape in this session: `git grep -i "matchday ?iq"` never
> searched the spaced form (BRE makes `?` a literal); a brand grep cannot find a false CLAIM that
> does not contain the brand; and a file-type filter narrower than the class being swept. Each was
> reported as a sweep and was structurally incapable of being one. **When a `done_when` is a grep,
> state what the grep cannot see.**

diff_sha256: 685e315b87496a6cdf359be4277f721b5c3be2974a11d95065c5134d6b10c7c9

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- **The widened objective is CPO-authorised, not builder drift** — it verified that amendment 6
  records an explicit CPO choice between three options, that the contract's title and objective now
  state the widened scope rather than leaving it to amendment archaeology, and that the work stayed
  inside those bounds. Its round-2 FAIL is what forced the escalation; it confirmed the escalation
  actually happened rather than being asserted.
- **Amendment 7's reservation split holds exactly** — `north_star.md`'s H1 still reads
  "Matchday IQ", and its brand and positioning are untouched and still reserved to #860; only line
  37, the false MVP-status claim, moved out. It named the residual risk honestly: "what constitutes
  an MVP-status false claim" is my interpretation inside the CPO's class-level authorisation, and
  that is a classification call, defensible here because the same boundary — correcting a FALSE
  claim is not the same act as RENAMING — was applied consistently across all four files.
- **The narrowed `done_when` guard still catches what it exists to catch** — a new forward-looking
  stale claim would not carry the word RETIRED. It flagged the real limitation: enforcement is a
  documented grep, not a CI gate, so this remains a discipline dependency.

## cto-reviewer
VERDICT: PASS
risks_checked:
- **Both guard holes re-derived independently, not taken from my report.** On hole 2 it confirmed the
  two-term `and` short-circuits: for a protected file listed in `scope_paths`,
  `not _matches_scope(...)` is `False` on its own, so `_is_protected`/`protected_override` are never
  evaluated. On hole 1 it confirmed the `$`-anchor makes a match impossible from inside a loop body,
  independent of whether the target is a literal or a variable.
- **`protected_override` is enforced by reviewer diffing and by NOTHING ELSE** — it read the source
  and found the gate only checks the field's PRESENCE (`re.match(r"^protected_override\s*:", line)`),
  never its content. So the prose bound is an audit commitment, not a mechanism. It then did that
  diffing itself at the final hash: both workflow files change only the `PROJECT_BOARD_TITLE` value,
  with `permissions:`, `on:`, `github-token`, `uses:` and every other line byte-identical.
- **Deferring `ci-site-v2.yml:4` is the right boundary, not a dodge** — reaching a third protected
  file, even for a one-word comment under a CPO objective that arguably covers it in spirit, would
  require the override to name it. Widening a protected-path authorisation by inference mid-review is
  exactly the drift the field exists to block. Confirmed the file appears nowhere in the diff.
- **Full file-list reconciliation** — diffed the patch's complete `diff --git` list against
  `scope_paths` and found exact 1:1 correspondence across 23 files, ruling out undeclared drift
  introduced alongside the widening. Confirmed `CLAUDE.md` and `north_star.md` are not protected, so
  the widened scope is a plain amendment and not a second guard-integrity question.
- **Merge safety, asked directly** — an open bypass in the guard chain does NOT make this PR unsafe:
  the exposure is identical whether this branch merges or sits open, and blocking an already-correct
  change would not reduce it. #863 needs priority because the hole is live and exploited, not
  theoretical; that is a tracker question, not a merge blocker.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- **The round-1 FAIL is closed and the file is now internally consistent** — it re-read
  `site_architecture.md` in full and swept the whole class; all six previously-contradictory sites
  (§2:29, §7:196-197/200/203-208, §8:218, header:4) now agree with each other and with the corrected
  `export_site_data.py` docstring. The two remaining "MVP" mentions (§4:140, §5:159) are
  backward-looking description of what the MVP was, not claims about current liveness.
- **Three-way cross-consistency of the authorities** — it read `CLAUDE.md:53`,
  `docs/north_star.md:37` and `docs/site_architecture.md:29` directly and confirmed they state
  identical facts (retirement date, mechanism, #377's redefinition, the #799 consequence). Any two
  disagreeing would have been the round-1 defect one level up.
- **It found what my own sweep could not** — `site_v2/src/layouts/Layout.astro:25` and
  `site_v2/src/lib/href.ts:3`, hidden from me by my `--include` filter. Verified both sit in
  `site_v2/**`, excluded by `done_when` on all three hashes and untouched by this branch, so they are
  pre-existing and out of scope. Disclosed rather than silently passed over. Filed as #864.
- **The two narrow checks at the final hash** — `scripts/export_site_data.py` still has exactly one
  hunk (`@@ -4,9 +4,10 @@`, lines 7-10), entirely inside the module docstring (lines 1-24), no
  executable line touched; no `dbt_project/**` path anywhere in the diff.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- **It re-derived the box measurement independently and RETRACTED its own round-1 finding.** Against
  the diff's preimage (= `main`), the entire drawer block and the entire footer block measured 45
  interior characters while every border row measured 44 — so the row it had named was already 45
  before this branch, and my edits had held every row's original width. It confirmed its own proposed
  fix "would indeed have left it inconsistent with rows 38-40 in the same block". At the final hash
  all 12 rows measure 44 and the box closes.
- **Wireframe-file identity since its PASS, verified not assumed** — same postimage blob hashes and
  hunk text for `09_chrome.md` and `00_overview.md`, and a fresh grep confirming the six reserved
  SEO-title files (`02`, `03`, `11`, `12`, `13`, `14`) appear nowhere in the diff.
- **`mdp-theme` matches shipped code in both directions** — `SiteHeader.astro:89` and
  `Layout.astro:39`, with no `mdiq-theme` anywhere in `site_v2/src`. The doc had been wrong since
  #862 merged, so this was a correctness fix rather than cosmetics. The Brand row's split-markup
  claim matches `SiteHeader.astro:38` and `SiteFooter.astro:38` exactly.
- **Asked whether to file the double-width-glyph caveat, it said NO, with reasons** — line 28's
  `🌓`/`☰` make character count diverge from rendered column width, but that is a property of any
  ASCII wireframe mixing box-drawing with emoji, nothing parses these diagrams programmatically,
  there is no canonical width they target, and a real narrow-viewport question is already covered by
  #827's rendered-page evidence against the live build. Filing it would be tracker noise with no
  realistic owner. Not filed.

## escalations
- question: The scope grew from a brand rename into a documentation-correctness PR. scope-auditor
  ruled that should have come back to the CPO rather than become amendments. Split into two PRs,
  authorise the wider scope, or drop the corrections and file them?
  CPO ANSWER: 2026-07-28 — **"Keep it as one PR, you authorize the wider scope"**, explicitly
  covering "rename plus correcting the whole MVP-status class plus the ASCII realign". Recorded as
  amendment 6. My recommendation had been the split; he chose otherwise and that is the decision.
