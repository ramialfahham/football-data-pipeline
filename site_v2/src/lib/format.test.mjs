// Pins the kick-off clock a match row prints: the served venue wall clock and its zone label,
// read as the digits they show on every machine; a row served without them keeps its UTC kick-off.

import { test } from "node:test";
import assert from "node:assert/strict";
import { formatDate, formatTime, kickoffClock, kickoffDay } from "./format.ts";

const SERVED = {
  kickoff: "2026-11-21 23:30:00+00:00",
  kickoff_local: "2026-11-22 00:30:00",
  kickoff_zone_label: "CET",
};

test("a row prints its served local kick-off and its zone label", () => {
  assert.deepEqual(kickoffClock(SERVED), { at: "2026-11-22 00:30:00", zone: "CET" });
  assert.equal(formatTime(kickoffClock(SERVED).at, "en"), "00:30");
});

test("a served wall clock is read as its digits, whatever the machine's zone", () => {
  const was = process.env.TZ;
  try {
    for (const zone of ["America/Los_Angeles", "Asia/Tokyo", "UTC"]) {
      process.env.TZ = zone;
      assert.equal(formatTime("2026-07-05 20:00:00", "en"), "20:00");
    }
  } finally {
    if (was === undefined) delete process.env.TZ;
    else process.env.TZ = was;
  }
});

test("the day heading groups a row under the date of its local clock", () => {
  assert.equal(kickoffDay(SERVED), "2026-11-22");
  assert.match(formatDate(kickoffClock(SERVED).at, "en"), /22/);
});

test("a row served without a local clock keeps its UTC kick-off and says UTC", () => {
  const row = { kickoff: "2026-11-21 23:30:00+00:00" };
  assert.deepEqual(kickoffClock(row), { at: "2026-11-21 23:30:00+00:00", zone: "UTC" });
  assert.equal(formatTime(kickoffClock(row).at, "en"), "23:30");
  assert.equal(kickoffDay(row), "2026-11-21");
});

test("a row with a local clock and no label says UTC, never a blank", () => {
  assert.equal(kickoffClock({ kickoff_local: "2026-11-22 00:30:00" }).zone, "UTC");
});

test("a row with no kick-off at all has no clock and no day", () => {
  assert.deepEqual(kickoffClock({}), { at: null, zone: "UTC" });
  assert.equal(kickoffDay({}), null);
});
