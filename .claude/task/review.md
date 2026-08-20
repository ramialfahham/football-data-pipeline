# Review — feat/docs-blocks-shared-columns — 2026-08-20

diff_sha256: 470e47d3923ba700fa6f2c79d686ca7d09275417553ae5aa2ee32784ce3f125d

rounds: 3

> MR2 of the six-MR description-drift plan (`escalations.log`, 2026-08-20). Routing gives
> analytics-engineer-reviewer (`dbt_project/**`) and the always-on scope-auditor.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- ROUND 1 FAILED on a defect I introduced, and it was the exact failure this contract's own
  `impact_map` names as its risk: five surrogate-key blocks were worded "Foreign key to `dim_X`"
  and then applied verbatim to `dim_X`'s OWN primary key — false at the five defining sites
  (`dim_league.league_sk`, `dim_competition_season.season_sk`, `dim_team.team_sk`,
  `dim_player.player_sk`, `fct_fixture.fixture_sk`), replacing text that had been correct. Fixed by
  rewording all five to be direction-neutral (identity, not FK-ness) so the same text is true at
  the home table and at every joining site. Re-verified true across all 44 call sites.
- ROUND 2 FAILED on incomplete work: many sites were left as standalone bespoke text rather than
  composed with the block, so "one shared definition per concept" was claimed but not delivered.
  All now compose. Verified mechanically across all 259 references: zero uncomposed descriptions,
  zero unresolved `doc()` references.
- ROUND 2's factual finding was DISPUTED by me and ADJUDICATED IN MY FAVOUR after the reviewer read
  both source files: it had read `core.yml:386`'s "resolved by (league_code, season_api_year)" as a
  claim about how `season_sk` is CONSTRUCTED, and called it a contradiction of the real
  `league_api_id` grain. Construction and resolution are different: `dim_competition_season.sql:8`
  builds the key from `league_api_id`; `dim_player_team_season_mapping.sql:23-33,78-81` resolves it
  by lookup on `league_code`, because the roster source carries only that. Both halves of the text
  match their respective SQL. Recorded because accepting a confident-sounding finding uncritically
  would have replaced a true statement with a false one.
- Verified every `{{ doc() }}` call site resolves to one of the nine blocks actually defined — no
  typo'd name — and that both transfer models route to `league_code_ingest_provenance` rather than
  the ordinary block.
- Independently confirmed the "partition key" basis: zero `partition_by`/`cluster_by` in the
  project. Four pre-existing mentions elsewhere (three SQL docstrings, one model-level description)
  confirmed untouched by this diff and out of the eight-column scope.
- Qualifier preservation checked site by site, including the one loss it declined to wave through:
  a CPO-ruling citation dropped from `shared.yml:782`. The substantive grain and nullability
  content survived verbatim, and the ruling itself remains documented at
  `int_player_season__team.yml:7`, the model that implements it.
- Confirmed no `tests:` block added, removed or weakened anywhere; description strings only.

## scope-auditor
VERDICT: PASS
risks_checked:
- Judged the two declared deviations from the plan's "8 columns, 8 blocks" shorthand and accepted
  both as forced rather than chosen: the `league_code` split into two blocks (the transfer models'
  meaning is incompatible and was already flagged as such in the pre-existing text, so merging
  would manufacture a false claim), and the omission of "partition key" from the new block (the
  phrase is false, and writing a canonical block that repeats it would entrench the error at every
  call site while fixing the duplication).
- Checked the MR3/MR4 boundary held: walked every changed hunk and confirmed each is a
  `description:` value for one of the eight named columns. No dates, rulings, issue refs, unrelated
  descriptions, tests or config touched.
- Spot-checked qualifier preservation independently across ~10 sites, including the VAR-nullability
  note and the DOMESTIC-LEAGUE registry assertion, confirming the generic boilerplate was dropped
  only where the new block already carried the same meaning.
- scope_paths covers every touched file, including the new `dbt_project/models/docs/shared_columns.md`,
  whose location under `models/` is required since dbt resolves docs blocks from `model-paths` and
  there is no `docs-paths` override.
- Full diff swept for credential-shaped content: none.

## escalations
(none)
