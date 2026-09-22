// Metric labels resolve from the catalogue, per locale (#370).
//
// Runs in `npm test`, which `prebuild` runs, so this gates the BUILD and not only CI. Each test below
// is one of #370's locked acceptance criteria.
//
// Parses the TypeScript as TEXT rather than importing it, which is the house pattern here:
// `check-page-specs.mjs` extracts the EN key set from `strings.ts` the same way, because `node --test`
// cannot import `.ts` and adding a transpile step for four assertions would not earn its cost.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const SITE = join(HERE, "..");
const REPO = join(SITE, "..");

const strings = readFileSync(join(SITE, "src/i18n/strings.ts"), "utf8");
const rowsSrc = readFileSync(join(SITE, "src/lib/metricRows.ts"), "utf8");
const LOCALES = ["EN", "DE", "FI"];

/** The quoted-dotted label keys inside one METRIC_LABELS_<loc> block.
 *
 * ⚠ ANY dotted key, not just `metrics.*.label`. The catalogue uses a SECOND namespace for player
 * metrics — `playerMetrics.scorerPoints.goals` and friends — and while this regex was anchored on
 * `metrics\.` those four labels were invisible to every parser that polices metric names: this
 * one, `check-page-specs.mjs`'s, and `scripts/check_copy_gate.py`'s. A missing Finnish label would
 * have shipped a BLANK board title (metricLabel falls back to English, then to "") with nothing
 * red. Widened with #40 MR B, which is the change that first rendered one.
 */
function labelBlock(loc) {
  const m = strings.match(
    new RegExp(`const METRIC_LABELS_${loc}: MetricLabels = \\{([\\s\\S]*?)\\n\\};`));
  assert.ok(m, `METRIC_LABELS_${loc} not found in strings.ts`);
  const out = new Map();
  for (const [, key, val] of m[1].matchAll(/"([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+)":\s*"((?:[^"\\]|\\.)*)"/g)) {
    out.set(key, val);
  }
  return out;
}

const labels = Object.fromEntries(LOCALES.map((l) => [l, labelBlock(l)]));
const rowKeys = [...rowsSrc.matchAll(/labelKey:\s*"(metrics\.[A-Za-z0-9_]+\.label)"/g)].map((m) => m[1]);
const heroKeys = [...readFileSync(join(SITE, "src/components/team/DeservedHero.astro"), "utf8")
  .matchAll(/metricLabel\(lang,\s*"(metrics\.[A-Za-z0-9_]+\.label)"\)/g)].map((m) => m[1]);

/** The catalogue rows, as {metric_id, entity, label_i18n_key}. Naive comma split, which is safe
 * for exactly these three columns: they are the first three, and `description` — the only field
 * that carries commas — comes after them. */
function catalogueRows() {
  const lines = readFileSync(join(REPO, "dbt_project/seeds/metric_catalogue.csv"), "utf8")
    .split(/\r?\n/);
  const header = lines[0].split(",");
  const [id, entity, key] = ["metric_id", "entity", "label_i18n_key"].map((c) => header.indexOf(c));
  assert.ok(id >= 0 && entity > 0 && key > 0, "metric_catalogue.csv is missing a required column");
  return lines.slice(1).filter(Boolean).map((l) => l.split(","))
    .map((c) => ({ metric_id: c[id], entity: c[entity], label_i18n_key: c[key] }));
}

/** The Home Top players board label keys (#40), derived from the two places that already own them:
 * the board list in the export and the catalogue's own `label_i18n_key`.
 *
 * ⚠ NOT read from `src/data/landing.json`, and that is deliberate. A board with no data is omitted
 * from the payload by design (#40: "if a board is missing, the user may not even notice, so don't
 * show"), so a payload-derived list would make a legitimately empty board turn this test red — a
 * build failure over something the DESIGN says is silent. `assert_mart_leaderboards_every_home_
 * board_has_a_leader` is what notices a vanished board. This list must not move with the data. */
const exportSrc = readFileSync(join(REPO, "scripts/export_site_data.py"), "utf8");

/** The label keys of one board tuple in the export, resolved through the catalogue for its entity. */
function boardTuple(name, entity, atLeast) {
  const block = exportSrc.match(new RegExp(`${name}\\s*=\\s*\\(([^)]*)\\)`));
  assert.ok(block, `could not find ${name} in scripts/export_site_data.py`);
  const ids = [...block[1].matchAll(/"([a-z0-9_]+)"/g)].map((m) => m[1]);
  assert.ok(ids.length >= atLeast, `parsed only ${ids.length} ${name} ids — the tuple regex broke`);
  const rows = catalogueRows().filter((r) => r.entity === entity);
  return ids.map((id) => {
    const row = rows.find((r) => r.metric_id === id);
    assert.ok(row?.label_i18n_key, `no ${entity} catalogue row with a label_i18n_key for board ${id}`);
    return row.label_i18n_key;
  });
}

// The Home boards and the competition page's Rankings tab (#151): the twelve team boards and the
// thirteen player boards, resolved the same way, so a board label missing in a locale is red here
// before the page ships it blank.
const boardKeys = [
  ...boardTuple("_HOME_PLAYER_BOARDS", "player", 4),
  ...boardTuple("_COMPETITION_TEAM_BOARDS", "team", 12),
  ...boardTuple("_COMPETITION_PLAYER_BOARDS", "player", 13),
];

/** The metric GROUPS (#152): keys and order from the export's copy of the catalogue
 * (`src/data/metric_groups.json`, pinned to the seed by `tests/test_metric_groups.py`); a name per
 * locale under `metricGroups.<key>.label`. */
const groupJson = JSON.parse(readFileSync(join(SITE, "src/data/metric_groups.json"), "utf8"));
const groupIds = groupJson.groups.map((g) => g.key);
const groupKeys = groupIds.map((k) => `metricGroups.${k}.label`);
const rowGroups = [...rowsSrc.matchAll(/\bgroup:\s*"([a-z_]+)"/g)].map((m) => m[1]);

test("the metric groups come from the catalogue and every one has a name in every locale", () => {
  assert.ok(groupIds.length >= 8, `parsed only ${groupIds.length} groups from metric_groups.json`);
  assert.deepEqual(groupJson.groups.map((g) => g.order), groupIds.map((_, i) => i + 1),
    "metric_groups.json is not one row per group at positions 1..N");
  assert.ok(rowGroups.length >= 16, `parsed only ${rowGroups.length} group: tokens from metricRows.ts`);
  const unknown = [...new Set(rowGroups)].filter((g) => !groupIds.includes(g));
  assert.deepEqual(unknown, [],
    `metricRows.ts names groups the catalogue does not define: ${unknown.join(", ")}`);
  for (const loc of LOCALES) {
    const missing = groupKeys.filter((k) => !labels[loc].get(k));
    assert.deepEqual(missing, [], `${loc} has no group name for: ${missing.join(", ")}`);
    const stray = [...labels[loc].keys()].filter((k) => k.startsWith("metricGroups.") && !groupKeys.includes(k));
    assert.deepEqual(stray, [], `${loc} names a group the catalogue does not define: ${stray.join(", ")}`);
  }
});

test("every metric name the page asks for resolves in all three locales", () => {
  const asked = [...new Set([...rowKeys, ...heroKeys, ...boardKeys, ...groupKeys])];
  assert.ok(asked.length >= 22, `expected >=22 metric names in use, found ${asked.length}`);
  for (const loc of LOCALES) {
    const missing = asked.filter((k) => !labels[loc].get(k));
    assert.deepEqual(missing, [],
      `${loc} has no label for: ${missing.join(", ")}. t()'s sibling metricLabel() falls back to ` +
      `English, so a gap here silently ships English to a ${loc} reader.`);
  }
});

test("no locale carries a label nothing renders, and none is empty", () => {
  const asked = new Set([...rowKeys, ...heroKeys, ...boardKeys, ...groupKeys]);
  for (const loc of LOCALES) {
    for (const [key, val] of labels[loc]) {
      assert.ok(asked.has(key), `${loc}.${key} is defined but no component asks for it`);
      assert.ok(val.trim().length > 0, `${loc}.${key} is empty, which renders a blank label`);
    }
  }
});

test("every labelKey is a label_i18n_key the catalogue actually declares", () => {
  // Checks the `label_i18n_key` COLUMN, verbatim. The first version of this test stripped
  // ⚠ Read the `label_i18n_key` COLUMN. Do not strip `metrics.`/`.label` and look the remainder up in
  // `metric_id` — that is a different and wrong invariant. metric_id `shots_on_goal_per_match` declares
  // label_i18n_key `metrics.shots_on_target_per_match.label`, so an id-based check calls the real key
  // dangling and an invented one valid.
  // ⭐ That disagreement is now a LEGACY KEY NAME, not a term split: step 5 (RULING 2) moved the
  // English label to "Ø Shots on goal", so the id and the user-facing term agree and only the key
  // still reads "on_target". The invariant this test enforces is unchanged.
  const csv = readFileSync(join(REPO, "dbt_project/seeds/metric_catalogue.csv"), "utf8");
  const lines = csv.split(/\r?\n/);
  const header = lines[0].split(",");
  const col = header.indexOf("label_i18n_key");
  assert.ok(col > 0, "metric_catalogue.csv has no label_i18n_key column");
  const declared = new Set(
    lines.slice(1).map((l) => l.split(",")[col]).filter(Boolean));
  assert.ok(declared.size >= 50,
    `parsed only ${declared.size} label_i18n_key values — the CSV column split broke, and a set that ` +
    `small would make every key look undeclared`);
  const asked = [...new Set([...rowKeys, ...heroKeys, ...boardKeys])];
  const bad = asked.filter((k) => !declared.has(k));
  assert.deepEqual(bad, [],
    `label keys the catalogue does not declare in label_i18n_key: ${bad.join(", ")}. ` +
    `Read the column; never infer the key from the metric_id or the payload field.`);
});

test("the CPO-validated MVP labels are byte-identical to site/i18n", () => {
  const corpus = Object.fromEntries(["en", "de", "fi"].map((l) => [
    l.toUpperCase(),
    JSON.parse(readFileSync(join(REPO, `site/i18n/${l}.json`), "utf8")).metrics ?? {},
  ]));
  let compared = 0;
  const drift = [];
  for (const loc of LOCALES) {
    for (const [key, val] of labels[loc]) {
      const id = key.replace(/^metrics\./, "").replace(/\.label$/, "");
      const validated = corpus[loc][id]?.label;
      if (!validated) continue;
      // EN diverges for finishing_efficiency_pct by design: v2's locked label is kept and the corpus's
      // "% Conversion rate" is a §10 pick still open.
      if (loc === "EN" && id === "finishing_efficiency_pct") continue;
      compared += 1;
      if (val !== validated) drift.push(`${loc}.${id}: "${val}" != validated "${validated}"`);
    }
  }
  assert.ok(compared >= 27, `expected >=27 validated labels to compare, compared ${compared}`);
  assert.deepEqual(drift, [], `CPO-validated wording changed:\n  ${drift.join("\n  ")}`);
});

test("the three hand-written hero label strings are gone", () => {
  for (const key of ["heroSotFor", "heroSotAgainst", "heroSotDiff"]) {
    assert.ok(!new RegExp(`^\\s+${key}:`, "m").test(strings),
      `${key} is still a chrome string; it is a metric name and belongs in METRIC_LABELS`);
  }
});

test("the page-spec checker's parser and this one see the SAME metric keys", async () => {
  // The `"metrics.X.label"` shape is now parsed by THREE hand-written regexes: this file's
  // `labelBlock`, `check-page-specs.mjs`'s inline one inside `collectEnI18nKeys`, and
  // `scripts/check_copy_gate.py`'s `_METRIC_ENTRY_RE`. An edit to one (a hyphen in a metric id, a
  // different quote style) can silently diverge from the others. This pins the two JS parsers to each
  // other; the Python one is pinned to the same anchor in tests/test_governance_hooks.py.
  const { collectEnI18nKeys } = await import("./check-page-specs.mjs");
  const { keys, error } = collectEnI18nKeys();
  assert.equal(error, null);
  // Dotted keys, both namespaces. Anchoring this filter on `metrics\.` while `labelBlock` above
  // reads any dotted key would make the two sets disagree by construction on every playerMetrics
  // entry — the drift this test exists to catch, manufactured by the test itself.
  const theirs = new Set([...keys].filter((k) => k.includes(".")));
  const mine = new Set(labels.EN.keys());
  assert.deepEqual([...theirs].sort(), [...mine].sort(),
    "the two metric-key parsers disagree; one of the regexes has drifted");
});

test("a board title spells the rate out, in the LOCALE's own words", async () => {
  // #41: "Ø Goals" reads badly as a heading, and a bare "Goals" is wrong because these are
  // per-match rates and a bare noun reads as a season total. So the sigil is expanded.
  // ⚠ Derived from the LOCALISED label — the DE and FI labels carry the sigil too, so deriving from
  // the English one would title a Finnish board in English. That is the failure this asserts.
  const { boardTitle } = await import("../src/i18n/strings.ts");
  const key = "metrics.goals_per_match.label";
  assert.equal(boardTitle("en", key), "Goals per match");
  assert.equal(boardTitle("de", key), "Tore pro Spiel");
  assert.equal(boardTitle("fi", key), "Maalit ottelua kohden");
  for (const lang of ["en", "de", "fi"]) {
    assert.ok(!boardTitle(lang, key).includes("Ø"),
      `${lang} board title still carries the sigil it is supposed to expand`);
  }
});

test("every team board label the block renders is a bare sigil label, not a windowed one",
  async () => {
  // ⛔ REPLACES a test that fed `boardTitle` a per-90 metric id and asserted it came back
  // unexpanded. That test pinned the WRONG guard: `boardTitle` used to read
  // `metricId.endsWith("_per_match")`, which is a taxonomy judgement made in the frontend from
  // an id's spelling — which this catalogue already proves
  // unsafe (`shots_on_goal_per_match` carries `metrics.shots_on_target_per_match.label`).
  //
  // The real premise is that the four boards this block renders are per-match rates, and that is
  // asserted against the catalogue's own data in `test_the_team_board_set_is_all_per_match_rates`
  // (`denominator_expr = count(*)`). What is left for THIS file is the display half of the same
  // premise: those four labels must be bare `Ø <noun>` strings, because expanding one that already
  // states its window would read "Ø Goals per 90 per match".
  const { boardTitle, metricLabel, t } = await import("../src/i18n/strings.ts");
  const boards = ["goals_per_match", "shots_on_goal_per_match", "passes_per_match",
                  "duels_per_match"];
  const rows = catalogueRows();
  for (const id of boards) {
    const row = rows.find((r) => r.metric_id === id && r.entity === "team");
    assert.ok(row, `${id} is not a team metric in the catalogue`);
    for (const lang of ["en", "de", "fi"]) {
      const label = metricLabel(lang, row.label_i18n_key);
      assert.ok(label.startsWith("Ø "),
        `${lang} label for ${id} is "${label}" — no sigil for the heading to expand`);

      // The window must appear EXACTLY ONCE in the heading. A label that already stated its own
      // window would read "Ø Goals per 90 per match"; this counts rather than pattern-matches, so
      // it needs no per-locale list of window words.
      const title = boardTitle(lang, row.label_i18n_key);
      const window = t(lang, "perMatch");
      assert.equal(title.split(window).length - 1, 1,
        `${lang} heading for ${id} is "${title}" — "${window}" must appear exactly once`);
      assert.ok(!title.includes("Ø"), `${lang} heading for ${id} kept the sigil: "${title}"`);
    }
  }
});

test("metricRows.ts no longer carries an English label", () => {
  assert.ok(!/^\s*label:/m.test(rowsSrc),
    "metricRows.ts still declares `label:` — a metric name must live in one place only");
  assert.ok(!/\blabel:\s*"/.test(rowsSrc),
    "metricRows.ts still has an inline label string");
});
