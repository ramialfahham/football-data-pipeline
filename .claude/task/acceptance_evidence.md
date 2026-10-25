# Verification — the correction check compares every goal

Checked locally on the branch: `dbt parse`; SQLFluff on the test from the repo root; the full
pytest suite (1,600 passed, 2 skipped); the six offline gates. The test compiled and pointed at
prod's datasets, run on prod's data, then the same SQL without the one new condition, which is
main's logic.

criteria_demonstrated:
  - The goal part counts, per match, the seed goals with a player id that have a provider goal with the same team, player id, minute and added minute (an empty added minute counts as 0), one to one; no_longer_needed now also needs that count to equal the seed's goals. The warehouse review's round-1 double-count case is closed by normalising the added minute on both sides.
  - On prod's data the new check returns no row; main's logic returns `fixture_goal_corrections | 1639347 | no_longer_needed`. The provider's fifth goal names another scorer at 83'.
  - The diff touches only the header comment, three new steps, one added condition and one left join; the not_applied, does_not_add_up and not_sourced branches and the other two seeds' checks are unchanged.
