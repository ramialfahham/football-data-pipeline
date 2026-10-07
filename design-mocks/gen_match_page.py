"""The match page for its design review, state 1 (the next matchday): the BUILT page, and a
proposal that draws every block with the site's shared elements, each change marked and numbered,
with a "Built today" / "Proposed" switch and every block's data source on a toggle.

The page is what `npm run build` emitted for one real match (site_v2/dist, EN), its stylesheet
inlined, in ONE copy: the page's own switches are ids the stylesheet targets, so a second copy
would share them and break both. A changed block carries its built and its proposed form side by
side and the switch shows one. The proposed forms are the block standard's elements in the markup
the built site emits for them: the breadcrumb of the Matchdays tab, THE match row, the fact row, the
board. Every value is a served payload field; where a proposal needs a value the payload does not
serve, the legend names the gap instead of the mock inventing it. Run `npm run build` first.

The page carries the site's own header and adapts as the window is resized, the way it is reviewed:
a label in the top bar names the view (phone, tablet, desktop), and "Link areas" outlines every link.

    python gen_match_page.py [out.html]
"""

import copy
import html
import json
import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DIST = REPO / "site_v2" / "dist"
DATA = REPO / "site_v2" / "src" / "data"

LEAGUE = "bundesliga"
# Which of the page's states the render draws: "next" (the next matchday's match, state 1),
# "future" (a match further out, state 2), "future-unmet" (the same, for a pair the data has not
# seen meet) or "played" (a played match, state 3), set by MATCH_STATE. A played match has no built
# page, so its render takes the next match page's shell: the stylesheet and the site header.
STATE = os.environ.get("MATCH_STATE", "next")
SLUG, FIXTURE_ID = {"next": ("2026-10-09-borussia-dortmund-vs-sv-werder-bremen", 1575176),
                    "future": ("2026-10-31-bayern-munchen-vs-borussia-dortmund", 1575203),
                    "future-unmet": ("2026-11-07-borussia-dortmund-vs-sv-elversberg", 1575212),
                    "played": ("2026-10-09-borussia-dortmund-vs-sv-werder-bremen", 1575150),
                    "played-pen": ("2026-10-09-borussia-dortmund-vs-sv-werder-bremen", 1550700)}[STATE]
PAGE = DIST / "en" / LEAGUE / "matches" / SLUG / "index.html"

E = html.escape
DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec")
POSITIONS = {"G": "Goalkeeper", "D": "Defender", "M": "Midfielder", "F": "Forward"}
POSITION_LABELS = {"G": "Goalkeeper", "D": "Defence", "M": "Midfield", "F": "Forward"}

# Nothing serves a player's season across competitions yet, so the proposed Players to watch shows a
# stand-in read once from mart_player_fixture_stats (this season, every competition, before the
# match; ordered by goals plus assists, then goals, then fewer minutes). Every one of these teams'
# matches carried player stats (Dortmund 6 of 6, Bremen 5 of 5), so the totals are complete.
SEASON_PLAYERS = {
    165: [("S. Guirassy", "F", 4, 2, 21393), ("Fábio Silva", "M", 3, 1, 129791), ("S. Inacio", "F", 2, 0, 478991),
          ("F. Nmecha", "M", 2, 0, 637), ("M. Beier", "F", 1, 1, 158644)],
    162: [("M. Grüll", "F", 2, 4, 7073), ("N. Füllkrug", "F", 4, 0, 25391), ("Chuky San José", "M", 0, 2, 331004),
          ("M. Weiser", "D", 1, 0, 973), ("Dariusz Stalmach", "M", 1, 0, 323507)],
}

# Possession and Fouls join the Form comparison (#132 state 3), and the window's cards are shown; nothing serves
# them for the window yet, so the proposal reads a stand-in read once from the team stat lines of each team's five
# window matches: (Dortmund, Bremen); possession is the team's share of the passes in them, a blank card is 0.
# The rest of Match stats' metrics come from the same lines and the player legs: a count is the mean over the
# matches that carry it, a share the ratio of the sums.
FORM_STANDIN = {"possession": (53, 54), "fouls": (10.8, 11.8), "yellow_cards": (1.8, 1.2), "red_cards": (0.0, 0.0),
                "sog_against": (3.6, 4.0), "sog_share": (35, 43), "box": (14.0, 11.6),
                "dribbles": (17.8, 15.2), "dribbles_pct": (44, 49),
                "shots_off_goal": (6.2, 5.6), "shots_blocked": (5.8, 3.4), "passes_accurate": (416, 459),
                "dribbles_completed": (7.8, 7.4), "duels_won": (48, 49), "saves": (3.0, 2.2),
                "free_kicks": (9.5, 10.0), "offsides": (2.2, 2.2)}

# mart_head_to_head does not serve which side was at home in a past meeting, so the proposed Head to
# head reads it from a stand-in read once from core.fct_fixture: the meeting's day -> its home team.
H2H_HOME = {"2026-05-16": 162, "2026-01-13": 165, "2025-01-25": 165, "2024-08-31": 162, "2024-03-09": 162,
            "2026-02-28": 165, "2025-10-18": 157, "2025-04-12": 157, "2024-11-30": 165, "2024-03-30": 157}

# A fix corrects the page to data it already serves; a proposal changes what the page does.
PROPOSALS = [
    (1, "Breadcrumb", "the site hierarchy's trail (rule A, as you answered): Home &rsaquo; Competitions &rsaquo; Bundesliga &rsaquo; Matchdays &rsaquo; the match, every level above it a link; how it adapts to a phone and a tablet is drawn in the board at the top", "proposal"),
    (2, "Header", "the competition&rsquo;s group head opens it, as Home&rsquo;s Next matches draws it (decided in state 3); each team (crest, name, standing) is one link to its team page, the name carrying the chevron every heading link carries at rest; under 700px the two teams stack, one per line as the match row stacks its sides, so a name of any length fits; fixed with it: the standing never splits a label from its number; the round reads &ldquo;Matchday 5&rdquo; as on the Matchdays tab, and the time carries &ldquo;UTC&rdquo; as every match row does; the venue closes the kick-off line instead of taking a line of its own", "proposal"),
    (3, "Recent matches", "the built result row kept (result &middot; score &middot; opponent, H or A), in two lines: the opponent wraps instead of being cut off, and the competition's name (not its code) and the date sit under it; each row is one link to that match's page (a played match's page, designed in state 3), the whole row, lit on hover, as #129 rules every row link", "proposal"),
    (4, "Players to watch", "the built player row kept (photo, name and position, goals and assists; a goalkeeper's saves and save %), its name wrapping instead of being cut off, the two teams level side by side; the block explained in the site's intro form; each row is one link to the player's page, the whole row, as #129 rules every row link (every player shown gets a page)", "proposal"),
    (5, "Head to head", "the last 5 meetings: the block's intro (the site's block explainer) says how they went, from the served split, then the 5 meetings in the result row of Recent matches without its W/D/L chip, which would take one side: the score first, in the match's order, then both names with the side that was at home first, then the competition and the date with its year; the totals (18 meetings, 11&ndash;5&ndash;2, 36:20 goals), the stacked bar and meetings 6&ndash;10 leave, because the totals count only the meetings inside the data window; fewer meetings: &ldquo;last 3 meetings&rdquo;, &ldquo;last meeting&rdquo;; none in the data: &ldquo;No meetings on record&rdquo; in place of &ldquo;First-ever meeting&rdquo;; each meeting is a played match and, like a Recent matches row, one link to that match's page", "proposal"),
    (6, "Explore", "the block leaves: its chips are no site element, and its links are the header's team names and the breadcrumb's competition", "proposal"),
    (7, "Page foot", "the \"Sample data &middot; v2 preview\" footnote leaves: the page carries real data", "fix"),
    (9, "Form comparison", "Shooting reads its counts, then its two rates, Shots on goal against after Shots on goal; Possession leads Passing, Fouls leads Discipline, whose averages read per match, and no name carries &Oslash; or % (decided in state 3); one window and no switch: This season leaves the match page (its league position and points are in the header's standing, its season averages belong on the team page); each team shows the window the phase rules give it (metrics_context_model.md &sect;3&ndash;4), named in the caption: while a league runs, up to the last 5 matches in all the club's competitions this season, never padded from last season; before a team's first match in it, last season's record in that league; the points (15/15) leave, because points count only inside a league and summed across competitions they mean nothing; the W/D/L pills stay; the 16 rows of the locked contract are unchanged; fixed with it: competition names instead of codes, the W/D/L letters and the Defending sub-label in the page's language", "proposal"),
    (8, "The sentence", "the sentence leaves: it repeats the header and the blocks below, and its &ldquo;met 18 times&rdquo; is not all their meetings, only those inside the data's window; the page's summary for search results stays its description", "proposal"),
]

GAPS = [
    "Players to watch: the board shows the warehouse's rank. mart_player_momentum ranks by row number, "
    "so equal goals would get different ranks; the board needs its dense rank served (the mock shows "
    "the served order's positions).",
    "Head to head: which side was at home in each past meeting is not served; the mock reads it from "
    "a stand-in until mart_head_to_head serves it.",
]

# Every value the reader sees, where the design reads it (mart and column), and what the reader
# sees when it is missing; a gap is where the build today reads something else, or nothing
# guarantees the value. A block is listed once it has been walked through.
SOURCES = {
    "crumb": {
        "rows": [
            ("Home &middot; Competitions", "site text, in each language", "never missing"),
            ("Matchdays, or Rounds for a cup", "site text, chosen by <code>mart_competition_index.competition_type</code> (a domestic league reads Matchdays)",
             "never missing: the column is tested never empty"),
            ("Bundesliga", "<code>mart_competition_index.competition_name</code>",
             "nothing guarantees it (gap 1); the build today falls back to the registry file's name, then the provider's, then the code &ldquo;BL1&rdquo;"),
            ("the four links", "<code>mart_competition_index.slug</code>, with the address words",
             "never missing: tested never empty, and a match page without it is not built"),
            ("Borussia Dortmund vs SV Werder Bremen", "<code>mart_competition_fixtures.home_team_name</code>, <code>.away_team_name</code>",
             "nothing guarantees them (gap 1); an empty name leaves &ldquo; vs &rdquo; with one side blank"),
        ],
        "gaps": [
            "1. No test that the competition name and the two team names are filled in: a not-null test on each of the three columns.",
            "2. The build reads around the marts: the links' slug from the registry file, the team names from the core table "
            "<code>dim_team</code>. It should read the two marts above, which already serve every value.",
        ],
    },
    "mast": {
        "rows": [
            ("Match preview &middot; vs &middot; pts &middot; GD", "site text, in each language", "never missing"),
            ("Matchday 5", "site text &ldquo;Matchday {n}&rdquo; with <code>mart_competition_fixtures.round_order</code>, as the Matchdays tab; "
             "a cup's round: <code>.round_name</code>, the provider's words, until #148", "no number: the provider's round name; no name: left out"),
            ("Fri, 9 Oct 2026 &middot; 18:30 UTC", "<code>mart_competition_fixtures.kickoff_datetime</code>, in UTC until #146; the zone label as on every match row",
             "no time set yet (status TBD): &ldquo;time TBD&rdquo; in place of the time"),
            ("the two names and crests", "<code>mart_competition_fixtures.home_team_name</code>, <code>.away_team_name</code>, "
             "<code>.home_team_logo_url</code>, <code>.away_team_logo_url</code>",
             "a name: not guaranteed (block 1, gap 1); a crest: a monogram of the name (1 side of 1,256 in the sample)"),
            ("the two links", "<code>mart_competition_fixtures.home_team_slug</code>, <code>.away_team_slug</code>",
             "a team with no team page gets no link"),
            ("#1 &middot; 12 pts &middot; GD +7", "<code>mart_fixture_standing_context.league_rank</code>, <code>.standing_points</code>, <code>.standing_goals_diff</code>",
             "no row: no chip. A row without a rank (a cup match: 250 sides in 128 of 628 matches) shows an EMPTY chip today; proposed: no chip"),
            ("Signal Iduna Park", "no mart serves it: the build reads <code>core.fct_fixture.venue_name_snapshot</code>",
             "left out (126 of 628 matches)"),
            ("the competition&rsquo;s head: logo, name, link", "<code>mart_competition_index.competition_name</code>, "
             "<code>.logo_url</code>, the link by <code>.slug</code> (decided in state 3)",
             "the name: not guaranteed (block 1, gap 1); the logo: an empty box"),
        ],
        "gaps": [
            "1. The venue is in no mart: <code>mart_competition_fixtures</code> gains the venue's name.",
            "2. The build reads the header from the core tables (<code>fct_fixture</code>, <code>dim_team</code>) though "
            "<code>mart_competition_fixtures</code> serves everything but the venue, and the fixture payload does not carry the round number.",
            "3. The chip's three columns have no test: a league match whose chip has no rank passes unnoticed.",
        ],
    },
    "Form comparison": {
        "rows": [
            ("the switch, the group names, the 16 labels", "site text, in each language; which rows, their groups and order: the locked "
             "<code>metrics_display.md</code> and <code>metric_catalogue</code>", "never missing"),
            ("which window a team shows", "the phase rules, <code>docs/metrics_context_model.md</code> &sect;3&ndash;4, per team and "
             "competition edition: while it runs, <code>mart_team_momentum</code> (<code>window_type</code> last_5, this season only); "
             "before the team's first match in a league, <code>mart_team_season_record</code> (<code>window_type</code> prev_season)",
             "neither served: the block says there are no matches yet"),
            ("the 16 values, while a league runs", "<code>mart_team_momentum</code>, up to the last 5 finished matches in all the club's competitions this season: "
             "<code>goals_per_match</code>, <code>goals_against_per_match</code>, <code>clean_sheets</code>, <code>shots_per_match</code>, "
             "<code>shots_inside_box_pct</code>, <code>shots_on_goal_per_match</code>, <code>finishing_efficiency_pct</code>, "
             "<code>passes_per_match</code>, <code>passes_accuracy_pct</code>, <code>passes_key_per_match</code>, <code>duels_per_match</code>, "
             "<code>duels_won_pct</code>, <code>defensive_actions_per_match</code>, <code>saves_pct</code>, <code>corners_per_match</code>, "
             "<code>corners_against_per_match</code>",
             "one side missing: &ldquo;&ndash;&rdquo; on that side; both missing: the row is left out"),
            ("the 16 values, before a team's first match in a league", "<code>mart_team_season_record</code>, the same columns, "
             "last season in this league (<code>window_type</code> prev_season)", "as above"),
            ("the link &ldquo;What the metrics mean&rdquo;", "the glossary page: not built, its address a placeholder, its "
             "definitions not written yet (the catalogue's <code>description</code> is technical and English only)",
             "until the page exists, nothing links"),
            ("Discipline: yellow cards, red cards", "nothing serves them for the window: the catalogue's <code>cards_yellow</code>, "
             "<code>cards_red</code> are season totals, and <code>mart_team_momentum</code> has no card columns",
             "shown as &ldquo;&ndash;&rdquo; until served (gap 5)"),
            ("the five W/D/L pills, newest first", "<code>mart_team_momentum_window.result</code>, ordered by <code>recency_rank</code>; "
             "read from the final score, so a win after extra time is W and a match settled on penalties is D",
             "fewer than five: fewer pills"),
            ("incl. DFB-Pokal, UEFA Champions League", "<code>mart_team_momentum.contributing_competitions</code>, named by "
             "<code>mart_competition_index.competition_name</code>", "own competition only: no &ldquo;incl.&rdquo; part"),
        ],
        "gaps": [
            "1. None of the 16 value columns has a not-null test; 11 of them have only a not-negative test, no upper bound "
            "(the 5 percentages are held to 0&ndash;1, clean sheets to 0&ndash;games).",
            "2. The page picks between two marts by phase; the choice is a rule of the matrix, so one mart should serve each "
            "side's window for the match, with its <code>window_type</code>, and the page only show it.",
            "3. The Last 5 caption shows competition codes (&ldquo;DFBP, UCL&rdquo;); the W/D/L letters are English on the German "
            "and Finnish pages (the site says S/U/N and V/T/H elsewhere); the Defending sub-label is English in all three.",
            "4. Every value is rounded in the browser (<code>format.ts</code>); rounding in the browser is the defect #108 names.",
            "5. Discipline needs each team's yellow and red cards over its window: <code>mart_team_momentum</code> gains them "
            "from <code>int_legs__team_match</code>, the source the season totals already use, withheld when a match in the "
            "window has no statistics line.",
        ],
    },
    "Recent matches": {
        "rows": [
            ("Recent matches &middot; the team names", "site text; <code>mart_competition_fixtures.home_team_name</code>, <code>.away_team_name</code>",
             "a name: not guaranteed (block 1, gap 1)"),
            ("which matches, newest first", "<code>mart_team_momentum_window</code>, the same window as the form block, ordered by <code>recency_rank</code>",
             "fewer matches: fewer rows; none: no rows"),
            ("W &middot; D &middot; L", "<code>mart_team_momentum_window.result</code>", "never missing: tested never empty, W/D/L only"),
            ("1&ndash;0", "<code>.goals_for</code>, <code>.goals_against</code>, from the team's side", "not guaranteed (gap 1)"),
            ("VfB Stuttgart &middot; A", "<code>.opponent_name</code>; <code>.home_away</code>", "a name: not guaranteed (gap 1)"),
            ("Bundesliga &middot; 19 Sept", "<code>.played_league_code</code>, named by <code>mart_competition_index.competition_name</code>; "
             "<code>.played_kickoff_datetime</code>, its UTC day until #146", "not guaranteed (gap 1)"),
        ],
        "gaps": [
            "1. The window mart tests the result, the order and the opponent's key, but not the opponent's name, the goals, the "
            "date or the competition: a row can render with a blank.",
            "2. The built row cuts long names off with &ldquo;&hellip;&rdquo; at every width (&ldquo;TSG 1899 Hoffenheim&rdquo;, "
            "&ldquo;L&uuml;neburger SK Hansa&rdquo;), shows competition codes, and its W/D/L and H/A letters are English on the "
            "German and Finnish pages.",
        ],
    },
    "Players to watch": {
        "rows": [
            ("which players, in which order", "<b>not served</b>: each player's season to date across all the club's "
             "competitions, before the match, ranked by goals plus assists (<code>scorer_points_player</code>, &ldquo;Goal "
             "contributions&rdquo;), ties by more goals, then fewer minutes. The mock shows a stand-in read once from "
             "<code>mart_player_fixture_stats</code>", "fewer players with a goal or an assist: fewer rows"),
            ("before a team's first match of the season", "last season, as the phase rules give the form window", "&ndash;"),
            ("4 goals &middot; 2 assists", "the same stand-in: the sums of <code>goals_total</code>, <code>goals_assists</code>",
             "see gap 2"),
            ("Forward &middot; Midfield &middot; the name and photo", "<code>position_code</code>, <code>player_name</code>, "
             "<code>player_photo_url</code> on the player's match rows", "the photo: the initials"),
        ],
        "gaps": [
            "1. The new window, in the mart that serves the players today: <code>mart_player_momentum</code> takes each "
            "player's season to date across all the club's competitions instead of the team's last 5 (its "
            "<code>window_type</code> says so), and <code>top_player_rank</code> orders by goals plus assists, then goals, "
            "then fewer minutes. The player list stops sharing the team form's window; the window model "
            "(<code>metrics_context_model.md</code>) gains this kind.",
            "2. Player stats are missing for whole competitions (&ldquo;absence means unavailable, never zero&rdquo;): the "
            "mart must say when a season total misses matches. Here every match is covered (Dortmund 6 of 6, Bremen 5 of 5).",
            "3. The built row cuts long names off with &ldquo;&hellip;&rdquo; (the sample's longest: 44 characters).",
        ],
    },
    "Head to head": {
        "rows": [
            ("the intro: &ldquo;Of the last 5 meetings, Borussia Dortmund won 3 and 2 were drawn&rdquo;",
             "<code>mart_head_to_head.meetings_last5</code>, <code>.wins_last5</code>, <code>.draws_last5</code>, "
             "<code>.losses_last5</code>, the row for (home team, away team); the names: the header's (block 2)",
             "never missing while the row exists: tested to sum to <code>meetings_last5</code>; each split has its own wording "
             "(&ldquo;All of the last 3 meetings were drawn&rdquo;, &ldquo;SV Werder Bremen won the last meeting&rdquo;); "
             "no row: &ldquo;No meetings on record&rdquo; in place of the list"),
            ("which meetings, newest first", "<code>.recent_meetings[]</code>, its first 5", "fewer meetings: fewer rows"),
            ("0&ndash;2 SV Werder Bremen &ndash; Borussia Dortmund", "which side was at home: <b>not served</b> (gap 1); "
             "the goals: <code>.recent_meetings[].goals_for</code>, <code>.goals_against</code>, in the match's order; the names: the header's (block 2)",
             "not tested (gap 3)"),
            ("Bundesliga &middot; 16 May 2026", "<code>.recent_meetings[].league_code</code>, named by "
             "<code>mart_competition_index.competition_name</code>; <code>.kickoff_datetime</code>, its UTC day until #146",
             "not tested (gap 3)"),
        ],
        "gaps": [
            "1. Which side was at home in a past meeting is not served: <code>recent_meetings</code> carries no "
            "<code>home_away</code>, while <code>int_legs__team_match</code>, the model the mart is built from, has it. One "
            "field added to the existing mart; its one reader is the export's match payload. The mock reads it from a "
            "stand-in read once from <code>core.fct_fixture</code>.",
            "2. The mart's descriptions say &ldquo;all time&rdquo; (the table and <code>total_meetings</code>), which is false: "
            "it counts only the meetings inside the data window, set per competition in the registry (the Bundesliga's last 10 "
            "seasons, the DFB-Pokal's last 5, the European cups' last 10), and BigQuery shows the false text. A competition the "
            "site does not hold (the DFL-Supercup) is never counted, here or in the form's last 5.",
            "3. Nothing tests the fields inside <code>recent_meetings</code> (result, goals, competition, date).",
            "4. The built block: dates without the year (&ldquo;25 Jan&rdquo; is 2025, the next row&rsquo;s &ldquo;31 Aug&rdquo; "
            "is 2024), competition codes (BL1), totals and a bar that read as all-time, and &ldquo;First-ever meeting&rdquo; "
            "for a pair the data has not seen meet.",
        ],
    },
    "Next matches": {
        "rows": [
            ("which matches", "each of the two teams' earliest match not yet started, in any competition: a filter of "
             "<code>mart_competition_fixtures</code>, the one source of every list of matches (#173); a team whose next "
             "match is this one adds none. The mock reads the exported fixtures after the export day",
             "a team with no fixture left: no row"),
            ("Bundesliga", "the fixture's <code>league_code</code>, named by <code>mart_competition_index</code>",
             "a name: not guaranteed (block 1, gap 1)"),
            ("the two clubs, crests, 18:30, 9 Oct", "the fixture's two teams, the side at home first; its kick-off "
             "(UTC until #146)", "no time: &ldquo;TBC&rdquo;, as every match row"),
        ],
        "gaps": [
            "1. Home, the Matches page and the team page each read their own mart for the same content today "
            "(<code>mart_next_matchday</code>, <code>mart_match_days</code>, <code>mart_team_fixtures</code>); #173 moves "
            "every list of matches onto <code>mart_competition_fixtures</code>, filtered per page.",
        ],
    },
    "Explore": {
        "rows": [
            ("Borussia Dortmund &middot; SV Werder Bremen", "the header's names (block 2)", "a name: left out"),
            ("Table &middot; Top scorers", "site text, <code>table</code>, <code>topScorers</code>", "never missing"),
        ],
        "gaps": [
            "1. None of the four chips is a link, although every target is built: the team pages, the league table on the "
            "competition's Overview tab, the top scorers on its Rankings tab. The chip is no element of the block "
            "standard; the team page shows the same two inert chips (Table, Top scorers) under its fixtures.",
        ],
    },
    "lede": {
        "rows": [
            ("the words (built today)", "site text, <code>aboutWithH2h</code> / <code>aboutNoH2h</code>", "never missing"),
            ("the two names", "<code>core.dim_team.team_name</code> (block 2 moves it to <code>mart_competition_fixtures</code>)", "left blank"),
            ("Regular Season - 5", "<code>core.fct_fixture.round_name</code>, the provider's English", "left out"),
            ("met 18 times: 11&ndash;5&ndash;2", "<code>mart_head_to_head.total_meetings</code>, <code>.wins</code>, <code>.draws</code>, <code>.losses</code>",
             "never met: the shorter template without it"),
        ],
        "gaps": [
            "1. The meetings are only those inside the data's window, which is set per competition: the Bundesliga's 10 seasons "
            "(so since 2016/17), most other competitions only the current season. The mart's column description says "
            "&ldquo;all time&rdquo;, which is false, and BigQuery shows it.",
            "2. The page's description for search results reuses <code>aboutNoH2h</code> with the provider's English round name.",
        ],
    },
}

HARNESS_CSS = """
/* MOCK HARNESS ONLY -- not part of the design. */
.mk-ctl { position: relative; z-index: 99; display: flex; flex-wrap: wrap; gap: 18px; align-items: center;
          padding: 12px 16px; background: #14161c; border-bottom: 1px solid #2b2f38; color: #c7ccd4;
          font: 400 13px/1.4 system-ui, sans-serif; }
.mk-ctl label { display: inline-flex; align-items: center; gap: 7px; cursor: pointer; user-select: none; }
.mk-in { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
.mk-box { width: 15px; height: 15px; border-radius: 4px; border: 1px solid #4a505b; background: #0d0f13; }
#mk-built:checked ~ .mk-ctl label[for="mk-built"] .mk-box,
#mk-prop:checked ~ .mk-ctl label[for="mk-prop"] .mk-box,
#mk-src:checked ~ .mk-ctl label[for="mk-src"] .mk-box { background: #3bb072; border-color: #3bb072; }
#mk-built:checked ~ .mk-page .mk-p { display: none; }
#mk-prop:checked ~ .mk-page .mk-b { display: none; }
.mk-src { display: none; margin: 18px 0 0; padding: 8px 10px; border-left: 3px solid #d29922;
          background: #1f1a10; color: #e3c27a; font: 400 12px/1.45 system-ui, sans-serif; }
.mk-src b { display: block; margin-bottom: 4px; color: #f0d59a; }
.mk-src table { width: 100%; border-collapse: collapse; }
.mk-src th, .mk-src td { text-align: left; vertical-align: top; padding: 4px 10px 4px 0; border-bottom: 1px solid #3a3020; }
.mk-src th { color: #c9a85c; font-weight: 600; }
.mk-src code { font: 11.5px/1.4 ui-monospace, Consolas, monospace; color: #f0d59a; overflow-wrap: anywhere; }
.mk-gap { margin-top: 6px; }
#mk-links:checked ~ .mk-ctl label[for="mk-links"] .mk-box { background: #3bb072; border-color: #3bb072; }
#mk-links:checked ~ .mk-page a { outline: 2px dashed #3bb072; outline-offset: -1px; }
@media (max-width: 699.98px) {
  .mk-src table, .mk-src tbody, .mk-src tr, .mk-src td { display: block; }
  .mk-src th { display: none; }
  .mk-src tr { padding: 5px 0; border-bottom: 1px solid #3a3020; }
  .mk-src td { padding: 1px 0; border: 0; }
  .mk-src td:first-child { color: #f0d59a; font-weight: 600; }
}
#mk-src:checked ~ .mk-page .mk-src { display: block; }
.mk-chg { outline: 2px dashed #d29922; outline-offset: 4px; }
/* A change marker on a block that lays itself out sits on the outline's corner, out of the flow. */
.mk-crumbbox, .mast.mk-chg, .lede.mk-chg { position: relative; }
.lede.mk-chg > .mk-n { position: absolute; top: 2px; right: -10px; margin: 0; }
#mk-prop:checked ~ .mk-page section[aria-label="Form comparison"] .seg,
#mk-prop:checked ~ .mk-page section[aria-label="Form comparison"] .win-w2 { display: none !important; }
#mk-prop:checked ~ .mk-page section[aria-label="Form comparison"] .win-w1 { display: block !important; }
/* Without the switch the first line sits the block standard's one heading gap under the heading. */
#mk-prop:checked ~ .mk-page section[aria-label="Form comparison"] .win-w1 > .formrow:first-child { margin-top: 0; }
#mk-prop:checked ~ .mk-page section[aria-label="Form comparison"] .win-w1 .wmeta { display: none; }
.mk-rsplit { display: grid; grid-template-columns: 1fr; column-gap: 30px; }
.sechead + .mk-rsplit .mk-rcol:first-child .colhead { margin-top: 0; }
@container (min-width: 560px) { .mk-rsplit { grid-template-columns: 1fr 1fr; } .sechead + .mk-rsplit .colhead { margin-top: 0; } }
.mk-rcol { display: grid; grid-template-rows: subgrid; grid-row: span 6; }
/* Each row sits in a wrapper that measures the list's width, so the column itself keeps sharing its
   row heights with the other team's column; the line between rows moves to the wrapper. */
.mk-rwrap { container-type: inline-size; }
.mk-rwrap .rmatch { border-bottom: 0; }
.mk-rwrap:not(:last-child) { border-bottom: 1px solid var(--line); }
/* A result row opening a block carries no space of its own, as the built match row opening one does. */
.sechead + .mk-h2h > .mk-rwrap:first-child .rmatch { padding-top: 0; }
/* A club in a match row carries its crest before its name, 10px apart, as in every match row. */
.mk-club { display: inline-flex; align-items: center; gap: 10px; vertical-align: middle; max-width: 100%; }
.mk-club .mk-cn { min-width: 0; }
/* A club alone in its cell has no text to centre on, so it sits at the cell's top, not 1.3px under it. */
.ropp > .mk-club:only-child { vertical-align: top; }
/* A reference copied from another approved page, shown for comparison only. */
.mk-ref { margin-top: 36px; padding: 4px 0 14px; border-top: 1px dashed #4a8fd6; border-bottom: 1px dashed #4a8fd6; }
.mk-reflabel { margin: 8px 0 0; color: #7fb3ea; font: 600 12px/1.4 system-ui, sans-serif; }
/* A row that leads somewhere is one link, the whole row, lit on hover, as #129 rules every row link. */
a.mk-rlink { display: block; border-radius: 9px; margin-inline: -12px; padding-inline: 12px; color: inherit; text-decoration: none; }
@media (hover: hover) { a.mk-rlink:hover { background: color-mix(in srgb, var(--ink) 11%, transparent); } }
a.mk-rlink:active { background: var(--sunk); }
.mk-rm { grid-template-columns: 24px 42px 1fr; grid-template-areas: "res score opp" ". . meta"; row-gap: 2px; align-content: start; }
/* One W/D/L chip on the page (the form block's pill), and the opponent named as every match row names a
   club: 15px ink, wrapping, never cut off. */
.mk-rm .pill { grid-area: res; }
.mk-rm .rscore { grid-area: score; font-size: 15px; }
.mk-rm .ropp { grid-area: opp; white-space: normal; overflow: visible; text-overflow: clip; font-size: 15px; }
.mk-rm .rmeta { grid-area: meta; text-align: left; white-space: normal; }
/* The player row: the numbers stay on the right at every width and only the name wraps, never cut off. */
.mk-pr { grid-template-columns: 34px 1fr auto; grid-template-areas: "photo name stat" "photo pos stat"; row-gap: 2px; align-content: start; }
.mk-pr .pphoto { grid-area: photo; }
.mk-pr .pname { display: contents; }
.mk-pr .pname .nm { grid-area: name; white-space: normal; overflow: visible; text-overflow: clip; }
.mk-pr .pname .ps { grid-area: pos; }
.mk-pr .pstat { grid-area: stat; align-self: center; text-align: right; }
/* The same type scale as the result row: name 15px regular, the second line 12px grey, numbers 15px bold. */
.mk-pr .pname .nm { font-size: 15px; font-weight: 400; }
.mk-pr .pname .ps { font-size: 12px; }
.mk-pr .pstat { font-size: 12px; }
.mk-pr .pstat b { font-size: 15px; }
/* Like the fact row: where the list is 420px wide or more, a result row is one line with the
   competition or round and the date on the right; narrower, two lines. */
@container (min-width: 420px) {
  .mk-rm { grid-template-columns: 24px 42px 1fr auto; grid-template-areas: "res score opp meta"; column-gap: 11px; }
  .mk-rm .rmeta { text-align: right; }
}
/* A meeting of the two teams is the same row without the chip, which would take one side: the score
   in the order of the match, then both names, the side that was at home first. */
.mk-rm.mk-meet { grid-template-columns: 42px 1fr; grid-template-areas: "score opp" ". meta"; }
@container (min-width: 420px) {
  .mk-rm.mk-meet { grid-template-columns: 42px 1fr auto; grid-template-areas: "score opp meta"; }
}/* The metric groups carry the Rankings tab's metric group heading: 17px bold ink at the block's left
   edge, 34px above the group, 26px to its first row, no line. */
#mk-prop:checked ~ .mk-page .win-w1 .mgroup { font-size: 17px; font-weight: 700; line-height: 1.2; letter-spacing: normal;
                                              text-transform: none; color: var(--ink); text-align: left; padding: 34px 0 0; margin-bottom: 26px; }
/* Where the content is under 480px wide, a comparison row takes two lines: its label across the full
   width, then the two values at the outer edges with the bar filling the space between them; wider,
   the three-column row keeps a bar of 195px or more. */
@container (max-width: 479.98px) {
  #mk-prop:checked ~ .mk-page .win-w1 .mbar { max-width: none; }
  #mk-prop:checked ~ .mk-page .win-w1 .mrow { grid-template-columns: auto 1fr auto; grid-template-areas: "lab lab lab" "home bar away";
                                               row-gap: 2px; column-gap: 12px; }
  #mk-prop:checked ~ .mk-page .win-w1 .mval { line-height: 1.2; }
  #mk-prop:checked ~ .mk-page .win-w1 .mmid { display: contents; }
  #mk-prop:checked ~ .mk-page .win-w1 .mlabel { grid-area: lab; }
  #mk-prop:checked ~ .mk-page .win-w1 .mbar { grid-area: bar; align-self: center; }
  #mk-prop:checked ~ .mk-page .win-w1 .mval.home { grid-area: home; text-align: left; min-width: 3ch; }
  #mk-prop:checked ~ .mk-page .win-w1 .mval.away { grid-area: away; text-align: right; min-width: 3ch; }
}
/* A link inside a sentence marked by the heading link's chevron at rest, not an underline that only
   hover makes visible; the invisible padding gives it a 44px touch area without moving the text. */
.fx p a.mk-chevlink { text-decoration: none; font-weight: 600; color: var(--ink); white-space: nowrap; padding-block: 14px; }
.mk-chevlink .chev { width: 14px; height: 14px; vertical-align: -2px; margin-left: 3px; }
@media (hover: hover) { .mk-chevlink:hover .chev { color: var(--ink-2); transform: translateX(2px); } }
#mk-prop:checked ~ .mk-page section[aria-label="Form comparison"] .win-w1 .formrow,
#mk-prop:checked ~ .mk-page section[aria-label="Form comparison"] .win-w1 .cmp-head { display: none !important; }
/* One head row: each team's name over its five pills, in two halves; the pills share their half,
   24px where they fit, smaller where they do not. */
.mk-formhead { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; padding-bottom: 12px;
               border-bottom: 1px solid var(--line); margin-bottom: 2px; }
.mk-formhead .mk-fh { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.mk-formhead .mk-fh.home { align-items: flex-start; text-align: left; }
.mk-formhead .mk-fh.away { align-items: flex-end; text-align: right; }
.mk-formhead .h { text-align: inherit; }
.mk-formhead .pills { width: 100%; max-width: 140px; }
.mk-formhead .away .pills { justify-content: flex-end; }
.mk-formhead .pill { width: auto; height: auto; flex: 0 1 24px; min-width: 0; aspect-ratio: 1; }
.mk-crumbbox > .mk-n, .mast.mk-chg > .mk-n { position: absolute; top: 2px; right: -10px; margin: 0; }
.mk-n { display: inline-grid; place-items: center; min-width: 18px; height: 18px; margin-left: 6px; padding: 0 4px;
        border-radius: 9px; background: #d29922; color: #111; font: 700 11px/1 system-ui, sans-serif;
        vertical-align: middle; }
.mk-gone { margin-top: 36px; padding: 10px 12px; border: 2px dashed #d29922; color: #e3c27a;
           font: 400 12px/1.45 system-ui, sans-serif; }
.mk-legend { max-width: 680px; margin: 0 auto; padding: 18px 16px 48px; color: #9aa0a9;
             font: 400 13px/1.55 system-ui, sans-serif; }
.mk-legend b { color: #e6e8ec; }
.mk-legend table { border-collapse: collapse; width: 100%; margin: 8px 0 18px; }
.mk-legend td, .mk-legend th { text-align: left; vertical-align: top; padding: 5px 10px 5px 0; border-bottom: 1px solid #2b2f38; }
@media (max-width: 699.98px) {
  .mk-legend table, .mk-legend tbody, .mk-legend tr, .mk-legend td { display: block; }
  .mk-legend th { display: none; }
  .mk-legend td { border: 0; padding: 2px 0; }
  .mk-legend tr { padding: 6px 0; border-bottom: 1px solid #2b2f38; }
}
.mk-view { margin-left: auto; color: #e3c27a; font-weight: 600; }
.mk-view span { display: none; }
/* The competition group head opens the header, keeping its own alignment inside the centred header. */
.mast .mk-comp { text-align: start; }
@media (max-width: 699.98px) { .mk-view .mk-v1 { display: inline; } }
@media (min-width: 700px) and (max-width: 1009.98px) { .mk-view .mk-v2 { display: inline; } }
@media (min-width: 1010px) { .mk-view .mk-v3 { display: inline; } }
"""

# The adaptation, at the site's phone boundary (the menu folds into the drawer under 700px), in
# harness classes only: the phone trail drops Home and the current page, every crumb link gets a
# 44px touch area with its text where it was, and the menu marks its section with the tab bar's
# selected style (ink, bold, the 2px line; in the drawer's list, ink and bold).
ADAPT_CSS = """
.mk-seg { display: inline-flex; align-items: center; gap: 8px; white-space: nowrap; }
.mk-ph-off.mk-seg { display: inline-flex; }
@media (max-width: 699.98px) { .mk-ph-off, .mk-ph-off.mk-seg { display: none; } }
.mk-adapt { align-items: center; padding-top: 6px; row-gap: 0; }
.mk-touch { padding-block: 12px; }
/* Under 700px the trail is one line at any width: when it does not fit, it slides sideways inside
   its line, opened at its end (the nearest level), and the cut start fades to show there is more. */
@media (max-width: 699.98px) {
  .mk-adapt { flex-wrap: nowrap; overflow-x: auto; overscroll-behavior-x: contain; scrollbar-width: none; }
  .mk-adapt::-webkit-scrollbar { display: none; }
  .mk-adapt.mk-cut { -webkit-mask-image: linear-gradient(to right, transparent 0, #000 28px);
                     mask-image: linear-gradient(to right, transparent 0, #000 28px); }
}
.mk-team .chev { vertical-align: -1px; margin-left: 5px; }
.mk-nw { white-space: nowrap; }
@media (hover: hover) { .mk-team:hover .chev { color: var(--ink-2); transform: translateX(2px); } }
.mk-team:active .chev { color: var(--ink); }
/* Under 700px the two teams stack, one per line as the match row stacks its sides, so a name of
   any length wraps inside a full-width line instead of overflowing a half-width column. */
@media (max-width: 699.98px) {
  .mk-stack .teams { grid-template-columns: 1fr; gap: 0; margin-top: 16px; }
  .mk-stack .vs { display: none; }
  .mk-stack .mk-team { display: grid; grid-template-columns: auto 1fr; column-gap: 14px; row-gap: 4px;
                       align-items: center; text-align: left; padding: 12px 4px; border-bottom: 1px solid var(--line); }
  .mk-stack .mk-team + .vs + .mk-team { border-bottom: 0; }
  .mk-stack .mk-team .crest { grid-row: span 2; }
  .mk-stack .mk-team .tname { font-size: 20px; text-wrap: pretty; }
  .mk-stack .mk-team .stand { grid-column: 2; }
}
@media (max-width: 699.98px) and (hover: hover) {
  .mk-stack .mk-team:hover { background: color-mix(in srgb, var(--ink) 11%, transparent); }
}
"""
# The one line of behaviour the one-line trail needs: open it at its end, and fade the start while
# something is cut off there. CSS alone opens a sliding line at its start.
TRAIL_JS = """
(function () {
  var n = document.querySelector('.mk-crumbbox nav');
  if (!n) return;
  function cut() { n.classList.toggle('mk-cut', n.scrollLeft > 0); }
  function end() { n.scrollLeft = n.scrollWidth; cut(); }
  n.addEventListener('scroll', cut, { passive: true });
  addEventListener('resize', end);
  document.getElementById('mk-prop').addEventListener('change', end);
  end();
})();
"""
# One layout at every width: the two values on the name's line, one at each edge of the block, and the bar the full
# width beneath, so every bar is the same length and nothing moves when the window narrows.
FORM_CSS = """
#mk-prop:checked ~ .mk-page .win-w1 .mrow { display: grid; grid-template-columns: 4.6ch 1fr 4.6ch;
                                             grid-template-areas: "home lab away" "bar bar bar";
                                             column-gap: 12px; row-gap: 6px; align-items: center; }
#mk-prop:checked ~ .mk-page .win-w1 .mmid { display: contents; }
#mk-prop:checked ~ .mk-page .win-w1 .mlabel { grid-area: lab; }
#mk-prop:checked ~ .mk-page .win-w1 .mbar { grid-area: bar; max-width: none; }
#mk-prop:checked ~ .mk-page .win-w1 .mval.home { grid-area: home; text-align: left; }
#mk-prop:checked ~ .mk-page .win-w1 .mval.away { grid-area: away; text-align: right; }
"""
# "Clean page", on by default: the page as a reader sees it, every review aid hidden (the approved instances for
# comparison, the change outlines and numbers, the notes on what leaves, the data notes, the legend).
CLEAN_CSS = """
#mk-clean:checked ~ .mk-ctl label[for="mk-clean"] .mk-box { background: #3bb072; border-color: #3bb072; }
#mk-clean:checked ~ .mk-page .mk-ref, #mk-clean:checked ~ .mk-page .mk-gone, #mk-clean:checked ~ .mk-page .mk-n,
#mk-clean:checked ~ .mk-page .mk-src, #mk-clean:checked ~ .mk-legend { display: none !important; }
#mk-clean:checked ~ .mk-page .mk-chg { outline: none !important; }
"""
CUR_CSS = """
%(on)s.mk-cur { color: var(--ink) !important; font-weight: 700 !important; }
%(on)s.mainnav .mk-cur { border-radius: 0; box-shadow: inset 0 -2px 0 var(--ink); }
"""


def badge(n, proposed_only=True):
    return '<span class="mk-n%s">%d</span>' % (" mk-p" if proposed_only else "", n)


def fdate(iso, weekday=True):
    d = date.fromisoformat(iso[:10])
    return "%s%d %s %d" % ("%s, " % DAYS[d.weekday()] if weekday else "", d.day, MONTHS[d.month - 1], d.year)


def crest(url):
    img = '<img src="%s" alt="" loading="lazy" width="24" height="24">' % E(url) if url else ""
    return '<div class="crest xs">%s</div>' % img


def match_row(left, right):
    """THE match row, played: two sides, each (name, crest, goals); the winner by weight."""
    (ln, lc, lg), (rn, rc, rg) = left, right
    def side(n, c, g, other):
        return ('<span class="side">%s<span class="nm">%s</span><span class="g num%s">%d</span></span>'
                % (crest(c), E(n), " winner" if g > other else "", g))
    return '<div class="fxrow played"><span class="sides">%s%s</span></div>' % (side(ln, lc, lg, rg), side(rn, rc, rg, lg))


def h2h_sentence(n, won, drawn, lost, home_name, away_name):
    """Head to head's intro from the served last-meetings split (the home team's wins, the draws, the
    away team's wins), home team first; every case of the split has its own wording. A club's name
    opens the sentence wherever a club won, so the name never breaks and never leaves a clause alone
    on the first line."""
    both_or_all = "both" if n == 2 else "all"
    meetings = '<span class="nb">%d meetings</span>' % n
    if n == 1:
        if drawn:
            return "The last meeting was drawn"
        return "%s won the last meeting" % (home_name if won else away_name)
    if drawn == n:
        return "%s of the last %s were drawn" % (both_or_all.capitalize(), meetings)
    if n in (won, lost):
        return "%s won %s of the last %s" % (home_name if won else away_name, both_or_all, meetings)
    if won and lost:
        said = "%s won %d and %s %d of the last %s" % (home_name, won, away_name, lost, meetings)
    else:
        said = "%s won %d of the last %s" % (home_name if won else away_name, won or lost, meetings)
    if drawn:
        said += ', and <span class="nb">%d %s drawn</span>' % (drawn, "was" if drawn == 1 else "were")
    return said


def club(name, crest_url, after=""):
    """A club inside a match row: its crest, the size every match row gives it, then its name."""
    return '<span class="mk-club">%s<span class="mk-cn">%s%s</span></span>' % (crest(crest_url), E(name), after)


def next_matches(fx):
    """Each team's next match in any competition after the export day, a stand-in for the rank across all
    competitions mart_team_fixtures gains; a team whose next match is this one adds nothing."""
    every = [json.loads(p.read_text(encoding="utf-8")) for p in (DATA / "fixtures").glob("*.json")]
    out = []
    for side in (fx["home"], fx["away"]):
        tid = int(side["team_id"])
        mine = sorted((f for f in every if tid in (int(f["home"]["team_id"]), int(f["away"]["team_id"]))
                       and f["kickoff"][:10] > EXPORT_DAY), key=lambda f: f["kickoff"])
        if mine and mine[0]["fixture_id"] != fx["fixture_id"] and mine[0]["fixture_id"] not in [f["fixture_id"] for f in out]:
            out.append(mine[0])
    return sorted(out, key=lambda f: f["kickoff"])


# Home's Next matches as approved on #127: the reference the future match page's Next matches follows.
HOME_RENDER = HERE / "renders" / "home_2026-09-17_02.html"


def upcoming_block(matches, comps):
    """Upcoming matches as the approved Home's Next matches draws them (#127, the Home render of
    record): the competition's head with its logo, a date heading per day, the match rows with both
    crests and the kick-off with its zone; every row a link to the match's page."""
    groups = {}
    for f in matches:
        groups.setdefault((f["league_code"], f["season"]), []).append(f)
    out = []
    for (code, season), rows in groups.items():
        path = DATA / "competitions" / code / ("%s.json" % season)
        if path.is_file():
            comp = json.loads(path.read_text(encoding="utf-8"))
        else:
            # The sample carries one competition's payload; another's head comes from mart_competition_index.
            index = json.loads((DATA / "competition_index.json").read_text(encoding="utf-8"))
            row = next(r for r in index["competitions"] if r["league_code"] == code)
            comp = {"slug": row["slug"], "name": row["competition_name"], "crest": row.get("logo_url")}
        body, day = [], None
        for f in rows:
            if f["kickoff"][:10] != day:
                day = f["kickoff"][:10]
                body.append('<div class="dh">%s</div>' % fdate(f["kickoff"]))
            sides = "".join('<span class="side">%s<span class="nm">%s</span></span>' % (crest(s.get("crest")), E(s["name"]))
                            for s in (f["home"], f["away"]))
            body.append('<a class="fxrow" href="/en/%s/matches/%s/"><span class="sides">%s</span><span class="when">'
                        '<b class="t">%s</b><span class="rowtz">UTC</span></span></a>'
                        % (comp["slug"], f["slug"], sides, f["kickoff"][11:16]))
        out.append('<div class="fxgroup"><div class="gh"><a class="cnm" href="/en/%s/"><span class="clogo">%s</span>'
                   '<span class="nm">%s</span>%s</a></div>%s</div>'
                   % (comp["slug"], crest(comp.get("crest")), E(comps.get(code, {}).get("name") or comp["name"]), CHEV, "".join(body)))
    return "".join(out)


def home_reference():
    """The approved Home's first Next matches group, copied from its render, shown under the page's own
    block so the two can be compared on one screen."""
    page = HOME_RENDER.read_text(encoding="utf-8")
    at = page.index('<div class="fxgroup">')
    return ('<section class="mk-p mk-ref" aria-label="For comparison"><div class="mk-reflabel">For comparison, not part of the '
            'page: Home&rsquo;s Next matches as approved (#127, render home_2026-09-17_02)</div>%s</section>' % page[at:block_end(page, at)])


def fact_row(label, value, context=""):
    sub = '<span class="sub">%s</span>' % context if context else ""
    return ('<div class="frow"><span class="fl">%s</span><span class="fv"><span class="fvv"><b>%s</b></span>%s</span></div>'
            % (label, value, sub))


def board(name, rows):
    """The board: rank, crest, name with a sub-line, the ordered-by number; rows are not links
    here, because a player has a page only while he leads a rankings board."""
    body = "".join('<div class="ctab-row"><span class="rk num">%d</span><span class="tm">%s<span class="ent">'
                   '<span class="nm">%s</span><span class="sub">%s</span></span></span><span class="n num pts">%d</span></div>'
                   % (rk, crest(c), E(n), E(sub), v) for rk, c, n, sub, v in rows)
    return ('<div class="board"><div class="ctab rkt"><div class="ctab-head"><span class="h rk"></span>'
            '<span class="h nmh"><span class="bt"><span class="nm">%s</span></span></span><span class="h"></span></div>%s</div></div>'
            % (E(name), body))


def slug(text):
    """The site's address form of a name: ASCII, lower case, words joined by hyphens."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def match_href(comp_slug, day, home_name, away_name):
    """A match page's address, as the site builds it for every match."""
    return "/en/%s/matches/%s-%s-vs-%s/" % (comp_slug, day, slug(home_name), slug(away_name))


def team_slugs():
    """team_id -> slug for every team page the build emitted."""
    out = {}
    for f in (DATA / "teams").glob("*.json"):
        t = json.loads(f.read_text(encoding="utf-8"))
        if (DIST / "en" / "teams" / t["slug"] / "index.html").is_file():
            out[int(t["team_id"])] = t["slug"]
    return out


def inline_css(page):
    return re.sub(r'<link rel="stylesheet" href="([^"]+)">',
                  lambda m: "<style>%s</style>" % (DIST / m.group(1).lstrip("/")).read_text(encoding="utf-8"),
                  page)


def page_sources(fx, comps):
    """The data-source tables for the page drawn: every example is this match's own value, and a block
    the page does not show has no table."""
    src = copy.deepcopy(SOURCES)
    home, away = fx["home"], fx["away"]
    rnd, _ = served_round(fx)

    def label(key, i, text):
        src[key]["rows"][i] = (text,) + tuple(src[key]["rows"][i][1:])

    def chip(side):
        st = side.get("standing") or {}
        if st.get("league_rank") is None:
            return "no chip"
        gd = st["standing_goals_diff"]
        return "#%s &middot; %s pts &middot; GD %s" % (st["league_rank"], st["standing_points"], "+%d" % gd if gd > 0 else gd)

    label("crumb", 2, E(comps.get(fx["league_code"], {}).get("name") or fx["league_code"]))
    label("crumb", 4, "%s vs %s" % (E(home["name"]), E(away["name"])))
    label("mast", 1, "Matchday %d" % rnd["round_order"])
    label("mast", 2, "%s &middot; %s UTC" % (fdate(fx["kickoff"]), fx["kickoff"][11:16]))
    label("mast", 5, "%s; %s" % (chip(home), chip(away)))
    label("mast", 6, "%s, closing the kick-off line" % E(fx.get("venue") or "the venue"))
    h = fx.get("head_to_head")
    if h:
        m = h["recent_meetings"][0]
        at_home = H2H_HOME[m["kickoff_datetime"][:10]] == int(home["team_id"])
        (hn, hg), (an, ag) = (((home["name"], m["goals_for"]), (away["name"], m["goals_against"])) if at_home
                              else ((away["name"], m["goals_against"]), (home["name"], m["goals_for"])))
        label("Head to head", 0, "the intro: &ldquo;%s.&rdquo;" % h2h_sentence(h["meetings_last5"], h["wins_last5"], h["draws_last5"],
                                                                          h["losses_last5"], E(home["name"]), E(away["name"])))
        label("Head to head", 2, "%d&ndash;%d %s &ndash; %s" % (hg, ag, E(hn), E(an)))
        label("Head to head", 3, "%s &middot; %s" % (E(comps.get(m["league_code"], {}).get("name") or m["league_code"]),
                                                     fdate(m["kickoff_datetime"], weekday=False)))
    else:
        src["Head to head"]["rows"] = [("No meetings on record.", "<code>mart_head_to_head</code> has no row for (home team, "
                                        "away team): the data holds no meeting of the pair inside its window", "&ndash;")]
        src["Head to head"]["gaps"] = src["Head to head"]["gaps"][1:2]
    if STATE == "next":
        rows = src["Form comparison"]["rows"]
        rows[5] = ("Discipline: fouls, yellow cards, red cards, per match", "each team&rsquo;s window matches&rsquo; team stat "
                   "lines (a blank card on a line with statistics is 0). Not served yet: the Form comparison&rsquo;s mart gains "
                   "fouls and the cards per match with the catalogue change; the mock reads a stand-in read once",
                   "as every rate: &ndash; when a match in the window has no stat line")
        rows.insert(3, ("Shots on goal against", "the opponents&rsquo; shots on goal per match over the window, the "
                        "catalogue&rsquo;s <code>shots_on_goal_against_per_match</code> (a Rankings board over the season). Not "
                        "served for the window yet; the mock reads a stand-in read once", "as every rate"))
        rows.insert(3, ("Possession", "each team&rsquo;s share of the passes in its window matches (its passes over both "
                        "teams&rsquo;), the catalogue&rsquo;s new Possession. Not served yet; the mock reads a stand-in read once",
                        "&ndash; when a match in the window lacks either team&rsquo;s passes"))
    if STATE.startswith("future"):
        for key in ("Form comparison", "Recent matches", "Players to watch", "lede"):
            src.pop(key, None)
        src["mast"]["rows"] = [r for i, r in enumerate(src["mast"]["rows"]) if i != 5]
        src["mast"]["gaps"] = src["mast"]["gaps"][:2] + [
            "3. No table position on a match further out: today&rsquo;s table is not the position going into it, which "
            "<code>mart_fixture_standing_context</code> serves (&ldquo;the table position it goes into that fixture on&rdquo;) "
            "only for the next match.",
            "4. Kick-off times far out are placeholders served as facts: in Matchdays 12&ndash;14 every Bundesliga match stands "
            "at Saturday 14:30 UTC with the status &ldquo;not started&rdquo;. The provider does not mark such a time as "
            "provisional, so the page would state an unscheduled kick-off as fixed.",
        ]
    return src


def add_sources(inner, sources):
    """A source note before each block, shown by the toggle."""
    def note(inner, key, marker):
        wrapped = '<div class="mk-b">' + marker
        at = wrapped if wrapped in inner else marker
        src = sources.get(key)
        if src:
            body = ('<table><tr><th>On the page</th><th>Comes from</th><th>When it is missing</th></tr>%s</table>%s'
                    % ("".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % r for r in src["rows"]),
                       "".join('<div class="mk-gap">Gap %s</div>' % g for g in src["gaps"])))
        else:
            return inner
        return inner.replace(at, '<div class="mk-src"><b>Data</b>%s</div>' % body + at, 1)

    inner = note(inner, "crumb", '<nav class="crumb"')
    inner = note(inner, "mast", '<header class="mast"')
    inner = note(inner, "lede", '<div class="lede"')
    for label in ("Form comparison", "Recent matches", "Players to watch", "Head to head", "Explore"):
        inner = note(inner, label, '<section aria-label="%s"' % label)
    # The future match page's Next matches exists under "Proposed" only.
    if '<section class="mk-p mk-chg" aria-label="Next matches"' in inner:
        inner = note(inner, "Next matches", '<section class="mk-p mk-chg" aria-label="Next matches"')
    return inner


# The glossary page is not built and its address is not set: a placeholder for the mock.
GLOSSARY = "/en/glossary/"


def block_end(s, start):
    """The index just past the </div> that closes the <div> opening at `start`."""
    depth = 0
    for m in re.finditer(r"<div\b|</div>", s[start:]):
        depth += 1 if m.group(0) != "</div>" else -1
        if depth == 0:
            return start + m.end()
    raise ValueError("unbalanced div at %d" % start)


def span_of(inner, start_marker, end_marker):
    start = inner.index(start_marker)
    return start, inner.index(end_marker, start) + len(end_marker)


def swap(inner, start_marker, end_marker, proposed):
    """The block from start_marker to end_marker, shown under "Built today"; `proposed` beside it."""
    s, e = span_of(inner, start_marker, end_marker)
    return inner[:s] + '<div class="mk-b">%s</div>%s' % (inner[s:e], proposed) + inner[e:]


def section(label, body, n, note=""):
    return ('<section class="mk-p mk-chg" aria-label="%s"><div class="sechead"><span class="eyebrow">%s</span>%s%s</div>%s</section>'
            % (label, label, note, badge(n, proposed_only=False), body))


def trail(league, home, away, extra_cls="", tail=""):
    """The site hierarchy's trail: every level above the match a link, the match itself last."""
    return ('<nav class="crumb%s" aria-label="Breadcrumb"><a class="lnk" href="/en/">Home</a>'
            '<span class="sep">&rsaquo;</span><a class="lnk" href="/en/competitions/">Competitions</a>'
            '<span class="sep">&rsaquo;</span><a class="lnk" href="/en/%s/">%s</a>'
            '<span class="sep">&rsaquo;</span><a class="lnk" href="/en/%s/matches/">Matchdays</a>'
            '<span class="sep">&rsaquo;</span><span class="here" aria-current="page">%s vs %s</span>%s</nav>'
            % (extra_cls, LEAGUE, league, LEAGUE, E(home["name"]), E(away["name"]), tail))


def adaptive_trail(league, home, away, extra_cls="", tail="", comp=LEAGUE, level="Matchdays"):
    """The same trail, adapting: under 700px Home and the current page leave (the logo is Home,
    the heading below names the page); every link has a 44px touch area at every width. A
    separator travels with the level after it, so a trail that wraps starts its next line with it."""
    return ('<nav class="crumb mk-adapt%s" aria-label="Breadcrumb"><span class="mk-ph-off mk-seg"><a class="lnk mk-touch" href="/en/">Home</a>'
            '<span class="sep">&rsaquo;</span></span><a class="lnk mk-touch" href="/en/competitions/">Competitions</a>'
            '<span class="mk-seg"><span class="sep">&rsaquo;</span><a class="lnk mk-touch" href="/en/%s/">%s</a></span>'
            '<span class="mk-seg"><span class="sep">&rsaquo;</span><a class="lnk mk-touch" href="/en/%s/matches/">%s</a></span>'
            '<span class="mk-ph-off mk-seg"><span class="sep">&rsaquo;</span><span class="here" aria-current="page">%s vs %s</span></span>%s</nav>'
            % (extra_cls, comp, league, comp, level, E(home["name"]), E(away["name"]), tail))


def mark_section(body):
    """The menu marks the section the page sits in: a match sits under Competitions."""
    return body.replace('<a href="/en/competitions/">Competitions</a>',
                        '<a class="mk-cur" href="/en/competitions/" aria-current="true">Competitions</a>')

CHEV = ('<svg class="chev" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M9 6l6 6-6 6" '
        'fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"></path></svg>')


def served_round(fx):
    """The competition payload's round for this match (mart_competition_fixtures), which the
    fixture payload does not carry."""
    season = json.loads((DATA / "competitions" / fx["league_code"] / ("%s.json" % fx["season"])).read_text(encoding="utf-8"))
    for rnd in season["fixtures"]:
        for f in rnd["fixtures"]:
            if f["fixture_id"] == fx["fixture_id"]:
                return rnd, f
    return None, None


def masthead(inner, fx, slugs, head=""):
    """The header as proposed: each team's column is one link to its team page, the name carrying
    the heading link's chevron at rest; the kick-off line names the round as the Matchdays tab does
    and carries the match row's zone label, and the venue closes that line instead of taking one of its
    own; each unit stays whole when the line wraps."""
    s, e = span_of(inner, '<header class="mast"', "</header>")
    built = inner[s:e]
    rnd, served = served_round(fx)
    kick = re.search(r'<div class="kick">([^<]*)</div>', built).group(1).split(" &middot; " if "&middot;" in built else " · ")
    round_label = "Matchday %d" % rnd["round_order"] if rnd and rnd.get("round_order") else kick[0]
    venue = re.search(r'<div class="venue">([^<]*)</div>', built)
    units = [round_label, kick[1], kick[2] + " UTC"] + ([venue.group(1).strip()] if venue and venue.group(1).strip() else [])
    kick_html = " &middot; ".join('<span class="mk-nw">%s</span>' % u for u in units)

    def team(side, key):
        slug = (served or {}).get(key, {}).get("slug") or slugs.get(int(side["team_id"]))
        # A match further out shows no table position: the one going into it is known only when it is next.
        st = {} if STATE.startswith("future") else (side.get("standing") or {})
        chip = ('<div class="stand num"><span class="mk-nw">#<b>%s</b></span> &middot; <span class="mk-nw"><b>%s</b> pts</span> '
                '&middot; <span class="mk-nw">GD <b>%s</b></span></div>'
                % (st["league_rank"], st["standing_points"],
                   ("+%d" % st["standing_goals_diff"]) if st["standing_goals_diff"] > 0 else str(st["standing_goals_diff"]))
                if st.get("league_rank") is not None else "")
        # The chevron stays with the name's last word, so a wrapped name never leaves it alone on a line.
        head_words, _, last = E(side["name"]).rpartition(" ")
        name = '%s%s<span class="mk-nw">%s%s</span>' % (head_words, " " if head_words else "", last, CHEV)
        body = ('<div class="crest"><img src="%s" alt="" loading="lazy" width="52" height="52"></div>'
                '<span class="tname">%s</span>%s' % (E(side["crest"] or ""), name, chip))
        if slug:
            return '<a class="team mk-team" href="/en/teams/%s/">%s</a>' % (slug, body)
        return '<div class="team">%s</div>' % body

    return ('<header class="mast mk-p mk-chg mk-stack">%s%s<div class="eyebrow">%s</div><div class="kick">%s</div>'
            '<div class="teams">%s<div class="vs">vs</div>%s</div></header>'
            % (badge(2, proposed_only=False), head, re.search(r'<div class="eyebrow">([^<]*)</div>', built).group(1), kick_html,
               team(fx["home"], "home"), team(fx["away"], "away")))


def lede(fx):
    """The sentence leaves: every fact it could hold is shown by a block below it."""
    return ('<div class="mk-p mk-gone">%s The sentence leaves: every fact it could hold is shown by a block below it '
            '(the form comparison, the head to head). The page&rsquo;s one-line summary for search results is its '
            'description, which is not shown on the page.</div>' % badge(8, proposed_only=False))


def propose(inner, fx, comps, slugs):
    def name(code):
        return comps.get(code, {}).get("name") or code

    home, away = fx["home"], fx["away"]
    league = E(name(fx["league_code"]))

    crumb = '<div class="mk-p mk-chg mk-crumbbox">%s%s</div>' % (adaptive_trail(league, home, away), badge(1, proposed_only=False))
    inner = swap(inner, '<nav class="crumb"', "</nav>", crumb)

    inner = swap(inner, '<header class="mast"', "</header>", masthead(inner, fx, slugs, competition_head(fx, comps)) + comp_head_ref())
    inner = swap(inner, '<div class="lede"', "</div>", lede(fx))

    # The window's explanation moves under the block heading as the block's intro, in the form
    # the ruled block explainer uses (.bsub); the old caption shows under "Built today" only.
    cap = re.search(r'<div class="caption">(all competitions &middot; incl\. |all competitions · incl\. )([^<]+)</div>', inner)
    n = (fx["home"].get("w1") or {}).get("games_in_window")
    inner = inner[:cap.start()] + '<div class="caption mk-b">%s%s</div>' % (cap.group(1), cap.group(2)) + inner[cap.end():]
    # One list of competitions for both teams would claim matches a team did not play (Bremen has no
    # Champions League match); each match's competition is named in Recent matches below.
    intro = ('<p class="bsub mk-p mk-chg">Form metrics from each team&rsquo;s last %s matches across all competitions. '
             '<a class="mk-chevlink" href="%s">Metric Glossary%s</a> %s</p>'
             % (n, GLOSSARY, CHEV, badge(9, proposed_only=False)))
    # Discipline follows Set pieces. The window serves no cards yet, so both sides show the page's
    # missing-value dash and the sources name the gap.
    def card_row(label):
        side = '<div class="bside %s"><span class="fill" style="width:0%%"></span></div>'
        return ('<div class="mrow"><div class="mval home">&ndash;</div><div class="mmid"><div class="mlabel">%s</div>'
                '<div class="mbar" aria-hidden="true">%s%s</div></div><div class="mval away">&ndash;</div></div>'
                % (label, side % "home", side % "away"))
    w1 = inner.index('<div class="win win-w1">')
    cmp_at = inner.index('<div class="cmp">', w1)
    cmp_end = block_end(inner, cmp_at) - len("</div>")
    if STATE == "next":
        # Decided on the played match's page (#132 state 3): Fouls leads Discipline, and every average there reads
        # per match; the values are the window stand-in until the Form comparison's mart serves them.
        discipline = "".join(stat_row("%s<small>per match</small>" % label, *FORM_STANDIN[key], -1)
                             for label, key in (("Fouls", "fouls"), ("Offsides", "offsides"), ("Yellow cards", "yellow_cards"),
                                                ("Red cards", "red_cards")))
    else:
        discipline = card_row("Yellow cards") + card_row("Red cards")
    inner = (inner[:cmp_end] + '<div class="mk-p mk-chg"><div class="mgroup">Discipline</div>%s</div>'
             % discipline + inner[cmp_end:])

    # The sign leaves the labels: an average keeps its short name and says "per match" on the
    # sub-label line the Defending row already uses (the words #41 gave board headings).
    # The Defending row's own sub-label ("tackles + interceptions + blocks") leaves with it.
    def per_match(m):
        return ('<div class="mlabel"><span class="mk-b">Ø %s%s</span><span class="mk-p">%s<small>per match</small></span></div>'
                % (m.group(1), m.group(2) or "", m.group(1)))
    inner = re.sub(r'<div class="mlabel">(?:Ø|&Oslash;) ([^<]+)(<small>[^<]*</small>)?</div>', per_match, inner)
    if STATE == "next":
        # Decided on the played match's page (#132 state 3): no sign before a name, the value keeps its %; and
        # Possession follows the passing triple (passes, accurate passes, pass accuracy).
        inner = re.sub(r'<div class="mlabel">% ([^<]+)</div>',
                       r'<div class="mlabel"><span class="mk-b">% \1</span><span class="mk-p">\1</span></div>', inner)
        label_at = inner.index('<span class="mk-p">Pass accuracy</span>', inner.index('<div class="win win-w1">'))
        at = block_end(inner, inner.rindex('<div class="mrow">', 0, label_at))
        inner = inner[:at] + '<div class="mk-p mk-chg">%s</div>' % stat_row("Possession", *FORM_STANDIN["possession"], 1, "%") + inner[at:]
        # Shots on goal against follows Shots on goal, as Goals against follows Goals.
        label_at = inner.index("Shots on goal<small>per match</small>", inner.index('<div class="win win-w1">'))
        row_at = inner.rindex('<div class="mrow">', 0, label_at)
        at = block_end(inner, row_at)
        inner = (inner[:at] + '<div class="mk-p mk-chg">%s</div>'
                 % (stat_row("Shots on target against<small>per match</small>", *FORM_STANDIN["sog_against"], -1)
                    + stat_row("Shots off target<small>per match</small>", *FORM_STANDIN["shots_off_goal"], 1)
                    + stat_row("Blocked shots<small>per match</small>", *FORM_STANDIN["shots_blocked"], 1)) + inner[at:])
        # Shooting reads its counts, then its two rates (#132 state 3): Shots from box moves behind the shots on goal.
        label_at = inner.index('<span class="mk-p">Shots from box</span>', inner.index('<div class="win win-w1">'))
        row_at = inner.rindex('<div class="mrow">', 0, label_at)
        row_end = block_end(inner, row_at)
        row = inner[row_at:row_end]
        inner = inner[:row_at] + '<div class="mk-b">%s</div>' % row + inner[row_end:]
        label_at = inner.index("Goals per shot on goal", inner.index('<div class="win win-w1">'))
        row_at = inner.rindex('<div class="mrow">', 0, label_at)
        # The count of shots from the box joins the counts; a share takes a name of its own (Box share, Shot
        # accuracy), and the share of shots on goal joins the rates, between where the shots came from and how many
        # went in.
        box = stat_row("Shots inside box<small>per match</small>", *FORM_STANDIN["box"], 1)
        row = row.replace('<span class="mk-p">Shots from box</span>', '<span class="mk-p">Shots inside box<small>percentage</small></span>')
        on_goal = stat_row("Shooting accuracy", *FORM_STANDIN["sog_share"], 1, "%")
        inner = inner[:row_at] + '<div class="mk-p mk-chg">%s%s%s</div>' % (box, row, on_goal) + inner[row_at:]
        # Football's own words (#132 state 3): on target, not on goal; a share takes football's name where it has one,
        # else its count's name and "percentage".
        for built, named in (("Shots on goal<small>per match</small>", "Shots on target<small>per match</small>"),
                             ("Goals per shot on goal", "Goals per shot on target"),
                             ("Duels won", "Duels won<small>percentage</small>"),
                             ("Save percentage", "Saves<small>percentage</small>")):
            inner = inner.replace('<span class="mk-p">%s</span>' % built, '<span class="mk-p">%s</span>' % named)
        # Dribbling leads One-on-one, as the player catalogue names it: its base, then its share, then the duels.
        label_at = inner.index('<span class="mk-p">Duels<small>per match</small></span>', inner.index('<div class="win win-w1">'))
        at = inner.rindex('<div class="mrow">', 0, label_at)
        dribbles = (stat_row("Dribbles attempted<small>per match</small>", *FORM_STANDIN["dribbles"], 1)
                    + stat_row("Dribbles completed<small>per match</small>", *FORM_STANDIN["dribbles_completed"], 1)
                    + stat_row("Dribbles completed<small>percentage</small>", *FORM_STANDIN["dribbles_pct"], 1, "%"))
        inner = inner[:at] + '<div class="mk-p mk-chg">%s</div>' % dribbles + inner[at:]

        # Match stats' counts beside their shares and groups, in its order.
        def put(label, rows, after):
            label_at = inner.index('<span class="mk-p">%s</span>' % label, inner.index('<div class="win win-w1">'))
            row_at = inner.rindex('<div class="mrow">', 0, label_at)
            at = block_end(inner, row_at) if after else row_at
            return inner[:at] + '<div class="mk-p mk-chg">%s</div>' % rows + inner[at:]
        windows = fx["home"]["w1"], fx["away"]["w1"]
        inner = put("Pass accuracy", stat_row("Accurate passes<small>per match</small>", *FORM_STANDIN["passes_accurate"], 1), False)
        inner = put("Duels won<small>percentage</small>", stat_row("Duels won<small>per match</small>", *FORM_STANDIN["duels_won"], 1), False)
        inner = put("Defensive actions<small>per match</small>",
                    "".join(stat_row("%s<small>per match</small>" % label, *(w[key] for w in windows), 1)
                            for label, key in (("Tackles", "tackles_per_match"), ("Interceptions", "interceptions_per_match"),
                                               ("Blocks", "blocks_per_match"))), True)
        inner = put("Saves<small>percentage</small>", stat_row("Saves<small>per match</small>", *FORM_STANDIN["saves"], 1), False)
        inner = put("Corners against<small>per match</small>", stat_row("Free kicks<small>per match</small>", *FORM_STANDIN["free_kicks"], 1), True)
    fs, fe = span_of(inner, '<section aria-label="Form comparison"', "</section>")
    hs, he = span_of(inner[fs:fe], '<div class="sechead">', "</div>")
    inner = inner[:fs + he] + intro + inner[fs + he:]

    # Each team's name and its form in one head row, in two halves: the pills need the width of a
    # half, which the comparison's narrow value column does not have on a phone.
    def form_side(team, side):
        pills = "".join('<span class="pill %s">%s</span>' % (r["result"], r["result"]) for r in team["form_window"])
        return '<div class="mk-fh %s"><div class="h">%s</div><div class="pills">%s</div></div>' % (side, E(team["name"]), pills)
    head = '<div class="mk-p mk-formhead">%s%s</div>' % (form_side(home, "home"), form_side(away, "away"))
    fs, fe = span_of(inner, '<section aria-label="Form comparison"', "</section>")
    at = inner.index('<div class="cmp">', inner.index('<div class="win win-w1">', fs)) + len('<div class="cmp">')
    inner = inner[:at] + head + inner[at:]
    # One window: the switch leaves, and in its place a note says where the season record went.
    s, e = span_of(inner, '<section aria-label="Form comparison"', "</section>")
    e -= len("</section>")
    inner = inner[:e] + ('<div class="mk-p mk-gone">%s The switch leaves with This season: the block shows one window, '
                         'the one the phase rules give each team (metrics_context_model.md &sect;3&ndash;4): while a league '
                         'runs, up to the last 5 matches in all the club&rsquo;s competitions this season; before a team&rsquo;s '
                         'first match in it, last season&rsquo;s record in that league; the caption names the window.</div>'
                         % badge(9, proposed_only=False)) + inner[e:]

    def comp_slug(code):
        return comps.get(code, {}).get("slug") or slug(code)

    # The built result row, kept for a team's results (result · score · opponent), in two lines: the
    # opponent wraps instead of being cut off, and the competition's name and the date sit under it.
    # The whole row is the link to the match's page, as every row that leads somewhere is.
    def recent(team):
        out = []
        for r in team["form_window"]:
            d = date.fromisoformat(r["played_kickoff_datetime"][:10])
            sides = (team["name"], r["opponent_name"]) if r["home_away"] == "home" else (r["opponent_name"], team["name"])
            out.append('<a class="mk-rwrap mk-rlink" href="%s"><div class="rmatch mk-rm"><span class="pill %s">%s</span><span class="rscore">%d&ndash;%d</span>'
                       '<span class="ropp">%s</span><span class="rmeta"><span class="mk-nw">%s</span> &middot; '
                       '<span class="mk-nw">%d %s</span></span></div></a>'
                       % (match_href(comp_slug(r["played_league_code"]), r["played_kickoff_datetime"][:10], *sides),
                          r["result"], r["result"], r["goals_for"], r["goals_against"],
                          club(r["opponent_name"], r.get("opponent_logo_url"),
                               '<span class="ha">%s</span>' % ("H" if r["home_away"] == "home" else "A")),
                          E(name(r["played_league_code"])), d.day, MONTHS[d.month - 1]))
        return '<div class="mk-rcol"><div class="colhead">%s</div>%s</div>' % (E(team["name"]), "".join(out))

    # The two lists share their row heights side by side, so a wrapped row keeps its neighbour level.
    body = '<div class="mk-rsplit">%s%s</div>' % (recent(home), recent(away))
    inner = swap(inner, '<section aria-label="Recent matches"', "</section>", section("Recent matches", body, 3))

    # The built player row kept for one team's players (photo, name and position, goals and assists),
    # its name wrapping instead of being cut off; the two teams' lists share row heights side by side.
    def players(team):
        rows = []
        for nm, pos, goals, assists, pid in SEASON_PLAYERS.get(int(team["team_id"]), []):
            photo = '<img src="https://media.api-sports.io/football/players/%d.png" alt="" loading="lazy" width="34" height="34">' % pid
            stat = ('<span class="mk-nw"><b>%d</b> %s</span> &middot; <span class="mk-nw"><b>%d</b> %s</span>'
                    % (goals, "goal" if goals == 1 else "goals", assists, "assist" if assists == 1 else "assists"))
            rows.append('<a class="mk-rwrap mk-rlink" href="/en/players/%s-%d/"><div class="prow mk-pr"><span class="pphoto">%s</span><span class="pname">'
                        '<div class="nm">%s</div><div class="ps">%s</div></span><span class="pstat">%s</span></div></a>'
                        % (slug(nm), pid, photo, E(nm), POSITION_LABELS.get(pos, ""), stat))
        return '<div class="mk-rcol"><div class="colhead">%s</div>%s</div>' % (E(team["name"]), "".join(rows))

    intro = ('<p class="bsub">Each team&rsquo;s leading players this season across all competitions, by goals plus assists. '
             '<a class="mk-chevlink" href="%s">Metric Glossary%s</a></p>' % (GLOSSARY, CHEV))
    body = intro + '<div class="mk-rsplit">%s%s</div>' % (players(home), players(away))
    inner = swap(inner, '<section aria-label="Players to watch"', "</section>", section("Players to watch", body, 4))

    # A match further out is about the pair: the team blocks, which would repeat on every one of a
    # team's future match pages, wait until the match is next.
    if STATE.startswith("future"):
        gone = ('<div class="mk-p mk-gone">%s %s waits until the match is next: the same rows stand on every one of '
                'the team&rsquo;s future match pages.</div>')
        s, e = span_of(inner, '<section aria-label="Form comparison"', "</section>")
        inner = inner[:s] + '<div class="mk-b">%s</div>' % inner[s:e] + gone % (badge(9, proposed_only=False), "Form comparison") + inner[e:]
        for label, n in (("Recent matches", 3), ("Players to watch", 4)):
            s, e = span_of(inner, '<section class="mk-p mk-chg" aria-label="%s"' % label, "</section>")
            inner = inner[:s] + gone % (badge(n, proposed_only=False), label) + inner[e:]

    # The last 5 meetings only: the totals count just the meetings inside the data window. The block's
    # intro says what the list is; the meetings are the page's result row without the chip: the score
    # in the match's order, both names with the side that was at home first, the competition and the date.
    # A pair the data has not seen meet shows that, in place of the sentence and the list.
    h = fx["head_to_head"] or {"meetings_last5": 0, "recent_meetings": []}
    n = h["meetings_last5"]
    intro = ('<p class="bsub">%s.</p>' % h2h_sentence(n, h["wins_last5"], h["draws_last5"], h["losses_last5"],
                                                          '<span class="nb">%s</span>' % E(home["name"]),
                                                          '<span class="nb">%s</span>' % E(away["name"]))
             if n else '<p class="bsub">No meetings on record.</p>')
    rows = []
    for m in h["recent_meetings"][:n]:
        ours, theirs = (home["name"], home.get("crest"), m["goals_for"]), (away["name"], away.get("crest"), m["goals_against"])
        (hn, hc, hg), (an, ac, ag) = (ours, theirs) if H2H_HOME[m["kickoff_datetime"][:10]] == int(home["team_id"]) else (theirs, ours)
        rows.append('<a class="mk-rwrap mk-rlink" href="%s"><div class="rmatch mk-rm mk-meet"><span class="rscore">%d&ndash;%d</span>'
                    '<span class="ropp">%s &ndash; %s</span>'
                    '<span class="rmeta"><span class="mk-nw">%s</span> &middot; <span class="mk-nw">%s</span></span></div></a>'
                    % (match_href(comp_slug(m["league_code"]), m["kickoff_datetime"][:10], hn, an),
                       hg, ag, club(hn, hc), club(an, ac), E(name(m["league_code"])), fdate(m["kickoff_datetime"], weekday=False)))
    body = intro + '<div class="mk-h2h">%s</div>' % "".join(rows)
    inner = swap(inner, '<section aria-label="Head to head"', "</section>", section("Head to head", body, 5))

    # A match further out leads on to what comes first: each team's next match.
    if STATE.startswith("future"):
        s, e = span_of(inner, '<section class="mk-p mk-chg" aria-label="Head to head"', "</section>")
        block = section("Next matches", upcoming_block(next_matches(fx), comps), 10)
        inner = inner[:e] + block + home_reference() + inner[e:]

    inner = swap(inner, '<section aria-label="Explore"', "</section>",
                 '<div class="mk-p mk-gone">%s The Explore block leaves: its links are the team names above and the breadcrumb.</div>'
                 % badge(6, proposed_only=False))

    inner = re.sub(r'<div class="footnote">([^<]*)</div>',
                   lambda m: '<div class="footnote mk-b">%s</div><div class="footnote mk-p mk-chg"><s>%s</s>%s</div>'
                   % (m.group(1), m.group(1), badge(7, proposed_only=False)), inner, count=1)
    return inner


PROPOSALS_FUTURE = [
    (1, "Breadcrumb", "as decided for the next match page", "decided"),
    (2, "Header", "as decided for the next match page, the competition&rsquo;s group head opening it, the venue closing the kick-off line; no table position under the teams, since the position going into the match is known only when it is next", "proposal"),
    (8, "The sentence", "none, as decided for the next match page", "decided"),
    (9, "Form comparison", "waits until the match is next: the same rows stand on every one of the team's future match pages", "proposal"),
    (3, "Recent matches", "waits until the match is next: the same rows stand on every one of the team's future match pages", "proposal"),
    (4, "Players to watch", "waits until the match is next, for the same reason", "proposal"),
    (5, "Head to head", "as decided for the next match page: the part of the page that belongs to this pair alone", "decided"),
    (6, "Explore", "leaves, as decided", "decided"),
    (7, "Page foot", "as decided", "decided"),
    (10, "Next matches", "the page's way out: each team's next match, drawn as the approved Home's Next matches (#127: the competition's head with its logo, a date heading per day, the match rows with both crests and the kick-off with its zone), every row a link to that match's page; Home's block is shown under it for comparison", "proposal"),
    (11, "Search engines", "the page is indexed only when the pair has a head to head; otherwise it stays out of the index and the sitemap until it becomes the next match", "decided2"),
]
# The export day of the sample data: a team's next match is its first fixture after it.
EXPORT_DAY = "2026-09-25"

TEAM_STATS_1575150 = {
    "goals": (2, 3), "goals_against": (3, 2), "clean_sheets": (0, 0),
    "shots": (18, 11), "shots_inside_box_pct": (61, 91), "shots_on_goal": (6, 4), "shots_on_goal_against": (4, 6),
    "shots_on_goal_pct": (33, 36), "shots_inside_box": (11, 10),
    "finishing_pct": (33, 50),
    "shots_off_goal": (7, 2), "shots_blocked": (5, 5),
    "passes": (498, 335), "passes_accuracy_pct": (80, 76), "key_passes": (15, 9), "possession_pct": (60, 40),
    "duels": (99, 99), "duels_won_pct": (44, 56), "dribbles": (14, 14), "dribbles_pct": (29, 43),
    "passes_accurate": (399, 253), "dribbles_completed": (4, 6), "duels_won": (44, 55),
    "defensive_actions": (32, 36), "tackles": (19, 15), "interceptions": (8, 16), "blocks": (5, 5),
    "saves_pct": (40, 67), "saves": (2, 4),
    "corners": (10, 3), "corners_against": (3, 10), "free_kicks": (6, 13),
    "yellow_cards": (4, 2), "red_cards": (0, 0), "fouls": (13, 7), "offsides": (1, 2)}

# State 3, a played match. The export writes no payload for one (GAP-07), so the render reads a stand-in
# read once from the marts and core: TSG 1899 Hoffenheim 2-3 Borussia Dortmund, the fourth of Dortmund's
# Recent matches on the approved next match page.
PLAYED = {
    "fixture_id": 1575150, "league_code": "BL1", "season": 2026, "round_order": 2, "round_name": "Regular Season - 2",
    "status": "FT", "kickoff": "2026-09-05T13:30:00Z", "venue": "SNP Arena",
    "about": "the fourth row of Dortmund&rsquo;s Recent matches on the approved next match page",
    "home": {"team_id": 167, "name": "TSG 1899 Hoffenheim", "slug": "tsg-1899-hoffenheim", "goals": 2,
             "crest": "https://media.api-sports.io/football/teams/167.png"},
    "away": {"team_id": 165, "name": "Borussia Dortmund", "slug": "borussia-dortmund", "goals": 3,
             "crest": "https://media.api-sports.io/football/teams/165.png"},
    # core.fct_fixture_event, the goals in match order: minute, added time, the side the goal counts for,
    # event_detail, the scorer's id, the assist as served (a name, no id).
    "goals": [(45, None, 167, "Normal Goal", 390586, "Vladimír Coufal"),
              (54, None, 167, "Normal Goal", 203040, "Adam Daghim"),
              (61, None, 165, "Normal Goal", 21393, "Waldemar Anton"),
              (66, None, 165, "Normal Goal", 129791, "Serhou Guirassy"),
              (86, None, 165, "Own Goal", 278453, None)],
    # The Form comparison's metrics over a window of this one match, (home, away): mart_team_momentum's formulas on
    # the two legs it sums (int_legs__team_match, int_legs__team_from_players), rounded; the own goal on the side it
    # counts for, where the leg today credits it to the other side.
    "team": TEAM_STATS_1575150,
    # The provider's line-ups (stg_apif__lineups, read by nothing yet): the formation, the starting eleven in the
    # provider's order, and the substitutes who came on with the minute of their substitution event.
    "lineups": {167: {"formation": "4-4-2", "xi": [702, 1231, 26300, 278453, 408853, 126642, 390586, 37153, 362564, 66019, 203040],
                      "subs": [(726, 73, 66019), (279905, 73, 126642), (162964, 79, 26300), (453903, 79, 37153),
                               (387973, 84, 203040)]},
                165: {"formation": "3-4-2-1", "xi": [25282, 409215, 25368, 341839, 24845, 326757, 637, 198654, 404891, 158644, 21393],
                      "subs": [(313236, 32, 341839), (37749, 45, 637), (129791, 62, 404891), (568225, 63, 409215),
                               (1159, 87, 21393)]}},
    # The match's most notable players, read once from mart_player_fixture_stats: per board the top three across both
    # teams by the count, a shared count sharing the rank, a tie at the cut broken by fewer minutes; under the
    # catalogue's groups: (group, [(board, [(rank, player id, the count)])]).
    "leaders": [("Shooting", [("Shots", [(1, 21393, 5), (2, 203040, 4), (3, 26300, 3)])]),
                ("Passing", [("Passes", [(1, 390586, 70), (2, 408853, 61), (3, 278453, 59)]),
                             ("Key passes", [(1, 24845, 4), (2, 408853, 3), (3, 637, 2)])]),
                ("One-on-one", [("Dribbles attempted", [(1, 404891, 6), (2, 362564, 5), (3, 203040, 3)]),
                                ("Duels won", [(1, 198654, 9), (2, 37153, 8), (3, 404891, 7)])]),
                ("Defending", [("Defensive actions", [(1, 25368, 8), (2, 37153, 6), (2, 198654, 6)])]),
                ("Discipline", [("Fouls", [(1, 126642, 3), (2, 404891, 2), (2, 37153, 2)])])],
    # mart_player_fixture_stats, every player with minutes: team, id, name, position, minutes, goals, assists.
    "players": [(167, 702, "O. Baumann", "G", 90, 0, 0), (167, 362564, "A. Daghim", "M", 90, 0, 1),
                (167, 1231, "V. Coufal", "D", 90, 0, 1), (167, 408853, "M. Rots", "D", 90, 0, 0),
                (167, 390586, "L. Avdullahu", "M", 90, 1, 0), (167, 278453, "A. Hajdari", "D", 90, 0, 0),
                (167, 203040, "T. Lemperle", "F", 84, 1, 0), (167, 26300, "O. Kabak", "D", 79, 0, 0),
                (167, 37153, "W. Burger", "M", 79, 0, 0), (167, 126642, "P. Wimmer", "M", 73, 0, 0),
                (167, 66019, "A. Hložek", "F", 73, 0, 0), (167, 726, "A. Kramarić", "F", 17, 0, 0),
                (167, 279905, "B. Conté", "M", 17, 0, 0), (167, 162964, "R. Hranáč", "D", 11, 0, 0),
                (167, 453903, "Nathan De Cat", "M", 11, 0, 0), (167, 387973, "Max Moerstedt", "F", 6, 0, 0),
                (165, 158644, "M. Beier", "M", 90, 0, 0), (165, 25282, "G. Kobel", "G", 90, 0, 0),
                (165, 24845, "J. Ryerson", "M", 90, 0, 0), (165, 198654, "D. Svensson", "M", 90, 0, 0),
                (165, 25368, "W. Anton", "D", 90, 0, 1), (165, 326757, "J. Bellingham", "M", 90, 0, 0),
                (165, 21393, "S. Guirassy", "F", 87, 1, 1), (165, 409215, "Kouakou Joane Gadou", "D", 63, 0, 0),
                (165, 404891, "K. Karetsas", "M", 62, 0, 0), (165, 313236, "E. Nwaneri", "M", 58, 0, 0),
                (165, 37749, "J. Veerman", "M", 45, 0, 0), (165, 637, "F. Nmecha", "M", 45, 0, 0),
                (165, 341839, "F. Mané", "D", 32, 0, 0), (165, 129791, "Fábio Silva", "F", 28, 1, 0),
                (165, 568225, "L. Reggiani", "D", 27, 0, 0), (165, 1159, "M. Sabitzer", "M", 3, 0, 0)],
}
# A match settled on penalties, read the same way: FC Viktoria Köln 1-1 1. FC Nürnberg, the DFB-Pokal's first round.
# The shoot-out score is served nowhere yet (block 2, decision A); the stand-in reads it from the provider's payload,
# where it arrives with the match (score.penalty). The shoot-out's kicks are not among the events.
PLAYED_PEN = {
    "fixture_id": 1550700, "league_code": "DFBP", "season": 2026, "round_order": 64, "round_name": "Round of 64",
    "status": "PEN", "kickoff": "2026-08-22T13:30:00Z", "venue": "Sportpark Hohenberg",
    "about": "a match settled on penalties",
    "home": {"team_id": 1620, "name": "FC Viktoria Köln", "slug": "fc-viktoria-koln", "goals": 1, "shootout": 4,
             "crest": "https://media.api-sports.io/football/teams/1620.png"},
    "away": {"team_id": 171, "name": "1. FC Nürnberg", "slug": "1-fc-nurnberg", "goals": 1, "shootout": 5,
             "crest": "https://media.api-sports.io/football/teams/171.png"},
    "goals": [(56, None, 171, "Normal Goal", 511974, "Adam Markhiev"),
              (90, 6, 1620, "Normal Goal", 203070, "Pascal Fallmann")],
    # The provider sends no free kicks for this match, so that row is left out.
    "team": {"shots": (21, 11), "shots_inside_box_pct": (62, 64), "shots_on_goal": (6, 5), "finishing_pct": (17, 20),
             "shots_on_goal_against": (5, 6), "shots_off_goal": (10, 4), "shots_blocked": (5, 2),
             "shots_inside_box": (13, 7), "shots_on_goal_pct": (29, 45),
             "passes": (544, 650), "passes_accuracy_pct": (80, 87), "key_passes": (14, 9), "duels": (115, 115),
             "passes_accurate": (436, 566), "possession_pct": (46, 54),
             "dribbles": (20, 22), "dribbles_completed": (8, 6), "dribbles_pct": (40, 27), "duels_won": (68, 47),
             "duels_won_pct": (59, 41), "defensive_actions": (45, 34), "saves_pct": (75, 80), "corners": (8, 7),
             "tackles": (32, 15), "interceptions": (10, 13), "blocks": (3, 6), "saves": (3, 4),
             "corners_against": (7, 8), "fouls": (15, 17), "offsides": (4, 0),
             "yellow_cards": (3, 2), "red_cards": (0, 0)},
    # Read as the full-time match's are; the substitutes' minutes come from the substitution events.
    "lineups": {1620: {"formation": "4-4-2", "xi": [203381, 203070, 128138, 380629, 90649, 535071, 90697, 442151, 202565, 728, 352265],
                       "subs": [(273718, 46, 535071), (353670, 57, 352265), (272235, 74, 90697), (329472, 74, 202565),
                                (548586, 87, 728)]},
                171: {"formation": "4-2-3-1", "xi": [25651, 380969, 313222, 202942, 478854, 387361, 618443, 177661, 366021, 338355, 511974],
                      "subs": [(26677, 67, 380969), (330603, 67, 338355), (26502, 78, 511974), (663755, 79, 366021),
                               (620025, "90+4", 313222)]}},
    # A tie the minutes leave standing at the cut goes by name.
    "leaders": [("Shooting", [("Shots", [(1, 511974, 4), (2, 203070, 3), (3, 353670, 2)])]),
                ("Passing", [("Passes", [(1, 202942, 102), (2, 387361, 83), (2, 128138, 83)]),
                             ("Key passes", [(1, 272235, 3), (1, 366021, 3), (3, 548586, 2)])]),
                ("One-on-one", [("Dribbles attempted", [(1, 535071, 7), (2, 177661, 6), (3, 387361, 5)]),
                                ("Duels won", [(1, 203070, 10), (2, 535071, 8), (2, 128138, 8)])]),
                ("Defending", [("Defensive actions", [(1, 387361, 7), (1, 128138, 7), (1, 380629, 7)])]),
                ("Discipline", [("Fouls", [(1, 329472, 3), (1, 330603, 3), (1, 618443, 3)])])],
    "players": [(1620, 380629, "Tim Kloss", "D", 120, 0, 0), (1620, 90649, "K. Jakob", "D", 120, 0, 0),
                (1620, 203070, "M. Sponsel", "D", 120, 1, 0), (1620, 203381, "A. Schulz", "G", 120, 0, 0),
                (1620, 128138, "T. Eisenhuth", "D", 120, 0, 0), (1620, 442151, "Niklas Swider", "M", 120, 0, 0),
                (1620, 728, "D. Otto", "F", 87, 0, 0), (1620, 273718, "A. Prokopenko", "F", 75, 0, 0),
                (1620, 202565, "L. Wolf", "M", 74, 0, 0), (1620, 90697, "T. Duman", "M", 74, 0, 0),
                (1620, 353670, "N. Le Bret", "F", 63, 0, 0), (1620, 352265, "N. Castelle", "F", 57, 0, 0),
                (1620, 329472, "N. Jahn", "M", 46, 0, 0), (1620, 272235, "P. Fallmann", "D", 46, 0, 1),
                (1620, 535071, "Y. Tonye", "M", 45, 0, 0), (1620, 548586, "J. Sachse", "F", 33, 0, 0),
                (171, 618443, "J. Fernandez", "M", 120, 0, 0), (171, 177661, "J. Justvan", "M", 120, 0, 0),
                (171, 202942, "F. Otto", "D", 120, 0, 0), (171, 387361, "A. Marhiev", "M", 120, 0, 1),
                (171, 478854, "E. Porstner", "D", 120, 0, 0), (171, 25651, "J. Reichert", "G", 120, 0, 0),
                (171, 313222, "A. Kalogeropoulos", "D", 89, 0, 0), (171, 511974, "P. Scobel", "F", 78, 1, 0),
                (171, 366021, "Rafael Lubach", "M", 78, 0, 0), (171, 380969, "T. Janisch", "D", 67, 0, 0),
                (171, 338355, "M. Zoma", "M", 67, 0, 0), (171, 330603, "Can Yaha Moustfa", "F", 53, 0, 0),
                (171, 26677, "G. Masouras", "D", 53, 0, 0), (171, 26502, "A. Grimaldi", "F", 42, 0, 0),
                (171, 663755, "T. Hess", "D", 42, 0, 0), (171, 620025, "K. Mandic", "D", 31, 0, 0)],
}
STATUS_WORDS = {"FT": "Full time", "AET": "After extra time", "PEN": "After penalties"}
# The Form comparison's groups and rows as approved, in their order, and the catalogue's new and not yet shown team
# metrics beside what they belong with: possession before the passes, a count before its share, the whistle before
# the card; Shooting reads the counts that make up the shots, then its two rates. Off in one match: the Goals group (the header's score
# and the Goals block show it). (label without a sign, the match's total, +1 when more is better, -1 when fewer is,
# as the catalogue's direction, the value's unit).
PLAYED_STATS = (("Shooting", (("Shots", "shots", 1, ""), ("Shots on target", "shots_on_goal", 1, ""),
                              ("Shots on target against", "shots_on_goal_against", -1, ""),
                              ("Shots off target", "shots_off_goal", 1, ""), ("Blocked shots", "shots_blocked", 1, ""),
                              ("Shots inside box", "shots_inside_box", 1, ""),
                              ("Shots inside box<small>percentage</small>", "shots_inside_box_pct", 1, "%"),
                              ("Shooting accuracy", "shots_on_goal_pct", 1, "%"),
                              ("Goals per shot on target", "finishing_pct", 1, "%"))),
                ("Passing", (("Passes", "passes", 1, ""), ("Accurate passes", "passes_accurate", 1, ""),
                             ("Pass accuracy", "passes_accuracy_pct", 1, "%"), ("Possession", "possession_pct", 1, "%"),
                             ("Key passes", "key_passes", 1, ""))),
                ("One-on-one", (("Dribbles attempted", "dribbles", 1, ""), ("Dribbles completed", "dribbles_completed", 1, ""),
                                ("Dribbles completed<small>percentage</small>", "dribbles_pct", 1, "%"),
                                ("Duels", "duels", 1, ""), ("Duels won", "duels_won", 1, ""),
                                ("Duels won<small>percentage</small>", "duels_won_pct", 1, "%"))),
                ("Defending", (("Defensive actions", "defensive_actions", 1, ""), ("Tackles", "tackles", 1, ""),
                               ("Interceptions", "interceptions", 1, ""), ("Blocks", "blocks", 1, ""))),
                ("Goalkeeping", (("Saves", "saves", 1, ""), ("Saves<small>percentage</small>", "saves_pct", 1, "%"))),
                ("Set pieces", (("Corners", "corners", 1, ""), ("Corners against", "corners_against", -1, ""),
                                ("Free kicks", "free_kicks", 1, ""))),
                ("Discipline", (("Fouls", "fouls", -1, ""), ("Offsides", "offsides", -1, ""),
                                ("Yellow cards", "yellow_cards", -1, ""), ("Red cards", "red_cards", -1, ""))))
# The render each element was approved on: the next match page (#132, state 1).
APPROVED_RENDER = HERE / "renders" / "match-page_2026-09-27_56.html"

# The header as approved, with the final score where "vs" stands: the winner by weight, as on every played
# match row. Under 700px the teams stack and each team's goals close its line, as the match row's sides do.
PLAYED_CSS = """
@media (min-width: 700px) {
  .mk-played .mk-score { display: flex; align-items: center; gap: 10px; }
}
.mk-played .mk-score { font-size: clamp(30px, 6cqw, 40px); font-weight: 400; letter-spacing: 0; text-transform: none;
                       color: var(--ink); font-variant-numeric: tabular-nums; }
.mk-played .mk-score .mk-dash { color: var(--muted); }
.mk-played .mk-score .winner, .mk-played .mk-sg.winner { font-weight: 700; }
.mk-played .mk-sg { display: none; }
@media (max-width: 699.98px) {
  .mk-played .mk-team { grid-template-columns: auto 1fr auto; }
  .mk-played .mk-sg { display: block; grid-column: 3; grid-row: 1; align-self: center;
                      font-size: 24px; font-weight: 400; color: var(--ink); font-variant-numeric: tabular-nums; }
}
/* After penalties, the score after extra time closes the header in the kick-off line's form. */
.mk-played .mk-pens { font-size: 13px; color: var(--muted); margin-top: 14px; }
.mk-played .mk-pens b { color: var(--ink-2); font-weight: 600; }
#mk-prop:checked ~ .mk-page section[aria-label="Match stats"] .win-w1 { display: block !important; }
section[aria-label="Players"] .mk-rcol, section[aria-label="Line-ups"] .mk-rcol { grid-row: span %(rows)d; }
/* The goal row, a row of its own: its minute and assist are part of the goal, so its second line is larger and
   lighter than the list rows' 12px grey. */
section[aria-label="Goals"] .mk-rm .rmeta { font-size: 14px; color: var(--ink-2); }
"""

SOURCES_PLAYED = {
    "mast": {
        "rows": [
            ("Full time", "site text, chosen by <code>mart_competition_fixtures.status_short</code>: FT &ldquo;Full time&rdquo;, "
             "AET &ldquo;After extra time&rdquo;, PEN &ldquo;After penalties&rdquo;", "never missing on a played match"),
            ("Matchday 2 &middot; Sat, 5 Sept 2026 &middot; 13:30 UTC", "as on the next match page: <code>.round_order</code>, "
             "<code>.kickoff_datetime</code> (UTC until #146)", "as on the next match page"),
            ("SNP Arena", "no mart serves it: <code>core.fct_fixture.venue_name_snapshot</code>", "left out"),
            ("the two names, crests and links", "<code>mart_competition_fixtures</code>, as on the next match page", "as on the next match page"),
            ("2 &ndash; 3", "<code>mart_competition_fixtures.goals_home</code>, <code>.goals_away</code>: the final score, "
             "extra time included", "not tested on a played match (gap 3)"),
            ("no table position", "the position a team took into a past match is not served: "
             "<code>mart_fixture_standing_context</code> serves the next match only", "&ndash;"),
        ],
        "gaps": [
            "1. The venue is in no mart, as on the next match page: <code>mart_competition_fixtures</code> gains its name.",
            "2. The half-time score and a shoot-out's score are carried nowhere: <code>fct_fixture</code> keeps the final "
            "score only, and the ingest never reads the provider's half-time, extra-time and penalty scores. A match "
            "settled on penalties would read &ldquo;After penalties&rdquo; with a drawn score and no shoot-out result.",
            "3. Nothing tests that a played match has both goal counts.",
        ],
    },
    "Goals": {
        "rows": [
            ("which goals, in order", "<b>no mart serves a match's events</b>: <code>core.fct_fixture_event</code>, "
             "<code>event_type</code> Goal, by <code>minute_elapsed</code>, <code>minute_extra</code>, <code>event_index</code>",
             "no events for the match (271 of 4,807 played this season): the block is absent; a 0&ndash;0: absent"),
            ("1&ndash;0", "the score after the goal, counted from the goal rows and the side each counts for (<code>team_sk</code>): "
             "computed where the page is built, not served (gap 1)", "&ndash;"),
            ("L. Avdullahu", "<code>player_sk</code>, named by <code>dim_player</code> as every player row names him; the "
             "event's own <code>player_name_snapshot</code> is the long form (&ldquo;Leon Avdullahu&rdquo;)", "no id: not served (gap 1)"),
            ("the crest", "the side the goal counts for, <code>team_sk</code> (an own goal counts for the other side), "
             "with the header's crests", "never missing: tested not null"),
            ("45&rsquo; &middot; 45+2&rsquo;", "<code>minute_elapsed</code>, <code>minute_extra</code>", "not tested (gap 2)"),
            ("Own goal &middot; Penalty", "<code>event_detail</code> &ldquo;Own Goal&rdquo;, &ldquo;Penalty&rdquo;", "not tested (gap 2)"),
            ("Assist: Vladim&iacute;r Coufal", "<code>assist_player_name</code>: a name only, no id, in the long form",
             "no assist: left out"),
            ("the link", "the scorer's player page, as every Players to watch row", "a player without a page: no link (#169)"),
        ],
        "gaps": [
            "1. No mart serves a match's events: a mart at one row per event, reading <code>fct_fixture_event</code>, with "
            "the player named by id, the side the goal counts for and the score after it. The page reads that mart.",
            "2. <code>event_type</code>, <code>event_detail</code> and the minute have no test; the only readers today count "
            "penalties and own goals.",
            "3. The assist is a name without an id (the provider sends none), so it cannot link and does not match the "
            "form every other row uses (&ldquo;V. Coufal&rdquo;).",
            "4. The event's team name snapshot reads &ldquo;1899 Hoffenheim&rdquo;; the page reads the team by id.",
        ],
    },
    "Match stats": {
        "rows": [
            ("the groups, their order, the labels, which side is better", "the approved Form comparison's: "
             "<code>metric_catalogue</code> (<code>direction</code>), <code>metrics_display.md</code>, Discipline after Set pieces",
             "never missing"),
            ("every value", "<b>the Form comparison's source, a window of one match</b>: <code>mart_team_momentum</code>, its "
             "columns (<code>shots_per_match</code> &hellip; <code>saves_pct</code>, the cards), filtered to this match "
             "instead of the last 5. Not served yet (gap 1); the mock reads a stand-in: the mart's formulas on the two legs "
             "it sums, <code>int_legs__team_match</code> and <code>int_legs__team_from_players</code>",
             "as the Form comparison: a rate whose input is missing is &ldquo;&ndash;&rdquo; on that side; both sides: the "
             "row is left out"),
            ("18 &middot; 99 &middot; 32", "over one match an average is the match's count, so it reads as a whole number, "
             "with no &ldquo;per match&rdquo; line", "&ndash;"),
            ("33% &middot; 50%, Finishing", "open-play goals over shots on goal; the stand-in puts the own goal "
             "on the side it counts for, where the leg today puts it on the other (gap 2)", "&ndash;"),
            ("Shots off goal &middot; Shots blocked &middot; Fouls &middot; Offsides &middot; Free kicks &middot; Possession",
             "<b>new in the catalogue</b>: the provider&rsquo;s team line (free kicks: the provider sends it, staging drops "
             "it today), carried by the team leg; Possession: own passes over both teams&rsquo; passes. The stand-in read "
             "them once", "a blank is unknown, not zero: the provider writes real zeros for these"),
            ("Tackles &middot; Interceptions &middot; Blocks &middot; Saves &middot; Shots on goal against", "already catalogued (Shots on goal against: a Rankings board; the others shown nowhere yet): the opponent&rsquo;s shots on goal, the "
             "player legs (the parts of Defensive actions), the goalkeepers&rsquo; saves on the team line", "as above"),
            ("the order", "the Form comparison&rsquo;s groups and rows in their locked order; the new rows beside what they "
             "belong with: Possession first in Passing, Saves before Save percentage, Fouls and Offsides before the cards",
             "&ndash;"),
            ("the whole block", "the match's legs", "no team stat line (1,134 of 4,807 played this season): the block is absent"),
        ],
        "gaps": [
            "1. One source for a team's metrics over any window: the Form comparison's mart serves this match as a window "
            "of one (its window type says so), the same columns, formulas and coverage rules, so the two blocks cannot "
            "disagree. <code>mart_team_fixture_stats</code>, a copy of the provider's stat line with its own blanks (pass "
            "accuracy empty where both counts are served, red cards empty where every player's line says 0), then has no "
            "reader on the site and retires with the matchstats export this page replaces. A window of one is not "
            "&ldquo;momentum&rdquo;: the mart's name is yours at the build.",
            "2. The defect found in block 3: <code>int_legs__team_match</code> credits own goals to the wrong side and "
            "counts the shoot-out's kicks as penalty goals, so Finishing is wrong in every match with an "
            "own goal or a shoot-out, here and in the Form comparison (the leg gives 17% and 75% for this match).",
            "3. Rounding: the stand-in rounds; the served values should come rounded from the warehouse (#108).",
            "4. Free kicks: the provider does not say what it counts; it matches free kicks won (Dortmund&rsquo;s 13 are "
            "Hoffenheim&rsquo;s 13 fouls), and it is sent on only 54 of 72 Bundesliga team lines this season.",
        ],
    },
    "Match leaders": {
        "rows": [
            ("which players, in which order", "the match&rsquo;s player stat lines (<code>mart_player_fixture_stats</code>), "
             "per board the top three across both teams by the count, a tie broken by fewer minutes as Players to watch "
             "breaks one; the rank computed where the page is built, not served (gap 1)",
             "no player stats (1,353 of 4,807 played this season): the block is absent; fewer than three players above 0: "
             "fewer rows, as a zero is no rank"),
            ("the seven boards", "Shots <code>shots_total</code>, Passes "
             "<code>passes_total</code>, Key passes <code>passes_key</code>, Dribbles attempted <code>dribbles_attempts</code>, "
             "Duels won <code>duels_won</code>, Defensive actions <code>tackles_total + tackles_interceptions + tackles_blocks</code>, "
             "Fouls <code>fouls_committed</code>; under the catalogue&rsquo;s groups and in its order", "&ndash;"),
            ("the crest and the club", "the player&rsquo;s team in the match, named and crested as the header", "the crest: an empty box"),
            ("the link", "the player&rsquo;s page, as every player row", "a player without a page: no link (#169)"),
        ],
        "gaps": [
            "1. The rank is not served: the warehouse ranks each board (the dense rank the state 1 review asked for), from the "
            "one source of a player&rsquo;s numbers over a window, here one match, as block 4 set it for teams.",
            "2. A tie at the cut: here Shots has two players on 3, Key passes and Fouls six on 2; "
            "over this season&rsquo;s 3,451 matches the third place is shared past three rows in 64% (Shots, Key passes) to 77% "
            "(Dribbles completed) of them. The mock breaks a tie by fewer minutes and cuts at three: a board rule to set.",
            "3. A board can belong to one team: here all three Passes rows are Hoffenheim&rsquo;s.",
        ],
    },
    "Line-ups": {
        "rows": [
            ("which players, in which order", "<b>no mart serves line-ups</b>: the provider&rsquo;s line-ups, staged in "
             "<code>stg_apif__lineups</code> and read by nothing: the starting eleven in the provider&rsquo;s order, then the "
             "substitutes who came on, by the minute they came on", "no line-ups (350 of 4,807 played this season): the block is absent"),
            ("4-4-2", "the line-ups&rsquo; <code>formation</code>", "left out"),
            ("the name, photo and position", "the player&rsquo;s id in the line-up, named as every player row names him "
             "(<code>dim_player</code>); the position from his stat line", "the photo: the initials"),
            ("came on 73&rsquo;", "the substitution event&rsquo;s minute (the events mart, block 3), the player coming on read by "
             "his id, which the provider sends and staging drops today", "left out"),
            ("90 min", "<code>mart_player_fixture_stats.minutes_played</code>", "no player stats: no minutes, the rows stay"),
            ("the link", "the player&rsquo;s page, as every Players to watch row", "a player without a page: no link (#169)"),
        ],
        "gaps": [
            "1. A mart at one row per match player: from the line-ups (who started, the bench, the formation, the coach), "
            "with the minutes from the player stats and the minute a substitute came on from the events. It replaces the "
            "stat line&rsquo;s starter flag, wrong on 1,318 of 6,242 team line-ups this season.",
            "2. The line-ups cover 4,457 of 4,807 played matches this season (93%), 4,327 with exactly eleven starters each; "
            "player stats cover 72%.",
            "3. <code>mart_player_match_log</code> serves the same stat line from the player&rsquo;s side: two marts for one "
            "content, as #173 found for lists of matches.",
        ],
    },
    "Players": {
        "rows": [
            ("which players", "<code>mart_player_fixture_stats</code>, every player of the side with "
             "<code>minutes_played</code> above 0", "no player stats (1,353 of 4,807 played this season): the block is absent"),
            ("the order", "by <code>position_code</code> (goalkeeper, defence, midfield, forward), then minutes", "&ndash;"),
            ("the name, photo and position", "<code>player_name</code>, <code>player_photo_url</code>, <code>position_code</code>",
             "the photo: the initials"),
            ("90 min", "<code>minutes_played</code>", "not tested"),
            ("the link", "the player's page, as every Players to watch row", "a player without a page: no link (#169)"),
        ],
        "gaps": [
            "1. Who started and who came on is not reliable: this season 1,318 of 6,242 teams' match lines flag more than "
            "11 starters. This match flags all 16 of each side as starters and none as a substitute; the substitution "
            "events name who came on, by name only.",
            "2. The line-ups themselves (the formation, the coach, the starting eleven, the bench) are staged "
            "(<code>stg_apif__lineups</code>) and read by nothing.",
            "3. <code>mart_player_match_log</code> serves the same stat line from the player's side: two marts for one "
            "content, as #173 found for lists of matches.",
        ],
    },
}


def source_note(src):
    """A block's data sources, in the form add_sources draws them, shown by the toggle."""
    return ('<div class="mk-src"><b>Data</b><table><tr><th>On the page</th><th>Comes from</th><th>When it is missing</th></tr>'
            '%s</table>%s</div>' % ("".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % r for r in src["rows"]),
                                    "".join('<div class="mk-gap">Gap %s</div>' % g for g in src["gaps"])))


def approved(what, body, aria="For comparison"):
    """An approved instance of an element, copied from the render it was approved on, shown under ours."""
    return ('<section class="mk-p mk-ref" aria-label="%s"><div class="mk-reflabel">For comparison, not part of the '
            'page: %s</div>%s</section>' % (aria, what, body))


def comp_head_ref():
    """Home's competition group head as approved, copied from its render, shown under the header that opens with it."""
    home = HOME_RENDER.read_text(encoding="utf-8")
    s = home.index('<div class="gh">', home.index('<div class="fxgroup">'))
    return approved("the competition group head, Home&rsquo;s Next matches as approved (#127, render home_2026-09-17_02)",
                    '<div class="fxgroup">%s</div>' % home[s:block_end(home, s)], aria="For comparison: the competition group head")


def approved_parts():
    """The approved instances the played match's blocks use, copied from the state 1 render of record."""
    page = APPROVED_RENDER.read_text(encoding="utf-8")
    s = page.index('<nav class="crumb mk-adapt"')
    crumb = page[s:page.index("</nav>", s) + len("</nav>")]
    s = page.index('<header class="mast mk-p mk-chg mk-stack">')
    mast = page[s:page.index("</header>", s) + len("</header>")]
    mast = mast.replace(" mk-chg", "").replace(badge(2, proposed_only=False), "")
    s = page.index('<div class="mk-h2h">') + len('<div class="mk-h2h">')
    second = page.index('<a class="mk-rwrap', page.index('<a class="mk-rwrap', s) + 1)
    meetings = page[s:page.index("</a>", second) + len("</a>")]
    fs = page.index('<section aria-label="Form comparison"')
    s = page.index('<div class="cmp">', page.index('<div class="win win-w1">', fs))
    comparison = page[s:block_end(page, s)].replace(" mk-chg", "")
    s = page.index('<div class="mk-rsplit">', page.index('<section class="mk-p mk-chg" aria-label="Players to watch"'))
    players = page[s:block_end(page, s)]
    return {
        "crumb": approved("the breadcrumb as approved (#132 state 1, render match-page_2026-09-27_56)", crumb),
        "mast": approved("the header as approved (#132 state 1, render match-page_2026-09-27_56)", mast),
        "Goals": approved("the result row without its chip, Head to head&rsquo;s meetings as approved (#132 state 1, "
                          "render match-page_2026-09-27_56), its first two rows", '<div class="mk-h2h">%s</div>' % meetings),
        "Match stats": approved("the Form comparison as approved (#132 state 1, render match-page_2026-09-27_56): every "
                                "group and row, over each team&rsquo;s last 5 matches",
                                '<div class="win win-w1">%s</div>' % comparison, aria="Form comparison"),
        "Players": approved("the player row, Players to watch as approved (#132 state 1, render match-page_2026-09-27_56)", players),
        "comp": comp_head_ref(),
    }


def played_mast(fx, slugs, round_label, head):
    """The header as decided for the next and the future match page, played: the final score where "vs" stands.
    A team with no team page gets no link and no chevron. After penalties the score is the shoot-out's and the score
    after extra time closes the header, in the kick-off line's form."""
    home, away = fx["home"], fx["away"]
    units = [round_label, fdate(fx["kickoff"]), fx["kickoff"][11:16] + " UTC", E(fx["venue"])]
    kick_html = " &middot; ".join('<span class="mk-nw">%s</span>' % u for u in units)

    def win(side, other, key="goals"):
        return " winner" if side[key] > other[key] else ""

    # After penalties the score is the shoot-out's, as the label says, and the line under it the score after
    # extra time.
    key = "shootout" if fx["status"] == "PEN" else "goals"

    def team(side, other):
        linked = int(side["team_id"]) in slugs
        head_words, _, last = E(side["name"]).rpartition(" ")
        name = '%s%s<span class="mk-nw">%s%s</span>' % (head_words, " " if head_words else "", last, CHEV if linked else "")
        body = ('<div class="crest"><img src="%s" alt="" loading="lazy" width="52" height="52"></div><span class="tname">%s</span>'
                '<span class="mk-sg num%s">%d</span>' % (E(side["crest"]), name, win(side, other, key), side[key]))
        if linked:
            return '<a class="team mk-team" href="/en/teams/%s/">%s</a>' % (slugs[int(side["team_id"])], body)
        return '<div class="team mk-team">%s</div>' % body

    score = ('<div class="vs mk-score"><span class="num%s">%d</span><span class="mk-dash">&ndash;</span><span class="num%s">%d</span></div>'
             % (win(home, away, key), home[key], win(away, home, key), away[key]))
    pens = ('<div class="mk-pens"><b class="num">%d</b>&ndash;<b class="num">%d</b></div>' % (home["goals"], away["goals"])
            if fx["status"] == "PEN" else "")
    return ('<header class="mast mk-p mk-chg mk-stack mk-played">%s%s<div class="eyebrow">%s</div><div class="kick">%s</div>'
            '<div class="teams">%s%s%s</div>%s</header>'
            % (badge(2, proposed_only=False), head, STATUS_WORDS[fx["status"]], kick_html, team(home, away), score,
               team(away, home), pens))


def played_sources(fx):
    """The data-source tables, with the drawn match's own examples; the shoot-out match adds the line decision A serves."""
    src = copy.deepcopy(SOURCES_PLAYED)
    comps = json.loads((DATA / "competitions.json").read_text(encoding="utf-8"))
    src["mast"]["rows"].insert(1, (E(comps.get(fx["league_code"], {}).get("name") or fx["league_code"]),
                                   "the group head: <code>mart_competition_index.competition_name</code>, <code>.logo_url</code>, the link by <code>.slug</code>",
                                   "the name: not guaranteed, its not-null test is in #166; the logo: an empty box"))
    if fx is PLAYED:
        return src
    mast = src["mast"]["rows"]
    mast[2] = ("Round of 64 &middot; Sat, 22 Aug 2026 &middot; 13:30 UTC", "a cup&rsquo;s round: <code>.round_name</code>, the "
               "provider&rsquo;s words, until #148; <code>.kickoff_datetime</code> (UTC until #146)", "as on the next match page")
    mast[3] = ("Sportpark Hohenberg",) + mast[3][1:]
    mast[4] = (mast[4][0], mast[4][1], "neither club has a team page in the sample: no link, no chevron")
    mast[5] = ("4 &ndash; 5, after penalties the shoot-out&rsquo;s score", "<b>not served yet</b> (decision A): the provider&rsquo;s "
               "<code>score.penalty</code> and <code>teams.*.winner</code>, which arrive with the match and staging drops; "
               "<code>fct_fixture</code> and <code>mart_competition_fixtures</code> carry them. The mock reads a stand-in from the payload",
               "not a shoot-out: the final score")
    mast.insert(6, ("1&ndash;1 under it", "<code>mart_competition_fixtures.goals_home</code>, <code>.goals_away</code>: the score "
                    "after extra time", "not a shoot-out: no line"))
    src["mast"]["gaps"][1] = ("2. Decided (A): the shoot-out score and who went through, read by staging from the payload we already "
                              "download. 125 matches went to penalties this season; 18 of them are second legs, whose own score is not level.")
    goals = src["Goals"]["rows"]
    goals[1] = ("0&ndash;1",) + goals[1][1:]
    goals[2] = ("P. Scobel", "<code>player_sk</code>, named by <code>dim_player</code> as every player row names him", goals[2][2])
    goals[4] = ("56&rsquo; &middot; 90+6&rsquo;",) + goals[4][1:]
    goals[6] = ("Assist: Adam Markhiev",) + goals[6][1:]
    src["Goals"]["gaps"][2] = ("3. The assist is a name without an id (the provider sends none): it cannot link, and it is not even "
                               "spelt as the player&rsquo;s own row: &ldquo;Adam Markhiev&rdquo; here, &ldquo;A. Marhiev&rdquo; in Line-ups.")
    del src["Goals"]["gaps"][3]
    stats = src["Match stats"]
    stats["rows"][2] = ("21 &middot; 115 &middot; 45",) + stats["rows"][2][1:]
    stats["rows"][3] = ("17% &middot; 20%, Finishing", "open-play goals over shots on goal; this match has "
                        "no own goal, and its shoot-out&rsquo;s kicks are not among its events", "&ndash;")
    stats["gaps"][1] = ("2. The defect found in block 3 (own goals on the wrong side, the shoot-out&rsquo;s kicks counted as "
                        "penalty goals) misses this match, but not the 394 whose shoot-out kicks are among the events.")
    src["Players"]["gaps"][0] = ("1. Who started and who came on is not reliable: this season 1,318 of 6,242 teams&rsquo; match lines "
                                 "flag more than 11 starters. This match flags them correctly; the Bundesliga match drawn before "
                                 "flags all 16 of each side as starters.")
    return src


def goals_block(fx):
    """Each goal in match order, in the result row without its chip (Head to head's meeting row): the score after the
    goal where the meeting's score stands, the scorer with the crest of the side it counts for, the minute and the
    assist; each row a link to the scorer's page."""
    names = {p[1]: p[2] for p in fx["players"]}
    score, rows = [0, 0], []
    for minute, added, team, detail, pid, assist in fx["goals"]:
        side = fx["home"] if team == fx["home"]["team_id"] else fx["away"]
        score[side is fx["away"]] += 1
        meta = ["%d%s'" % (minute, "+%d" % added if added else "")]
        meta += {"Own Goal": ["Own goal"], "Penalty": ["Penalty"]}.get(detail, [])
        meta += ["Assist: %s" % E(assist)] if assist else []
        rows.append('<a class="mk-rwrap mk-rlink" href="/en/players/%s-%d/"><div class="rmatch mk-rm mk-meet">'
                    '<span class="rscore">%d&ndash;%d</span><span class="ropp">%s</span><span class="rmeta">%s</span></div></a>'
                    % (slug(names[pid]), pid, score[0], score[1], club(names[pid], side["crest"]),
                       " &middot; ".join('<span class="mk-nw">%s</span>' % m for m in meta)))
    return section("Goals", '<div class="mk-h2h">%s</div>' % "".join(rows), 3)


def stat_row(label, home, away, direction, unit=""):
    """One row of the Form comparison: the two values, the bar of each side against the larger, the better side marked;
    a share reads with its % sign, as the approved rows do."""
    top = max([v for v in (home, away) if v is not None] or [0])
    better = None if None in (home, away) or home == away else ("home" if (home > away) == (direction > 0) else "away")

    def val(v, side):
        return '<div class="mval %s%s">%s</div>' % (side, " better" if better == side else "", "&ndash;" if v is None else "%s%s" % (v, unit))

    def fill(v, side):
        width = round(100 * v / top) if v is not None and top else 0
        return '<div class="bside %s"> <span class="fill%s" style="width:%d%%"></span> </div>' % (side, " better" if better == side else "", width)

    return ('<div class="mrow"> %s <div class="mmid"> <div class="mlabel">%s</div> <div class="mbar" aria-hidden="true"> %s %s '
            '</div> </div> %s </div>' % (val(home, "home"), label, fill(home, "home"), fill(away, "away"), val(away, "away")))


def stats_block(fx):
    """The two teams' numbers in this match in the Form comparison's head row, groups and rows; a row neither side
    serves is left out, as the approved block leaves it out."""
    head = ('<div class="mk-formhead"><div class="mk-fh home"><div class="h">%s</div></div><div class="mk-fh away">'
            '<div class="h">%s</div></div></div>' % (E(fx["home"]["name"]), E(fx["away"]["name"])))
    groups = []
    for group, rows in PLAYED_STATS:
        drawn = [stat_row(label, *fx["team"].get(col, (None, None)), direction, unit)
                 for label, col, direction, unit in rows if fx["team"].get(col, (None, None)) != (None, None)]
        if drawn:
            groups.append('<div class="mgroup">%s</div>%s' % (group, "".join(drawn)))
    intro = ('<p class="bsub">Each team&rsquo;s numbers in this match. <a class="mk-chevlink" href="%s">Metric Glossary%s</a></p>'
             % (GLOSSARY, CHEV))
    return section("Match stats", intro + '<div class="win win-w1"><div class="cmp">%s%s</div></div>' % (head, "".join(groups)), 5)


def players_block(fx):
    """Every player who played, in the player row of Players to watch, the two teams side by side: by position, then
    minutes, the minutes on the right; each row a link to the player's page."""
    def col(team):
        mine = sorted((p for p in fx["players"] if p[0] == team["team_id"]), key=lambda p: ("GDMF".index(p[3]), -p[4]))
        rows = []
        for _, pid, nm, pos, minutes, _, _ in mine:
            photo = '<img src="https://media.api-sports.io/football/players/%d.png" alt="" loading="lazy" width="34" height="34">' % pid
            rows.append('<a class="mk-rwrap mk-rlink" href="/en/players/%s-%d/"><div class="prow mk-pr"><span class="pphoto">%s</span>'
                        '<span class="pname"><div class="nm">%s</div><div class="ps">%s</div></span><span class="pstat">'
                        '<span class="mk-nw"><b>%d</b> min</span></span></div></a>'
                        % (slug(nm), pid, photo, E(nm), POSITION_LABELS[pos], minutes))
        return '<div class="mk-rcol"><div class="colhead">%s</div>%s</div>' % (E(team["name"]), "".join(rows))
    body = '<div class="mk-rsplit">%s%s</div>' % (col(fx["home"]), col(fx["away"]))
    return section("Players", body, 6)


def lineups_block(fx):
    """Each team's starting eleven in the provider's order, then the substitutes who came on, in the player row of
    Players to watch under a second column head; the formation closes the team's head, the second line says when a
    starter went off and when a substitute came on and for whom, the minutes stand on the right; each row a link to
    the player's page."""
    players = {p[1]: p for p in fx["players"]}

    def row(pid, second):
        _, _, nm, pos, minutes, _, _ = players[pid]
        photo = '<img src="https://media.api-sports.io/football/players/%d.png" alt="" loading="lazy" width="34" height="34">' % pid
        return ('<a class="mk-rwrap mk-rlink" href="/en/players/%s-%d/"><div class="prow mk-pr"><span class="pphoto">%s</span>'
                '<span class="pname"><div class="nm">%s</div><div class="ps">%s</div></span><span class="pstat">'
                '<span class="mk-nw"><b>%d</b> min</span></span></div></a>' % (slug(nm), pid, photo, E(nm), second, minutes))

    def col(team):
        line = fx["lineups"][team["team_id"]]
        off = {out: on for _, on, out in line["subs"]}
        xi = "".join(row(pid, POSITION_LABELS[players[pid][3]] + (" &middot; off %s&rsquo;" % off[pid] if pid in off else ""))
                     for pid in line["xi"])
        subs = "".join(row(pid, "%s &middot; on %s&rsquo; for %s" % (POSITION_LABELS[players[pid][3]], on, E(players[out][2])))
                       for pid, on, out in line["subs"])
        return ('<div class="mk-rcol"><div class="colhead">%s &middot; %s</div>%s<div class="colhead">Substitutes</div>%s</div>'
                % (E(team["name"]), line["formation"], xi, subs))
    body = '<div class="mk-rsplit">%s%s</div>' % (col(fx["home"]), col(fx["away"]))
    return section("Line-ups", body, 6)


def leaders_block(fx):
    """The match's most notable players in the player board of the Rankings tab, in the catalogue's order: one board
    per count, its top three across both teams, each row the rank, the club's crest, the name over the club, the
    count, and a link to the player's page. A board here ranks one match, so its name leads nowhere and carries no
    chevron."""
    players = {p[1]: p for p in fx["players"]}
    teams = {fx["home"]["team_id"]: fx["home"], fx["away"]["team_id"]: fx["away"]}
    groups = []
    for group, boards in fx["leaders"]:
        drawn = []
        for name, rows in boards:
            body = []
            for rank, pid, value in rows:
                team_id, _, nm = players[pid][:3]
                team = teams[team_id]
                body.append('<a class="ctab-row" href="/en/players/%s-%d/"><span class="rk num">%d</span><span class="tm">'
                            '<span class="crest xs"><img src="%s" alt="" loading="lazy" width="24" height="24"></span><span class="ent">'
                            '<span class="nm">%s</span><span class="sub">%s</span></span></span><span class="n num pts">%d</span></a>'
                            % (slug(nm), pid, rank, E(team["crest"]), E(nm), E(team["name"]), value))
            drawn.append('<div class="board"><div class="ctab rkt"><div class="ctab-head"><span class="h rk"></span><span class="h nmh">'
                         '<span class="bt"><span class="nm">%s</span></span></span><span class="h"></span></div>%s</div></div>'
                         % (E(name), "".join(body)))
        # Most groups hold one board here and the board names itself, so the group heading stays off.
        groups.append("".join(drawn))
    intro = ('<p class="bsub">The match&rsquo;s most notable players, across both teams. <a class="mk-chevlink" href="%s">'
             'Metric Glossary%s</a></p>' % (GLOSSARY, CHEV))
    return section("Match leaders", intro + "".join(groups), 4)


def board_ref():
    """The player board as approved on the Rankings tab (#129), copied from its render, its Finnish width probe left out."""
    page = (HERE / "renders" / "competition-rankings_2026-09-17_02.html").read_text(encoding="utf-8")
    at = page.rindex('<div class="board">', 0, page.index('href="/en/players/'))
    board = re.sub(r'<span class="fi probe"[^>]*>[^<]*</span>', "", page[at:block_end(page, at)])
    return approved("the player board, the Rankings tab as approved (#129, render competition-rankings_2026-09-17_02)",
                    board, aria="For comparison: the player board")


def played_round(fx, comps):
    """The competition's name and address word, whether it is a cup (mart_competition_index.competition_type), and the
    round as the header names it: "Matchday {n}" in a league, the round's name in a cup."""
    league = E(comps.get(fx["league_code"], {}).get("name") or fx["league_code"])
    index = json.loads((DATA / "competition_index.json").read_text(encoding="utf-8"))
    kind = next((r["competition_type"] for r in index["competitions"] if r["league_code"] == fx["league_code"]), "")
    cup = kind.endswith("_cup")
    comp = comps.get(fx["league_code"], {}).get("slug") or slug(fx["league_code"])
    return league, comp, cup, E(fx["round_name"]) if cup else "Matchday %d" % fx["round_order"]


def competition_head(fx, comps):
    """The competition group head of Home's Next matches and the Matches page (logo, name, chevron, the 2px line), the
    match under its competition as a match row is on those pages; a heading link to the competition's page. It opens
    the header on the next, the future and the played match page alike."""
    league = E(comps.get(fx["league_code"], {}).get("name") or fx["league_code"])
    comp = comps.get(fx["league_code"], {}).get("slug") or slug(fx["league_code"])
    index = json.loads((DATA / "competition_index.json").read_text(encoding="utf-8"))
    logo = next((r.get("logo_url") for r in index["competitions"] if r["league_code"] == fx["league_code"]), None)
    return ('<div class="fxgroup mk-comp"><div class="gh"><a class="cnm" href="/en/%s/"><span class="clogo">%s</span>'
            '<span class="nm">%s</span>%s</a></div></div>' % (comp, crest(logo), league, CHEV))


def played_page(fx, comps, slugs):
    """The played match's page, block by block, each approved instance under the block that uses it. A cup's trail
    reads Rounds and its header the round's name, by the competition's type (mart_competition_index)."""
    ref = approved_parts()
    sources = played_sources(fx)
    league, comp, cup, round_label = played_round(fx, comps)
    trail = adaptive_trail(league, fx["home"], fx["away"], comp=comp, level="Rounds" if cup else "Matchdays")
    crumb = '<div class="mk-p mk-chg mk-crumbbox">%s%s</div>' % (trail, badge(1, proposed_only=False))
    crumb_src = copy.deepcopy(SOURCES["crumb"])
    crumb_src["rows"][2] = (league,) + crumb_src["rows"][2][1:]
    crumb_src["rows"][4] = ("%s vs %s" % (E(fx["home"]["name"]), E(fx["away"]["name"])),) + crumb_src["rows"][4][1:]
    nxt = {"fixture_id": fx["fixture_id"], "home": fx["home"], "away": fx["away"]}
    return "".join([
        '<div class="mk-b mk-gone">No page exists for a played match today (GAP-07): the export writes no payload for one, '
        'and a row that leads to one leads nowhere. Switch to Proposed.</div>',
        source_note(crumb_src), crumb, ref["crumb"],
        source_note(sources["mast"]), played_mast(fx, slugs, round_label, competition_head(fx, comps)), ref["mast"], ref["comp"],
        source_note(sources["Goals"]), goals_block(fx), ref["Goals"],
        (source_note(SOURCES_PLAYED["Match leaders"]) + leaders_block(fx) + board_ref()) if "leaders" in fx else "",
        source_note(sources["Match stats"]), stats_block(fx), ref["Match stats"],
        source_note(sources["Line-ups" if "lineups" in fx else "Players"]),
        lineups_block(fx) if "lineups" in fx else players_block(fx), ref["Players"],
        source_note(SOURCES["Next matches"]),
        section("Next matches", upcoming_block(next_matches(nxt), comps), 7),
        home_reference(),
    ])


PROPOSALS_PLAYED = [
    (1, "Breadcrumb", "as decided: Home &rsaquo; Competitions &rsaquo; Bundesliga &rsaquo; Matchdays &rsaquo; the match", "decided"),
    (2, "Header", "the competition&rsquo;s group head opens it (Home&rsquo;s and the Matches page&rsquo;s: logo, name, "
     "chevron, the 2px line); otherwise as decided for the next and the "
     "future match page (no table position, as on a future match page: the "
     "position going into a past match is not served), with the final score where &ldquo;vs&rdquo; stands, the winner by "
     "weight as on every played match row, and &ldquo;Full time&rdquo; for &ldquo;Match preview&rdquo;; stacked on a "
     "phone, each team&rsquo;s goals close its line, as the played match row&rsquo;s sides do; after penalties the score "
     "is the shoot-out&rsquo;s and the score after extra time closes the header in the kick-off line&rsquo;s form (A: the "
     "shoot-out score and who went through are served)", "decided3"),
    (3, "Goals", "each goal in match order in the result row without its chip (Head to head&rsquo;s meeting row): the "
     "score after the goal where the meeting&rsquo;s score stands, the scorer with the crest of the side it counts for, "
     "the minute and the assist, own goal or penalty on a 14px second line; each row a link to the scorer&rsquo;s page",
     "decided3"),
    (4, "Match leaders", "the match&rsquo;s most notable players in the player board: one board per count in the "
     "catalogue&rsquo;s order, no group headings, each its top three across both teams, a tie at the cut broken by fewer "
     "minutes", "decided3"),
    (5, "Match stats", "the two teams&rsquo; numbers in this match in the Form comparison&rsquo;s head row, groups and "
     "rows, one layout at every width; the catalogue&rsquo;s metrics in its order, from the Form comparison&rsquo;s mart "
     "over a window of this one match", "decided3"),
    (6, "Line-ups", "each team&rsquo;s starting eleven in the provider&rsquo;s order under its column head, the formation "
     "closing it, then the substitutes who came on under a second column head, in the player row of Players to watch: "
     "the position and &ldquo;off 73&rsquo;&rdquo; or &ldquo;on 73&rsquo; for &hellip;&rdquo; on the second line, the "
     "minutes on the right; each row a link to the player&rsquo;s page", "decided3"),
    (7, "Next matches", "as decided for the future match page: each team&rsquo;s next match as of today, the page&rsquo;s "
     "way out, last on the page", "decided3"),
]


def legend_played(fx, comps):
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                   % (badge(n, proposed_only=False), E(where), what,
                      {"decided": "decided in state 1", "decided2": "decided in state 2",
                       "decided3": "decided in state 3"}.get(kind, "<b>yours to decide</b>"))
                   for n, where, what, kind in PROPOSALS_PLAYED)
    league, _, _, round_label = played_round(fx, comps)
    pens = (" (%d&ndash;%d on penalties)" % (fx["home"]["shootout"], fx["away"]["shootout"])) if fx["status"] == "PEN" else ""
    return """<div class="mk-legend">
<b>Match page, state 3: a played match (#132).</b> %s %d&ndash;%d %s%s, %s, %s, %s, %s. No page exists for a played match (GAP-07), so there
is nothing under <b>Built today</b>; <b>Proposed</b> draws the page from a stand-in read once from the marts and core.
Under each block, in a blue frame, the approved instance of the element it uses, copied from the render it was
approved on. <b>Data sources</b> shows where each value comes from.
<table><tr><th></th><th>Where</th><th>Proposed</th><th></th></tr>%s</table>
<b>Across the page:</b><ul>
<li>The export writes no payload for a played match: its fixture target takes unplayed matches only (GAP-07).</li>
<li>Which played matches get a page is open: 4,807 were played this season in 47 competitions, 59,798 in the data
window, each in three languages. Rows on approved pages already lead to them (Recent matches, Head to head back to
2024, the Matchdays tab&rsquo;s and the Matches page&rsquo;s played rows). Counted and costed before anything is
built, as #169&ndash;#171.</li>
<li>What the data holds for the 4,807 played this season: events for 4,536, a team stat line for 3,673, player stats
for 3,454; 271 only the score. A block with nothing to show is absent.</li>
</ul>
</div>""" % (E(fx["home"]["name"]), fx["home"]["goals"], fx["away"]["goals"], E(fx["away"]["name"]), pens,
             fdate(fx["kickoff"], weekday=False), league, round_label, fx["about"], rows)


def legend(fx):
    if STATE.startswith("future"):
        rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                       % (badge(n, proposed_only=False), E(where), what,
                          {"decided": "decided in state 1", "decided2": "decided"}.get(kind, "<b>yours to decide</b>"))
                       for n, where, what, kind in PROPOSALS_FUTURE)
        rnd, _ = served_round(fx)
        return """<div class="mk-legend">
<b>Match page, state 2: a match further out than the next matchday (#132).</b> %s vs %s, %s, Bundesliga
matchday %s, as the site builds it from the 2026-09-25 export. <b>Built today</b> is that page unchanged:
the next match page's template, every block. <b>Proposed</b> is the future match page: the state 1 design,
about the pair only. The page turns into the next match page when its matchday is the next one.
<table><tr><th></th><th>Where</th><th>Proposed</th><th></th></tr>%s</table>
<b>Gap:</b> which side was at home in each meeting is not served (the mock reads a stand-in), as on the
next match page.
</div>""" % (E(fx["home"]["name"]), E(fx["away"]["name"]), fdate(fx["kickoff"], weekday=False), rnd["round_order"], rows)
    rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                   % (badge(n, proposed_only=False), E(where), what,
                      "fix, no decision" if kind == "fix" else "<b>yours to decide</b>")
                   for n, where, what, kind in PROPOSALS)
    gaps = "".join("<li>%s</li>" % g for g in GAPS)
    return """<div class="mk-legend">
<b>Match page, state 1: the next matchday (#132).</b> Borussia Dortmund vs SV Werder Bremen, 9 Oct 2026,
Bundesliga matchday 5, as the site builds it from the 2026-09-25 export. <b>Built today</b> is that page
unchanged. <b>Proposed</b> draws every block with the site's shared elements (the block standard): the
Matchdays tab's breadcrumb, THE match row, the fact row, the board. The header, the sentence and the form
comparison already follow them and do not change. <b>Data sources</b> shows where each block's numbers
come from.
<table><tr><th></th><th>Where</th><th>Proposed</th><th></th></tr>%s</table>
<b>Gaps the proposal names instead of inventing:</b><ul>%s</ul>
<b>Also fixed in the build, not visible on this match:</b> the standing chip renders empty when a team has
no table position (128 of 628 sample matches), and is hidden instead; "clubs" reads "teams" on a
national-team match; the German and Finnish pages translate the Defending row's sub-label.
<br><br><b>Not proposed here:</b> times stay UTC until #146. A played match's page and a page for every
player shown do not exist yet: the rows link to where those pages will be.
</div>""" % (rows, gaps)


def build():
    page = inline_css(PAGE.read_text(encoding="utf-8"))
    head = page[:page.index("<body")]
    start = page.index('<div class="inner">')
    end = page.index("<footer")
    comps = json.loads((DATA / "competitions.json").read_text(encoding="utf-8"))
    css = HARNESS_CSS + ADAPT_CSS + CUR_CSS % {"on": "#mk-prop:checked ~ .mk-page "}
    clean_in = clean_label = ""
    if STATE == "next" or STATE.startswith("played"):
        css += FORM_CSS + CLEAN_CSS
        clean_in = '<input class="mk-in" type="checkbox" id="mk-clean" checked>\n'
        clean_label = '  <label for="mk-clean"><span class="mk-box"></span>Clean page</label>\n'
    if STATE.startswith("played"):
        fx = PLAYED if STATE == "played" else PLAYED_PEN
        inner = '<div class="inner">%s</div>' % played_page(fx, comps, team_slugs())
        per_side = max(sum(p[0] == t["team_id"] for p in fx["players"]) for t in (fx["home"], fx["away"]))
        if "lineups" in fx:
            per_side = 1 + max(len(line["xi"]) + len(line["subs"]) for line in fx["lineups"].values())
        css += PLAYED_CSS % {"rows": per_side + 1}
        d = date.fromisoformat(fx["kickoff"][:10])
        head = re.sub(r"<title>[^<]*</title>", "<title>%s vs %s, %d %s</title>"
                      % (E(fx["home"]["name"]), E(fx["away"]["name"]), d.day, MONTHS[d.month - 1]), head, count=1)
        foot = legend_played(fx, comps)
    else:
        fx = json.loads((DATA / "fixtures" / ("%d.json" % FIXTURE_ID)).read_text(encoding="utf-8"))
        inner = add_sources(propose(page[start:end], fx, comps, team_slugs()), page_sources(fx, comps))
        foot = legend(fx)
    # The site's own header, live, so the page adapts as the window is resized; the section mark
    # is a proposal and shows under "Proposed" only.
    site_header = mark_section(page[page.index(">", page.index("<body")) + 1:start])
    head = head.replace("</head>", "<style>%s</style></head>" % css)
    return """%s<body class="fx" data-theme="dark">
<input class="mk-in" type="radio" name="mk-v" id="mk-built">
<input class="mk-in" type="radio" name="mk-v" id="mk-prop" checked>
<input class="mk-in" type="checkbox" id="mk-src">
<input class="mk-in" type="checkbox" id="mk-links">
%s<div class="mk-ctl">
  <label for="mk-built"><span class="mk-box"></span>Built today</label>
  <label for="mk-prop"><span class="mk-box"></span>Proposed</label>
  <label for="mk-src"><span class="mk-box"></span>Data sources</label>
  <label for="mk-links"><span class="mk-box"></span>Link areas</label>
%s  <span class="mk-view"><span class="mk-v1">Phone view (under 700px)</span><span class="mk-v2">Tablet view (700&ndash;1009px)</span><span class="mk-v3">Desktop view (1010px and up)</span></span>
</div>
<div class="mk-page">%s%s</div>
%s
<script>%s</script>
</body></html>
""" % (head, clean_in, clean_label, site_header, inner, foot, TRAIL_JS)


if __name__ == "__main__":
    out = HERE / (sys.argv[1] if len(sys.argv) > 1 else "match-page.html")
    out.write_text(build(), encoding="utf-8")
    print("wrote", out, "%.0f KB" % (out.stat().st_size / 1024))
