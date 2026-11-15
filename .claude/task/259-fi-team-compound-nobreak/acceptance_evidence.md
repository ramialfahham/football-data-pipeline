# Acceptance evidence — Finnish team compound stays on one line

The measurement is in rendered_page_evidence.md.

criteria_demonstrated:
  - **Criterion 1 (helper test):** site_v2/src/lib/teamCompound.test.mjs shows "Hertha BSC" before the Finnish compound is "Hertha BSC" + no-break space + non-breaking hyphen, "HJK" is "HJK-", and English and German are unchanged. npm test in site_v2 is green.
  - **Criterion 2 (wording and pins, no other change):** the diff touches the helper, its test, its one importer and the task folder; no i18n string, baseline pin, build step or other page file changed.
  - **Criterion 3 (design check at 280 to 375px):** words on two lines with 31 team names, before and after: 280px 2 and 0, 320px 17 and 0, 360px 19 and 0, 375px 14 and 0.
