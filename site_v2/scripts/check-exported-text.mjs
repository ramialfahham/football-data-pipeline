#!/usr/bin/env node
// The exported-text check: no value in `src/data` is text decoded in the wrong character set. The
// provider sends such text and `repair_garbled_text` repairs it in base, so a value that reaches
// this check is one the repair missed. `prebuild` runs it, so a build of the committed sample and
// a build of the full export both stop here.
//
//   node scripts/check-exported-text.mjs [dataDir]

import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

export const DATA_DIR = join(fileURLToPath(new URL(".", import.meta.url)), "..", "src", "data");

const WINDOWS_1252 = "€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•–—˜™š›œžŸ";
const CONTINUATION = `[\\u0080-\\u00BF${WINDOWS_1252}]`;

// The same sequences as the macro, plus the two marks of a failed decode: a C1 control character
// and the replacement character.
export const GARBLED = new RegExp(
  `[\\u00C2-\\u00CB]${CONTINUATION}|[\\u00E1\\u00E2][\\u0080-\\u00BF€]${CONTINUATION}|[\\u0080-\\u009F\\uFFFD]`,
);

/** Every string in a parsed JSON value that holds garbled text, keys included, with its path. */
export function garbledValues(value, path = "$") {
  if (typeof value === "string") return GARBLED.test(value) ? [{ path, text: value }] : [];
  if (Array.isArray(value)) return value.flatMap((item, i) => garbledValues(item, `${path}[${i}]`));
  if (value === null || typeof value !== "object") return [];
  return Object.entries(value).flatMap(([key, item]) => [
    ...garbledValues(key, `${path}.<key>`),
    ...garbledValues(item, `${path}.${key}`),
  ]);
}

function jsonFiles(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return jsonFiles(path);
    return entry.name.endsWith(".json") ? [path] : [];
  });
}

/** Each garbled value under `dataDir`, with its file; the count of files read. */
export function scanData(dataDir) {
  const files = jsonFiles(dataDir);
  const findings = files.flatMap((file) =>
    garbledValues(JSON.parse(readFileSync(file, "utf8"))).map((hit) => ({ file: relative(dataDir, file), ...hit })),
  );
  return { files: files.length, findings };
}

function main() {
  const dataDir = process.argv[2] ?? DATA_DIR;
  const { files, findings } = scanData(dataDir);
  if (findings.length > 0) {
    console.error(`check-exported-text: ${findings.length} value(s) decoded in the wrong character set:\n`);
    for (const { file, path, text } of findings) console.error(`  - ${file} ${path}: ${JSON.stringify(text)}`);
    process.exit(1);
  }
  console.log(`check-exported-text: ${files} file(s) read, no garbled text. OK.`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
