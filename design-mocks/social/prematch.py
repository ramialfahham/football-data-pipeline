"""The German pre-match image of one match, 1080x1350, from the marts and the frozen `assets/`.

    python design-mocks/social/prematch.py <fixture_slug>
    -> design-mocks/social/out/<fixture_slug>/<fixture_slug>_linkedin.png
"""
import argparse
import datetime as dt
import html
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
OUT = HERE / "out"

PROJECT = "football-data-pipeline-gcp"
MARTS = f"{PROJECT}.marts"
CREST_BUCKET = "football-data-pipeline-gcp-crests"
MAX_BYTES = 1_000_000_000

WINDOW = 5
# (mart column, label, format, which side is better)
METRICS = (
    ("goals_per_match", "Tore", "avg", "high"),
    ("goals_against_per_match", "Gegentore", "avg", "low"),
    ("shots_on_goal_per_match", "Schüsse aufs Tor", "avg", "high"),
    ("shots_on_goal_against_per_match", "Schüsse aufs Tor gegen", "avg", "low"),
    ("shots_inside_box_pct", "Schüsse aus dem Strafraum", "pct", "high"),
    ("finishing_efficiency_pct", "Abschlussquote", "pct", "high"),
    ("passes_share_pct", "Ballbesitz", "pct", "high"),
)
# The German short forms of Intl's de-DE, which the site prints.
WEEKDAYS = ("Mo.", "Di.", "Mi.", "Do.", "Fr.", "Sa.", "So.")
MONTHS = ("Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez.")

QUERIES = {
    "fixture": f"""
        select fixture_sk, fixture_slug, league_code, status_short, round_label_i18n_key,
               round_number, kickoff_local, kickoff_zone_label, venue_name,
               home_team_sk, home_team_name, away_team_sk, away_team_name,
               is_home_team_next_match, is_away_team_next_match
        from `{MARTS}.mart_competition_fixtures`
        where fixture_slug = @slug""",
    "window": f"""
        select team_sk, window_type, games_in_window, games_with_team_stats,
               contributing_competitions, {", ".join(m[0] for m in METRICS)}
        from `{MARTS}.mart_team_window_metrics`
        where fixture_sk = @fixture_sk""",
    "standing": f"""
        select team_sk, is_knockout, league_rank, standing_points, standing_goals_diff
        from `{MARTS}.mart_fixture_standing_context`
        where fixture_sk = @fixture_sk""",
    "competitions": f"""
        select league_code, competition_name
        from `{MARTS}.mart_competition_index`""",
}


class Refused(Exception):
    """The match cannot be drawn: a value the image states is missing or does not hold."""


def need(row, key, where):
    value = row.get(key)
    if value is None or value == "" or (isinstance(value, float) and not math.isfinite(value)):
        raise Refused(f"{where}: `{key}` has no value")
    return value


def one(rows, where):
    if len(rows) != 1:
        raise Refused(f"{where}: expected exactly one row, found {len(rows)}")
    return rows[0]


def fetch(slug):
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT)

    def config(params, **kwargs):
        return bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter(*p) for p in params], **kwargs
        )

    placeholder = {"fixture": [("slug", "STRING", slug)], "competitions": []}
    estimate = 0
    for name, sql in QUERIES.items():
        params = placeholder.get(name, [("fixture_sk", "INT64", 0)])
        job = client.query(sql, job_config=config(params, dry_run=True, use_query_cache=False))
        estimate += job.total_bytes_processed
    print(f"BigQuery dry run: {estimate / 1e6:.1f} MB")
    if estimate >= MAX_BYTES:
        raise Refused(f"the read would be {estimate / 1e6:.0f} MB; the limit is {MAX_BYTES / 1e6:.0f} MB")

    billed = 0

    def run(name, params):
        nonlocal billed
        job = client.query(QUERIES[name], job_config=config(params, maximum_bytes_billed=MAX_BYTES))
        rows = [dict(r) for r in job.result()]
        billed += job.total_bytes_billed or 0
        return rows

    fixtures = run("fixture", [("slug", "STRING", slug)])
    fixture = one(fixtures, f"fixture `{slug}`")
    sk = [("fixture_sk", "INT64", int(need(fixture, "fixture_sk", "fixture")))]
    data = {
        "fixture": fixture,
        "window": run("window", sk),
        "standing": run("standing", sk),
        "competitions": run("competitions", []),
    }
    print(f"BigQuery billed: {billed / 1e6:.1f} MB")
    return json.loads(json.dumps(data, default=str, ensure_ascii=False))


def model(data):
    """Every value the image states, checked. Raises `Refused` instead of leaving a gap."""
    fx = data["fixture"]
    if need(fx, "status_short", "fixture") != "NS":
        raise Refused(f"fixture: status is `{fx['status_short']}`, not a scheduled kickoff (`NS`)")
    if need(fx, "round_label_i18n_key", "fixture") != "compFactMatchday":
        raise Refused(f"fixture: the round is `{fx['round_label_i18n_key']}`, not a numbered matchday")
    # With an earlier match still open, the window is not yet the last five before this one.
    for side in ("home", "away"):
        if fx.get(f"is_{side}_team_next_match") is not True:
            raise Refused(f"fixture: this is not the {side} team's next match, so its last {WINDOW} can still change")

    names = {r["league_code"]: r.get("competition_name") for r in data["competitions"]}

    def competition(code):
        return need(names, code, "mart_competition_index name of competition")

    league = need(fx, "league_code", "fixture")
    teams, contributing = [], []
    for side in ("home", "away"):
        sk = need(fx, f"{side}_team_sk", "fixture")
        name = need(fx, f"{side}_team_name", "fixture")

        stand = one([r for r in data["standing"] if r["team_sk"] == sk], f"standing of {name}")
        if stand.get("is_knockout") is not False:
            raise Refused(f"standing of {name}: a knockout round has no table position")

        window = one(
            [r for r in data["window"] if r["team_sk"] == sk and r.get("window_type") == "last_5"],
            f"last_5 window of {name}",
        )
        for key in ("games_in_window", "games_with_team_stats"):
            if need(window, key, f"window of {name}") != WINDOW:
                raise Refused(f"window of {name}: `{key}` is {window[key]}, the image says {WINDOW}")
        codes = window.get("contributing_competitions")
        if not codes:
            raise Refused(f"window of {name}: `contributing_competitions` has no value")
        contributing += codes

        teams.append({
            "sk": sk,
            "name": name,
            "rank": need(stand, "league_rank", f"standing of {name}"),
            "points": need(stand, "standing_points", f"standing of {name}"),
            "goal_diff": need(stand, "standing_goals_diff", f"standing of {name}"),
            "metrics": {m[0]: need(window, m[0], f"window of {name}") for m in METRICS},
        })

    # The match's own competition leads; the others follow in the order of their names.
    codes = sorted(set(contributing), key=lambda c: (c != league, competition(c)))
    kickoff = dt.datetime.fromisoformat(str(need(fx, "kickoff_local", "fixture")))
    return {
        "league": competition(league),
        "matchday": need(fx, "round_number", "fixture"),
        "date": f"{WEEKDAYS[kickoff.weekday()]}, {kickoff.day}. {MONTHS[kickoff.month - 1]} {kickoff.year}",
        "clock": f"{kickoff:%H:%M} {need(fx, 'kickoff_zone_label', 'fixture')}",
        "venue": need(fx, "venue_name", "fixture"),
        "window_competitions": [competition(c) for c in codes],
        "home": teams[0],
        "away": teams[1],
    }


def esc(value):
    return html.escape(str(value), quote=False)


def joined(items):
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " und " + items[-1]


def rounded(value, step):
    # The Match page's Intl formats round an exact half up; Python's own formats round it to even.
    return str(Decimal(str(value)).quantize(Decimal(step), rounding=ROUND_HALF_UP))


def fmt(value, kind):
    if kind == "pct":
        # A float product, as the Match page multiplies before it formats.
        return rounded(value * 100, "1") + "%"
    return rounded(value, "0.1").replace(".", ",")


def logo():
    mark = (ASSETS / "mark.svg").read_text(encoding="utf-8").strip()
    word = (ASSETS / "wordmark.svg").read_text(encoding="utf-8").strip()
    word_w = float(re.search(r'viewBox="\S+ \S+ (\S+) \S+"', word).group(1))
    total = 150 + 9 + word_w
    return (
        f'<svg class="li-logo" viewBox="0 0 {total} 150" style="width:{total / 150 * 1.5:.3f}em">'
        + mark.replace("<svg ", '<svg x="0" y="0" width="150" height="150" ')
        + word.replace("<svg ", f'<svg x="159" y="0" width="{word_w}" height="150" ')
        + "</svg>"
    )


def team_block(team):
    lead, _, last = team["name"].rpartition(" ")
    name = (f"{esc(lead)} " if lead else "") + f'<span class="nb">{esc(last)}</span>'
    diff = f'{team["goal_diff"]:+d}'.replace("-", "\u2212") if team["goal_diff"] else "0"
    points = "Punkt" if team["points"] == 1 else "Punkte"
    return (
        f'<div class="team"><div class="crest"><img src="crests/{team["sk"]}-104.webp" alt="" width="52" height="52">'
        f'</div><span class="tname">{name}</span>'
        f'<div class="stand num facts-line"><span class="nb">#<b>{team["rank"]}</b></span>'
        f'<span class="nb"><b>{team["points"]}</b> {points}</span>'
        f'<span class="nb">Diff. <b>{diff}</b></span></div></div>'
    )


def metric_row(home, away, column, label, kind, better):
    h, a = home["metrics"][column], away["metrics"][column]
    hd, ad = fmt(h, kind), fmt(a, kind)
    side = None
    if hd != ad:
        side = "home" if (h > a) == (better == "high") else "away"
    top = max(h, a) or 1
    hc = " chart-better" if side == "home" else ""
    ac = " chart-better" if side == "away" else ""
    sub = '<span class="chart-tick">pro Spiel</span>' if kind == "avg" else ""
    return (
        f'<div class="cmp-row"><div class="cmp-val cmp-home{hc}">{hd}</div><div class="cmp-mid">'
        f'<div class="cmp-label"><span class="chart-name">{label}</span>{sub}</div>'
        f'<div class="chart-bar"><span class="{hc.strip()}"><span style="width:{round(h / top * 100)}%"></span></span>'
        f'<span class="{ac.strip()}"><span style="width:{round(a / top * 100)}%"></span></span></div></div>'
        f'<div class="cmp-val cmp-away{ac}">{ad}</div></div>'
    )


def page(m):
    rows = "".join(metric_row(m["home"], m["away"], *metric) for metric in METRICS)
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><title>{esc(m["home"]["name"])} – {esc(m["away"]["name"])}</title>
<link rel="stylesheet" href="site.css">
<link rel="stylesheet" href="layout.css">
</head>
<body class="fx" data-theme="dark"><main class="li">
<div class="li-brand">{logo()}</div>
<header class="mast">
<div class="status-word">Spielvorschau · {esc(m["league"])}</div>
<div class="kick facts-line"><span>{m["matchday"]}. Spieltag</span><span>{m["date"]}</span><span>{esc(m["clock"])}</span><span>{esc(m["venue"])}</span></div>
<div class="teams">{team_block(m["home"])}<div class="vs">gegen</div>{team_block(m["away"])}</div>
</header>
<section>
<div class="sechead"><span class="eyebrow">Formvergleich</span></div>
<p class="li-note">Letzte {WINDOW} Pflichtspiele · {esc(joined(m["window_competitions"]))}</p>
<div class="cmp">{rows}</div>
</section>
</main>
</body></html>"""


def fetch_crests(team_sks, folder):
    from google.cloud import storage

    bucket = storage.Client(project=PROJECT).bucket(CREST_BUCKET)
    folder.mkdir(parents=True, exist_ok=True)
    for sk in team_sks:
        name = f"{sk}-104.webp"
        content = bucket.blob(f"teams/{name}").download_as_bytes()
        if not content:
            raise Refused(f"crest teams/{name} is empty")
        (folder / name).write_bytes(content)


def find_edge():
    for candidate in (
        shutil.which("msedge"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ):
        if candidate and Path(candidate).is_file():
            return candidate
    raise Refused("Microsoft Edge is not installed in a known place")


def png_size(path):
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise Refused(f"{path.name} is not a PNG")
    return struct.unpack(">II", header[16:24])


def png_complete(path):
    return path.is_file() and path.read_bytes().endswith(b"IEND\xaeB`\x82")


def stop(process):
    if process.poll() is None:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False)
        else:
            process.kill()
        process.wait(timeout=30)


def run_until_written(command, target, timeout=120):
    # Headless Edge sometimes stays alive after writing the screenshot, so the file ends the wait.
    process = subprocess.Popen(
        command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    deadline = time.monotonic() + timeout
    try:
        while not png_complete(target):
            if process.poll() not in (None, 0):
                raise Refused(f"Edge failed with exit code {process.returncode}")
            if time.monotonic() > deadline:
                raise Refused(f"Edge wrote no screenshot within {timeout} seconds")
            time.sleep(0.2)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
    finally:
        stop(process)


def screenshot(source, target):
    target.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        run_until_written(
            [find_edge(), "--headless", "--disable-gpu", "--no-first-run", f"--user-data-dir={profile}",
             "--window-size=540,675", "--force-device-scale-factor=2", "--disable-lcd-antialiasing",
             "--allow-file-access-from-files", f"--screenshot={target}", source.as_uri()],
            target,
        )
    if png_size(target) != (1080, 1350):
        raise Refused(f"the screenshot is {png_size(target)}, not 1080x1350")


def build(data, slug, folder):
    m = model(data)
    markup = page(m)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{slug}_linkedin.png"
    target.unlink(missing_ok=True)
    for name in ("site.css", "layout.css", "InterVariable.woff2"):
        shutil.copyfile(ASSETS / name, folder / name)
    fetch_crests((m["home"]["sk"], m["away"]["sk"]), folder / "crests")
    source = folder / "index.html"
    source.write_text(markup, encoding="utf-8")
    screenshot(source, target)
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slug", help="fixture_slug, e.g. 2026-11-28-home-vs-away")
    parser.add_argument("--data", type=Path, help="draw from a saved data.json instead of reading BigQuery")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug):
        parser.error("a fixture slug is lowercase words and digits joined by '-'")
    folder = OUT / args.slug
    try:
        if args.data:
            data = json.loads(args.data.read_text(encoding="utf-8"))
            if data["fixture"].get("fixture_slug") != args.slug:
                raise Refused(f"{args.data} holds another match")
        else:
            (folder / f"{args.slug}_linkedin.png").unlink(missing_ok=True)
            data = fetch(args.slug)
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        target = build(data, args.slug, folder)
    except Refused as why:
        print(f"REFUSED: {why}", file=sys.stderr)
        return 1
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
