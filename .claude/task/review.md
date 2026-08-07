# Review — chore/add-python-linter — 2026-08-07

diff_sha256: aade10b157547b444ba5ee4af45d85446324c4795920dd179c487a197cb134ee

rounds: 3

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAILed on the "12 violations" figure, arguing no live F811 existed. WITHDRAWN in round 2
  on the evidence, re-derived independently: `tests/test_batch_fixtures.py:464` shadowed the
  line-9 `call` import in a comprehension, so removing that import cleared both the F811 and its
  F401 in one edit. 12 violations, 11 edits.
- Round 2 FAILed on "ten F401s survived it" contradicting its own sentence, since one of the ten is
  in `.claude/hooks/`, which the same clause says the hook does not cover. Round 3 confirms the
  objective now reads NINE inside the pattern, matching its own independent count.
- Second amendment verified as a genuine NARROWING rather than scope smuggled back: no
  `.pre-commit-config.yaml` hunk appears anywhere in the patch; `.ruff-ci.toml` is correctly named
  outside ruff's three auto-discovered names; the CI job matches the corrected `done_when` command
  verbatim.
- `.ruff-ci.toml` checked against `review_routing.json`'s protected-path table — matches no row, so
  the round-3 rename dropped no reviewer coverage.
- `done_when`, `decisions_reserved` and `decisions_taken` re-read against the final tree — no field
  still describes a superseded version of the branch.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAILed on the dependency's recorded reason being false: `.pre-commit-config.yaml` has
  configured `astral-sh/ruff-pre-commit` `rev: v0.7.4` all along, so "this repo has NO linter" was
  wrong, and a permanent comment in a PROTECTED file carried the same claim.
- Round 1 also FAILed on the new root `ruff.toml` silently retuning that existing hook: ruff walks
  up for config, so `select = ["F","E9"]` would have dropped E4 and E7 from a guard that enforces
  them today.
- Round 2 FAILed on three things: the false premise surviving VERBATIM in both permanent artifacts
  while only the contract was corrected; the contract contradicting itself on the fields that
  define bounds and acceptance; and — new — the `rev` bump dragging `ruff-format`, measured at 75
  files reformatted across v0.7.4 to v0.16.2.
- Round 3 confirms all three closed: `.gitlab-ci.yml` and `.ruff-ci.toml` carry the corrected
  account once with no contradicting sentence; the contract is corrected IN PLACE with the ⚠
  convention; `.pre-commit-config.yaml` is back to `main` exactly, so `ruff-format` never moves.
- The `.ruff-ci.toml` mechanism judged the plain option rather than a clever one, because the
  plainer alternative was MEASURED to be harmful. No new mechanism in the §10 sense — it grants no
  authority, gates no decision, changes no verdict rule.
- Direction of enforcement, the invariant that matters: nothing anywhere enforces less than it did
  on `main`. CI's `select` equals ruff's default, so the backstop is nowhere weaker than the local
  hook except in the four declared shim scripts, where the hook remains stricter.
- Thresholds re-checked on the delta: no dependency change beyond the approved pin, no cost change,
  no credential or permission surface, `*not_on_schedule` still first so the nightly cannot pick it
  up.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAILed on the same silent narrowing of the pre-commit hook, found independently, plus two
  ruff versions reading one config, plus the load-bearing `dummy-variable-rgx` having no test.
- Round 2 FAILed on the contract's acceptance criteria contradicting the tree, and specifically on
  `done_when` naming `ruff check . --select F,E9` — a CLI `--select` OVERRIDES the config file, so
  the stated verification bypassed the thing it verified and would have passed on a tree where the
  config failed to load at all. The sharpest finding of the three rounds.
- Round 3 confirms all five contract sites corrected and both residual test holes closed:
  `per-file-ignores` is pinned to `["E402"]` on single `scripts/*.py` patterns, and the CI
  invocation is pinned to carry `--config` and no `--select`/`--ignore`.
- The decoupling verified by reading, with the direction of every divergence checked rather than
  taken on trust: it is MONOTONE. CI is stricter on F811/F841 via `dummy-variable-rgx`; CI is more
  lenient on E402 for four files where the local hook still reports the same 10 it reports on
  `main`. Nothing enforced on `main` stops being enforced at either point, and no rule falls
  through both. The CI backstop additionally covers `.claude/hooks/`, which the hook's `files:`
  regex excludes and where the motivating defect lived.
- `per-file-ignores` re-counted against the tree after the rename — complete at four and not
  over-broad. Every other shim site already carries a pre-existing `# noqa: E402`.
- Removing round 2's version-parity test judged correct rather than lost coverage: the invariant it
  pinned no longer exists, and keeping it would have forced the alignment that `cto-reviewer`
  failed.
- ⚠ COULD NOT EXECUTE, stated in every round rather than implied: this reviewer had Read/Grep/Glob
  only and ran no command. `ruff check`, the red/green proofs, the 75-file format measurement and
  the pytest runs were all judged by reading. Its independent line-by-line count of the four shim
  files came to exactly 10, matching the measured figure.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- `effective_season_max` confirmed genuinely dead in `ingestion/api_football/seasons.py`: no call
  site in the file, no `__all__`, and no module re-exports it — `orchestrator.py:105` imports it
  directly from `season_inference.py`, which is untouched.
- Round 2 re-checked after the ruleset widened to ruff's default: grepped all `import`/`from`
  statements across `ingestion/**` (the two non-top-level ones are lazy imports inside function
  bodies, which E402 does not flag) and grepped for bare `except:`, `== None`, `== True/False` —
  the only hits are inside a comment. Nothing in the territory is silently carried.
- `per-file-ignores` and `extend-exclude` checked to confirm nothing under `ingestion/**` is
  exempted or excluded, so the exit-0 result is clean rather than suppressed.
- The `impact_map`'s `writers: none` / no-raw-table / no-mart claim tested against the diff — the
  entire ingestion-path change is the single import line.

## escalations
(none)

## Owed, carried forward rather than dropped
Four residual items, each surfaced by a reviewer and each explicitly judged BELOW the FAIL bar by
the reviewer that raised it. None is fixed here: round 3 is the cap, and any fix moves the hash.

1. **`impact_map`'s `import subprocess` enumeration is incomplete** (`scope-auditor`). It names
   `_staged_stat`, `_staged_paths` and `_cumulative_diff`; there are FIVE sites — add
   `_staged_diff_bytes:95` and `_base_commit:372`. The claim it supports still holds, because the
   operative verification is ruff flagging only line 197, which is independent of the manual list.
   The correct list is recorded here so it is not lost. This is the FIFTH #904-class instance in
   two days, sitting in a field that two rounds corrected adjacent text in.
2. **The decoupling rests on `.pre-commit-config.yaml`'s ruff hook never gaining
   `--config .ruff-ci.toml`** (`platform-reviewer`). `test_the_ci_config_is_not_auto_discoverable`
   pins the other direction only. One assertion that the hook's `args:` contain no `--config`
   closes it symmetrically.
3. **`test_the_ci_job_passes_the_config_and_no_select_override` forbids `--select`/`--ignore` but
   not `--isolated` or `--extend-ignore`** (`platform-reviewer`), both of which bypass the config
   the same way. Note `--extend-ignore` does not contain the substring `--ignore`.
4. **That same test's regex only matches invocations written as a YAML sequence item beginning
   `ruff check`** (`platform-reviewer`), so `python -m ruff check …` or a line inside a `- |` block
   scalar would go unseen while the test still passed on the compliant line.
