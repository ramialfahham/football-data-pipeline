# Acceptance evidence — #159, the last-matchday flag

No `site_v2/src/` change, so no acceptance gate applies; this records what was run. The compiled
model and the compiled test were run read-only against prod (dev datasets swapped for prod's, the
model inlined into the test), never `dbt build`.

criteria_demonstrated:
  - EVERY PLAYED MATCH OF THE ROUND JUST PLAYED IS FLAGGED. The inlined model: 479 flagged fixtures in
    29 rounds across 29 competitions, 0 of them unplayed; 1 competition with a round in progress
    carries both flags on that round; the new test returns 0 rows (the flagged set equals the played
    fixtures of each competition's latest round with a played fixture, recomputed from fct_fixture).
  - THE CURRENT SEASON IS THE NEXT MATCHDAY'S SEASON. The test's season property returns 0 rows;
    with the season condition removed from the model it returns 46 rows (AFCCL, APD, BL1, BL2, ...),
    earlier seasons flagged; a competition with no upcoming fixture has no flag (3 competitions carry
    a next round and no played fixture this season, and no last-round flag).
  - A TEST FAILS ON AN UNPLAYED OR OTHER-SEASON FLAG. RED under each mutation: flagging the round's
    unplayed fixtures too (CAFCL, CNL), dropping the season condition (46), choosing the round of the
    latest played kick-off (MLS, a played straggler), taking the round before the next round (CAFCL,
    KL1). dbt parse OK; sqlfluff clean on the model and the test; check_layer_contract and
    check_description_hygiene pass; pytest 1325 passed.
