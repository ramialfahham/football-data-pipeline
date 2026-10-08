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
const servedRows = JSON.parse(readFileSync(join(SITE, "src/data/metric_rows.json"), "utf8")).rows;
const rowKeys = [
  ...[...rowsSrc.matchAll(/labelKey:\s*"(metrics\.[A-Za-z0-9_]+\.label)"/g)].map((m) => m[1]),
  ...servedRows.map((r) => r.label_i18n_key),
];
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
 * from the payload by design, so a payload-derived list would make a legitimately empty board
 * turn this test red — a
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

test("no metric name carries a sigil, in any locale", () => {
  const bad = [];
  for (const loc of LOCALES) {
    for (const [key, val] of labels[loc]) {
      if (/[Ø%]/.test(val)) bad.push(`${loc} ${key}: "${val}"`);
    }
  }
  assert.deepEqual(bad, [], `a name carries Ø or %; its second line says "per match" or "percentage":\n  ${bad.join("\n  ")}`);
});

/** The catalogue's rows by (metric_id, entity), parsed with quoted fields (descriptions hold commas). */
function catalogueByKey() {
  const text = readFileSync(join(REPO, "dbt_project/seeds/metric_catalogue.csv"), "utf8");
  const rows = [];
  for (const line of text.split(/\r?\n/).filter(Boolean)) {
    rows.push([...line.matchAll(/("(?:[^"]|"")*"|[^,]*)(?:,|$)/g)].map((m) => m[1].replace(/^"|"$/g, "")).slice(0, -1));
  }
  const header = rows[0];
  const col = (r, name) => r[header.indexOf(name)];
  return new Map(rows.slice(1).map((r) => [`${col(r, "metric_id")}|${col(r, "entity")}`, {
    denominator: col(r, "denominator_expr"), format: col(r, "format"), key: col(r, "label_i18n_key"),
  }]));
}

test("the site's per-match flags and share list agree with the catalogue", () => {
  // Copies of catalogue facts, held here until the export serves them: each must match its row.
  const cat = catalogueByKey();
  // A per-match average divides by the matches and is not a share (clean_sheets_pct divides by the
  // matches too, but it is a share).
  const perMatch = (id) => cat.get(`${id}|team`)?.denominator === "count(*)" && cat.get(`${id}|team`)?.format !== "percent";
  const flags = [...rowsSrc.matchAll(/field: "([a-z_]+)", labelKey: "[^"]+"[^}]*?perMatch: (true|false)/g)];
  assert.ok(flags.length >= 17, `expected the 16 rows and the team binding, parsed ${flags.length}`);
  for (const [, field, flag] of flags) {
    assert.ok(cat.has(`${field}|team`), `metricRows.ts field ${field} is not a team catalogue metric`);
    assert.equal(flag === "true", perMatch(field), `metricRows.ts perMatch for ${field} disagrees with the catalogue`);
  }
  for (const id of ["shots_on_goal_per_match", "shots_on_goal_against_per_match", "shots_on_goal_difference_per_match"]) {
    assert.ok(perMatch(id), `the team hero tile ${id} says "per match" but the catalogue does not define it so`);
  }
  const shares = [...strings.match(/SHARE_NAMED_BY_ITS_COUNT = new Set\(\[([\s\S]*?)\]\)/)[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]);
  const byKey = new Map([...cat.values()].map((r) => [r.key, r]));
  for (const key of shares) {
    assert.equal(byKey.get(key)?.format, "percent", `${key} is listed as a share but is not a percent metric`);
  }
});

test("a share named by its count says percentage; a per-match value says per match", async () => {
  const { metricSubline, t } = await import("../src/i18n/strings.ts");
  for (const lang of ["en", "de", "fi"]) {
    assert.equal(metricSubline(lang, "metrics.duels_won_pct.label", false), t(lang, "percentage"));
    assert.equal(metricSubline(lang, "metrics.passes_accuracy_pct.label", false), "",
      "a share with a football word of its own has no second line");
    assert.equal(metricSubline(lang, "metrics.goals_per_match.label", true), t(lang, "perMatch"));
    assert.equal(metricSubline(lang, "metrics.clean_sheets.label", false), "",
      "a count has no second line");
  }
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
  // A bare "Goals" reads as a season total, so a per-match board says so in its title.
  const { boardTitle } = await import("../src/i18n/strings.ts");
  const key = "metrics.goals_per_match.label";
  assert.equal(boardTitle("en", key, true), "Goals per match");
  assert.equal(boardTitle("de", key, true), "Tore pro Spiel");
  assert.equal(boardTitle("fi", key, true), "Maalit ottelua kohden");
  assert.equal(boardTitle("en", "metrics.duels_won_pct.label", false), "Duels won percentage");
  assert.equal(boardTitle("de", "metrics.passes_accuracy_pct.label", false), "Passquote");
});

test("every team board label the block renders states no window of its own",
  async () => {
  // The four Home boards are per-match rates (asserted against the catalogue's denominator in
  // `test_the_team_board_set_is_all_per_match_rates`); their names must not state a window, or the
  // title would read "Goals per 90 per match".
  const { boardTitle, metricLabel, t } = await import("../src/i18n/strings.ts");
  const boards = ["goals_per_match", "shots_on_goal_per_match", "passes_per_match",
                  "duels_per_match"];
  const rows = catalogueRows();
  for (const id of boards) {
    const row = rows.find((r) => r.metric_id === id && r.entity === "team");
    assert.ok(row, `${id} is not a team metric in the catalogue`);
    for (const lang of ["en", "de", "fi"]) {
      const label = metricLabel(lang, row.label_i18n_key);
      assert.ok(label, `${lang} has no name for ${id}`);
      // The window must appear EXACTLY ONCE in the heading; counting needs no per-locale word list.
      const title = boardTitle(lang, row.label_i18n_key, true);
      const window = t(lang, "perMatch");
      assert.equal(title, `${label} ${window}`);
      assert.equal(title.split(window).length - 1, 1,
        `${lang} heading for ${id} is "${title}" — "${window}" must appear exactly once`);
    }
  }
});

/** The site code the Form comparison reads: its component, and every .astro/.ts/.mjs file it
 *  imports, followed through their imports. Data files (.json) are the export's and are not code. */
function formComparisonCode() {
  const seen = new Map();
  const visit = (file) => {
    if (seen.has(file)) return;
    const text = readFileSync(file, "utf8");
    seen.set(file, text);
    const specs = /(?:\bfrom\s+|\bimport\s*\(?\s*)["'](\.{1,2}\/[^"']+)["']/g;
    for (const [, spec] of text.matchAll(specs)) {
      if (/\.(astro|ts|mjs)$/.test(spec)) visit(join(dirname(file), spec));
      else if (!/\.json$/.test(spec)) visit(join(dirname(file), `${spec}.ts`));
    }
  };
  visit(join(SITE, "src/components/fixture/MetricComparison.astro"));
  return seen;
}

/** The catalogue metric ids a text spells as a string literal in code. Comments are not code. In the
 *  copy file a line such as `goals: "goals"` is a word for the reader, so it does not count there. */
function spelledMetricIds(text, ids, isCopy = false) {
  let code = text.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
  if (isCopy) code = code.replace(/^\s*[a-z][A-Za-z0-9]*:\s*"[^"]*",?\s*$/gm, "");
  return [...code.matchAll(/["'`]([a-z0-9_]+)["'`]/g)].map((m) => m[1]).filter((s) => ids.has(s));
}

test("the Form comparison and the site code it reads spell no metric", () => {
  const ids = new Set(catalogueRows().map((r) => r.metric_id));
  assert.ok(ids.size >= 80, `parsed only ${ids.size} metric ids from the catalogue`);
  assert.deepEqual(spelledMetricIds(`x = "goals_per_match"`, ids), ["goals_per_match"],
    "the literal finder no longer finds a metric id");
  assert.deepEqual(spelledMetricIds(`  { field: "goals_per_match", order: 1 },`, ids), ["goals_per_match"],
    "the literal finder no longer finds a metric id in a row definition");
  assert.deepEqual(spelledMetricIds(`const row = {\n  field: "goals_per_match",\n  order: 1,\n};`, ids), ["goals_per_match"],
    "the literal finder no longer finds a metric id on a line of its own");
  const copyFile = join(SITE, "src/i18n/strings.ts");
  const code = formComparisonCode();
  assert.ok(code.size >= 5, `followed only ${code.size} files from MetricComparison.astro`);
  const bad = [...code].flatMap(([file, text]) =>
    spelledMetricIds(text, ids, file === copyFile).map((id) => `${file.slice(SITE.length + 1)}: "${id}"`));
  assert.deepEqual(bad, [],
    `the Form comparison's rows, order, direction and format are served by src/data/metric_rows.json; ` +
    `site code spells a metric:\n  ${bad.join("\n  ")}`);
});

test("metricRows.ts no longer carries an English label", () => {
  assert.ok(!/^\s*label:/m.test(rowsSrc),
    "metricRows.ts still declares `label:` — a metric name must live in one place only");
  assert.ok(!/\blabel:\s*"/.test(rowsSrc),
    "metricRows.ts still has an inline label string");
});
