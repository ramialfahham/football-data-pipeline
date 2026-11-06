import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { GARBLED, garbledValues, scanData } from "./check-exported-text.mjs";

const SCRIPT = fileURLToPath(new URL("./check-exported-text.mjs", import.meta.url));

for (const [form, text] of [
  ["the Latin-1 form", "A. MaksimoviÄ\u0087"],
  ["the Windows-1252 form", "Dominik MartinoviÄ‡"],
  ["a lead with a printable continuation", "Rafael LuÃ­s"],
  ["a three-byte sequence", "N. Lâ\u0080\u0099Huillier"],
  ["a stray control character", "N. Kovač \u008D"],
  ["the replacement character", "K. Urba�ski"],
]) {
  test(`${form} is garbled`, () => assert.match(text, GARBLED));
}

for (const [what, text] of [
  ["a correct name with carons", "M. Ljubičić"],
  ["a correct name beside a no-break space", "Tomáš Vaclík"],
  ["German umlauts and a sharp s before a closing quote", "„Fuß“ für Mönchengladbach"],
  ["Finnish letters", "Pääsarja Ässät"],
  ["a typographic apostrophe", "N. L’Huillier"],
  ["Vietnamese letters", "Nguyễn Sỹ Đức"],
]) {
  test(`${what} is not garbled`, () => assert.doesNotMatch(text, GARBLED));
}

test("garbledValues finds a value at any depth, and a garbled key, with their paths", () => {
  const found = garbledValues({ a: [{ name: "L. JovanoviÄ\u0087" }], "LuÃ­s": 1, ok: "Plain", n: null });
  assert.deepEqual(found.map((f) => f.path), ["$.a[0].name", "$.<key>"]);
});

function dataDir(payload) {
  const dir = mkdtempSync(join(tmpdir(), "exported-text-"));
  mkdirSync(join(dir, "teams"));
  writeFileSync(join(dir, "teams", "1.json"), JSON.stringify(payload));
  return dir;
}

test("scanData reads nested folders and names the file", () => {
  const dir = dataDir({ name: "J. PotoÄ\u008Dnik" });
  try {
    const { files, findings } = scanData(dir);
    assert.equal(files, 1);
    assert.deepEqual(findings.map((f) => f.file), [join("teams", "1.json")]);
  } finally {
    rmSync(dir, { recursive: true });
  }
});

test("the command fails on garbled text and passes on clean text", () => {
  const bad = dataDir({ name: "J. PotoÄ\u008Dnik" });
  const good = dataDir({ name: "J. Potočnik" });
  try {
    assert.equal(spawnSync(process.execPath, [SCRIPT, bad]).status, 1);
    assert.equal(spawnSync(process.execPath, [SCRIPT, good]).status, 0);
  } finally {
    rmSync(bad, { recursive: true });
    rmSync(good, { recursive: true });
  }
});
