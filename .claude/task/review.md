# Review — feat/69-country-region-dims — 2026-08-17

diff_sha256: d88311e43a2df18e1fccdba29f0a03b2461ed853e63ecbc2b61ff4627809e90d

rounds: 2

> ROUND 2 closed two scope-auditor findings, both verified before being fixed rather than argued
> with. No model, seed or schema file changed between rounds — only `escalations.log`,
> `layering.md` and the paperwork.
> After round 2 passed, `layering.md` gained ONE further edit that no reviewer demanded: the
> analytics reviewer noted the **Reuse** qualification rule tests the same thing as the bullet that
> was fixed and still had no pointer, judging it pre-existing. That is the fix-one-place-leave-the-
> paraphrase pattern the repo has been bitten by, so the pointer was added there too. It weakens
> nothing — it points at the same ruling.

## scope-auditor
VERDICT: PASS
risks_checked:
- ⛔ ROUND 1 FAILED on TWO findings, both correct.
  **(1)** `contract.md` cited a "CPO rescope of #69, 2026-08-16" authorising `dim_region`, and no
  such entry existed in `escalations.log` — searched for "rescope", "dim_region", "POINTS AT",
  "bad modeling"; the only hit in the file was an unrelated line 1195. The authority existed only
  as a GitLab issue note. **This was the SAME defect the predecessor branch was failed for**: that
  fix covered the naming rulings and not the rescope, so the instance was fixed and the class was
  not.
  **(2)** `dbt_project/docs/layering.md` names COUNTRY explicitly — "keep as attributes until a
  consumer needs rollups… Promote to a dim when the rollup logic appears, not before" — and this MR
  promotes it with no reader while omitting the very rollup (confederation) the doc names as the
  trigger. An unrecorded override plus an unchanged doc is a doc-sync failure.
- ROUND 2: the new `escalations.log` entry (2026-08-17) names `dim_region` and the POINTS-AT
  mechanism specifically in Ruling 2 — not a `dim_country`-only entry — and matches what
  `decisions_taken` cites. It self-reports the repeated omission rather than glossing it.
- ROUND 2: `layering.md`'s new sub-bullet is an attributed, scoped exception. The base sentence is
  unchanged; the exception names its authority and states the rule still governs position, language
  and nationality, so it cannot be stretched into a general licence.
- No code drift between rounds: `dim_country.sql`, `dim_region.sql`, `countries.csv`,
  `seeds/schema.yml` and `core.yml` are unchanged from what round 1 read.
- `decisions_reserved` still excludes `entity_type`, per-country `label_i18n_key`, per-country
  confederation, the FK step and the registry-blanking question — none silently decided.
- `NEW MECHANISM` / `RECURRING COST` claims hold; no credential-shaped content.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: both dims publish seeds directly into `3_core`. Checked `layering.md`'s fact
  inventory — `fct_team_market_value_snapshot` is precedent for a core table sourced from a seed —
  and `check_layer_contract.py` forbids core `ref()`-ing `stg_*`/`mart_*`, not seeds. No violation.
- Premature promotion, raised by this reviewer in round 1 before scope-auditor found it: traced to
  `escalations.log` 2026-08-14, where the CPO directs "a `countries` seed and `dim_country` on the
  confederations pattern, with FKs from the four dims". CPO-decided, with four named future FK
  readers plus `mart_competition_index`, deliberately split per "a dim and its first reader cannot
  ship together".
- `dim_country` has no surrogate key, unlike every other core dim: documented in the model and in
  `core.yml` — a country has no provider id, so `country_key` is the key, mirroring #852's
  assigned-not-derived slug rule. Deliberate and explained, not an unexplained inconsistency.
- `dim_region`'s `confederation` -> `region_key` rename happens only at publish time; the seed keeps
  its column name and its existing `relationships` test is untouched, so the later FK is not
  obscured.
- The contract's "no new guard" claim about `dim_region` VERIFIED, not accepted:
  `competition_registry.confederation` already carries a `relationships` test to
  `ref('confederations')` independent of this diff.
- Leaf status VERIFIED independently: grepped the whole `dbt_project` tree for `ref('dim_country')`
  and `ref('dim_region')` — zero matches in marts, intermediate, base or tests.
- Seed internal consistency: read all 224 rows — keys unique and sorted, no diacritics
  (`Curacao`, `Sao Tome and Principe` ASCII as claimed), and every `country_name` target in the
  67-row `country_name_overrides` resolves into the list with no unlisted name introduced.
- ROUND 2, the `layering.md` override in this reviewer's own territory: every factual claim in the
  new sub-bullet matches the recorded ruling (no reader; confederation deliberately absent for lack
  of a source; scope limited to country), and it does not generalise. Flagged that the **Reuse**
  condition tests the same thing and had no pointer — judged pre-existing rather than newly opened;
  a pointer was added there anyway.

## escalations
- question: May country and region be promoted to dimensions, replacing the `single_country` flag,
  and in what shape?
  CPO ANSWER: recorded in `escalations.log` (2026-08-17, `feat/69-country-region-dims`), three
  rulings — "You don't mix up countries and continents or regions in one column and add a flag
  'single country'. That's really bad modeling."; "yes, scope #69 that way" for the two-dimension
  design; and "we only need a mapping between what the provider gives us and what we turn into the
  single source of truth name" for the seed shape.
