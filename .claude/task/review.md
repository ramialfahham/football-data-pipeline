# Review — feat/69-onboard-skill-country-check — 2026-08-16

diff_sha256: a2e050d95185482b200e7fc9be1460d9377a29e273e1f04bd5080d905a923921

rounds: 1

> REBOUND 2026-08-17. `gitlab/main` moved (`!56` #75, then `!53` #73), so the cumulative diff this
> hash is computed over has a new base. Rebased and the two task-artifact conflicts resolved per the
> documented rebase tax — MINE for `contract.md` and `review.md`. `escalations.log` and
> `active_work.md` did not conflict: this branch touches neither.
> **The reviewed file did not change.** `.claude/skills/onboard-competition/SKILL.md` is
> byte-identical to what scope-auditor read — verified with
> `git diff gitlab/main...HEAD -- .claude/skills/` against the pre-rebase blob.

## scope-auditor
VERDICT: PASS
risks_checked:
- Protected-path claim verified against `docs/working_agreement.md` lines 96-98 rather than taken
  from the contract: the enumerated list is `.claude/hooks/`, `.claude/agents/`,
  `.claude/commands/`, `.claude/settings.json`, `.claude/review_routing.json`, `.mcp.json`,
  `.cursor/mcp.json`, `.github/workflows/`, `.gitlab-ci.yml`. `.claude/skills/**` is genuinely
  absent, so no `protected_override` was required.
- Review routing: `.claude/review_routing.json`'s `paths` has no entry for `.claude/skills/**`,
  confirming scope-auditor is the sole required reviewer.
- The deferred governance question (should `.claude/skills/**` join the protected list, since a
  skill can embed shell exactly as a command can) is documented in `decisions_reserved` and NOT
  decided in the diff. The written rule is an enumerated list, not an analogised boundary, so
  editing the file without an override is not itself a violation — correctly deferred rather than
  silently decided.
- The step's central factual claim was checked against the model, not accepted:
  `base_apif__leagues.sql:40` is `coalesce(overrides.country_name, leagues.country)` behind a
  `left join`, so an unmatched provider string does pass through unchanged with no test failure.
  The claim is accurate, not exaggerated to justify the change.
- Mitigation-vs-guard framing: the added text flags itself as "a mitigation, not a guard" and names
  #69's FK to `dim_country` as the real fix — honest about its own limits.
- `scope_paths` conformance: the diff touches only `SKILL.md` and `contract.md`, both in scope.
- No new mechanism, no recurring cost — a checklist addition to an existing skill.

## escalations
(none — the `.claude/skills/**` protection question is recorded in `decisions_reserved` as a CPO
governance item, deliberately not raised as a blocker for this change)
