// Metric labels resolve from the catalogue, per locale (#370).
//
// Runs in `npm test`, which `prebuild` runs, so this gates the BUILD and not only CI. Each test below
// is one of the acceptance criteria the CPO locked on 2026-07-31.
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

/** The `metrics.*.label` keys inside one METRIC_LABELS_<loc> block. */
function labelBlock(loc) {
  const m = strings.match(
    new RegExp(`const METRIC_LABELS_${loc}: MetricLabels = \\{([\\s\\S]*?)\\n\\};`));
  assert.ok(m, `METRIC_LABELS_${loc} not found in strings.ts`);
  const out = new Map();
  for (const [, key, val] of m[1].matchAll(/"(metrics\.[A-Za-z0-9_]+\.label)":\s*"((?:[^"\\]|\\.)*)"/g)) {
    out.set(key, val);
  }
  return out;
}

const labels = Object.fromEntries(LOCALES.map((l) => [l, labelBlock(l)]));
const rowKeys = [...rowsSrc.matchAll(/labelKey:\s*"(metrics\.[A-Za-z0-9_]+\.label)"/g)].map((m) => m[1]);
const heroKeys = [...readFileSync(join(SITE, "src/components/team/DeservedHero.astro"), "utf8")
  .matchAll(/metricLabel\(lang,\s*"(metrics\.[A-Za-z0-9_]+\.label)"\)/g)].map((m) => m[1]);

test("every metric name the page asks for resolves in all three locales", () => {
  const asked = [...new Set([...rowKeys, ...heroKeys])];
  assert.ok(asked.length >= 18, `expected >=18 metric names in use, found ${asked.length}`);
  for (const loc of LOCALES) {
    const missing = asked.filter((k) => !labels[loc].get(k));
    assert.deepEqual(missing, [],
      `${loc} has no label for: ${missing.join(", ")}. t()'s sibling metricLabel() falls back to ` +
      `English, so a gap here silently ships English to a ${loc} reader.`);
  }
});

test("no locale carries a label nothing renders, and none is empty", () => {
  const asked = new Set([...rowKeys, ...heroKeys]);
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
  // label_i18n_key `metrics.shots_on_target_per_match.label` (internal id "on goal", user-facing term
  // "on target"), so an id-based check calls the real key dangling and an invented one valid.
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
  const asked = [...new Set([...rowKeys, ...heroKeys])];
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
      // EN diverges for finishing_efficiency by design: v2's locked label is kept and the corpus's
      // "% Conversion rate" is a §10 pick reserved to the CPO. Recorded in the task contract.
      if (loc === "EN" && id === "finishing_efficiency") continue;
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
  const theirs = new Set([...keys].filter((k) => /^metrics\./.test(k)));
  const mine = new Set(labels.EN.keys());
  assert.deepEqual([...theirs].sort(), [...mine].sort(),
    "the two metric-key parsers disagree; one of the regexes has drifted");
});

test("metricRows.ts no longer carries an English label", () => {
  assert.ok(!/^\s*label:/m.test(rowsSrc),
    "metricRows.ts still declares `label:` — a metric name must live in one place only");
  assert.ok(!/\blabel:\s*"/.test(rowsSrc),
    "metricRows.ts still has an inline label string");
});
