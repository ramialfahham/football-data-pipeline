"""NEGATIVE CONTROLS for `gen_competitions.py`'s guards.

⚠ A CHECK THAT HAS ONLY EVER BEEN SEEN GREEN PROVES NOTHING. Three checks in this folder passed
on real defects on 2026-08-10 until they were made to fail first. So each guard below is handed a
reconstruction of the defect it exists to catch, and must go RED.

Every reconstruction is a REAL failure mode, not an invented one:

   1. the region read off `country`                     -> the original #54 defect
   2. a confederation the seed does not know            -> a new one onboarded
   3. a confederation the registry's enum does not know -> an invented eighth
   4. a type with no `single_country`                   -> the new column forgotten
   5. single_country=true on a row whose country is a REGION -> a mistyped competition
   6. an UNDECLARED new competition_type                -> designing against fiction
   7. a shipped competition_type silently DROPPED       -> same
   8. an UNDECLARED rename                              -> same
   9. `display_group` creeping back into the proposal   -> the deleted column returning
  10. a blank label                                     -> "blanks are not allowed" (CPO)
  11. two types sharing a label                         -> two headings reading the same
  12. the registry already corrected                    -> the in-memory edit applied twice

Run:  python prove_region_checks_fail.py
"""
import copy

import gen_competitions as G

PASS, FAIL = [], []


def expect_red(label, fn):
    """The guard must RAISE. Anything else means it would not have caught the defect."""
    try:
        fn()
    except (AssertionError, SystemExit) as exc:
        first = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
        PASS.append((label, first))
        return
    FAIL.append(label)


def swapping(target, **attrs):
    """Swap module state, run one guard, put it back — controls must not leak into each other."""
    def run():
        saved = {k: copy.deepcopy(getattr(G, k)) for k in attrs}
        try:
            for k, v in attrs.items():
                setattr(G, k, v)
            target()
        finally:
            for k, v in saved.items():
                setattr(G, k, v)
    return run


# --- 1. THE ORIGINAL DEFECT -------------------------------------------------------------------
# Not a guard but the design premise, so it is proved by MEASUREMENT: reading the sub-line off
# `country` puts the literal "International" under headings meant to distinguish regions, and
# gives two members of ONE category two different strings for the same idea.
def prove_country_is_not_usable():
    champs = [c for c in G.REGISTRY_ALL if c["competition_type"] == "continental_championship"]
    by_country = {c["league_code"]: c.get("country") for c in champs}
    by_region = {c["league_code"]: G.region(c) for c in champs}
    assert len(set(by_country.values())) < len(set(by_region.values())), \
        "country is at least as informative as the confederation region — the premise is wrong"
    assert "International" in by_country.values(), \
        "no continental_championship says 'International' any more — the registry was fixed and " \
        "this control is stale"
    assert "International" not in by_region.values()
    collapsed = sorted(k for k, v in by_country.items() if v == "International")
    print("  1. country -> %d distinct value(s) over %d continental championships; %s all say "
          "\"International\". confederation -> %d distinct. PROVEN"
          % (len(set(by_country.values())), len(champs), ", ".join(collapsed),
             len(set(by_region.values()))))


# --- 2. a confederation the seed does not know -------------------------------------------------
_unknown_confed = copy.deepcopy(G.REGISTRY_ALL)
_unknown_confed[0] = {**_unknown_confed[0], "league_code": "NEWC", "confederation": "UNCAF"}

# --- 3. an invented eighth confederation (seed knows one the registry's enum does not) ---------
_extra_confed = {**G.CONFED_EN, "UNCAF": "Central America"}

# --- 4. the new column forgotten on a type -----------------------------------------------------
_noflag = copy.deepcopy(G._TYPES)
_noflag["continental_cup"]["single_country"] = ""

# --- 5. a mistyped competition: single_country=true, but its country is a REGION ---------------
_mistyped = {**G.SINGLE_COUNTRY, "continental_cup": True}

# --- 6 / 7 / 8 / 9. the shipped-seed guard, one control per declared kind of difference --------
_undeclared_new = {**copy.deepcopy(G._TYPES),
                   "womens_domestic_league": {"competition_type": "womens_domestic_league",
                                              "entity_type": "club", "single_country": "true",
                                              "label_i18n_key": "x", "label_en": "Women's leagues"}}
_dropped = {k: v for k, v in copy.deepcopy(G._TYPES).items() if k != "domestic_cup"}
_undeclared_rename = {("domestic_cups" if k == "domestic_cup" else k): v
                      for k, v in copy.deepcopy(G._TYPES).items()}
_column_returns = copy.deepcopy(G._TYPES)
for _row in _column_returns.values():
    _row["display_group"] = "leagues"

# --- 10 / 11. the label rules ------------------------------------------------------------------
_blank_label = copy.deepcopy(G._TYPES)
_blank_label["national_team_friendly"]["label_en"] = ""
_dupe_label = copy.deepcopy(G._TYPES)
_dupe_label["domestic_cup"]["label_en"] = "Domestic leagues"

# --- 12. the registry already corrected --------------------------------------------------------
_already_retyped = [{**c, "competition_type": "club_world_cup"} if c["league_code"] == "CWC" else c
                    for c in copy.deepcopy(G._REGISTRY_RAW)]


def _with_types(types, target):
    """check() and check_seed_matches_shipped() both read the derived maps, so swap all of them."""
    def run():
        saved = {k: copy.deepcopy(getattr(G, k))
                 for k in ("_TYPES", "TYPE_EN", "TYPE_KEY", "SINGLE_COUNTRY", "ENTITY_TYPE")}
        try:
            G._TYPES = types
            G.TYPE_EN = {k: v["label_en"] for k, v in types.items()}
            G.TYPE_KEY = {k: v["label_i18n_key"] for k, v in types.items()}
            G.SINGLE_COUNTRY = {k: v["single_country"] == "true" for k, v in types.items()}
            G.ENTITY_TYPE = {k: v["entity_type"] for k, v in types.items()}
            target()
        finally:
            for k, v in saved.items():
                setattr(G, k, v)
    return run


if __name__ == "__main__":
    print("Negative controls — every guard must go RED on the defect it exists to catch.\n")

    prove_country_is_not_usable()

    expect_red("2. confederation not in the seed (a new one onboarded)",
               swapping(G.check, REGISTRY_ALL=_unknown_confed))
    expect_red("3. seed carries a confederation the registry's enum does not",
               swapping(G.check_confederation_enum, CONFED_EN=_extra_confed))
    expect_red("4. a competition_type with no `single_country`",
               _with_types(_noflag, G.check))
    expect_red("5. single_country=true on a row whose country is a REGION (mistyped)",
               swapping(G.check, SINGLE_COUNTRY=_mistyped))
    expect_red("6. UNDECLARED new competition_type",
               _with_types(_undeclared_new, G.check_seed_matches_shipped))
    expect_red("7. a SHIPPED competition_type quietly dropped",
               _with_types(_dropped, G.check_seed_matches_shipped))
    expect_red("8. an UNDECLARED rename",
               _with_types(_undeclared_rename, G.check_seed_matches_shipped))
    expect_red("9. `display_group` creeping back into the proposal",
               _with_types(_column_returns, G.check_seed_matches_shipped))
    expect_red("10. a blank label (blanks are not allowed)",
               _with_types(_blank_label, G.check))
    expect_red("11. two competition_types sharing a label",
               _with_types(_dupe_label, G.check))
    expect_red("12. the registry has already been corrected (edit applied twice)",
               swapping(G.check_registry_still_unedited, _REGISTRY_RAW=_already_retyped))

    for label, why in PASS:
        print("  RED  %s\n         -> %s" % (label, why))
    for label in FAIL:
        print("  ⛔ GREEN ON A REAL DEFECT: %s" % label)

    print("\n%d/%d controls fired." % (len(PASS), len(PASS) + len(FAIL)))
    if FAIL:
        raise SystemExit("A guard did not catch its own defect.")
