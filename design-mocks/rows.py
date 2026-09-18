"""THE match row — one implementation, imported by every mock that shows a match.

The direction: *"make sure that displaying of next matches is consistent on every page"*. It
was not. Four treatments were in the tree or in these mocks:

    .fxrow    home hero (`home/HeroFixtures.astro`)        upcoming
    .nextfx   team page (`team/TeamFixtures.astro`)        upcoming, a single highlighted card
    .rmatch   fixture page, team page, H2H                 played, written from ONE team's view
    .fxrow.res  the competition-hub and matches mocks      played, neutral — a fourth, mine

So this module exists rather than a written rule: consistency by CONSTRUCTION. Both generators
import these functions, and `check_row_consistency.py` proves the two rendered mocks emit
identical row markup. In the real site this is one Astro component, not two call sites.

**The rule it encodes.** One row, `.fxrow`:
  * both sides stacked — crest/flag + name
  * the right column carries the KICKOFF when upcoming and a REPORT affordance when played
  * the score sits inline at the end of each side, so home/away needs no extra label
  * `.nextfx` retires — a next match is simply the first row, not a special card

The one legitimate variant, not built here: on a TEAM page the row also carries a W/D/L chip,
because that page has a subject and "we won" is meaningful. Everywhere else there is no "we",
so the row stays neutral.

**Linked or inert.** A row is an anchor only when its target exists. Upcoming rows link today.
Played rows do NOT — a played match has no page at all (#861) — so `result_row(linked=False)`
is the honest state now, and `linked=True` is what the same component emits the day match
reports land. Same markup either way; only the tag changes.
"""
import html

from interaction import CHEVRON

E = html.escape

# ⚠ Both badges below are HOTLINKED in production from media.api-sports.io (#36 — a go-live
# blocker with an open licence question). The league logo inherits that problem exactly. The
# mocks draw neutral placeholders: they must not hotlink, and the design system's text-initials
# fallback reads as if the abbreviation were the design.

CREST = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M12 3.2l6.6 2.35v5.65c0 3.95-2.73 7.15-6.6 8.95'
    '-3.87-1.8-6.6-5-6.6-8.95V5.55L12 3.2z"'
    ' fill="none" stroke="currentColor" stroke-width="1.6" opacity=".42"/></svg>'
)

# a NATIONAL side is a flag, not a crest — `dim_league` already carries `country_flag_url`, so
# this is a different asset, not the same one restyled
FLAG = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<rect x="3" y="6" width="18" height="12" rx="1.5" fill="none" stroke="currentColor"'
    ' stroke-width="1.6" opacity=".42"/>'
    '<path d="M3 10h18M3 14h18" stroke="currentColor" stroke-width="1.2" opacity=".3"/></svg>'
)

# the league logo — `dim_league.league_logo_url`. A CIRCLE where a club crest is a SHIELD, so a
# group head cannot be misread as a row.
LEAGUE_LOGO = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.6"'
    ' opacity=".45"/>'
    '<circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" stroke-width="1.3"'
    ' opacity=".3"/></svg>'
)


def badge(kind):
    return FLAG if kind == "nation" else CREST


def _sides(kind, home, away, hg=None, ag=None):
    def side(name, goals, won):
        g = ""
        if goals is not None:
            # ⚠ `winner`, NOT `win`. `system.css:93` defines `.win { display: none }` — the
            # segment control's hidden-panel class — so marking the winning side `win` made the
            # WINNER'S SCORE INVISIBLE. Second collision found by the same check, minutes after
            # the first (`res`, which was 24px wide).
            g = '<b class="g%s num">%d</b>' % (" winner" if won else "", goals)
        return ('<span class="side"><span class="crest xs">%s</span>'
                '<span class="nm">%s</span>%s</span>' % (badge(kind), E(name), g))
    if hg is None:
        return '<span class="sides">%s%s</span>' % (side(home, None, False), side(away, None, False))
    return '<span class="sides">%s%s</span>' % (side(home, hg, hg > ag), side(away, ag, ag > hg))


def upcoming_row(kind, home, away, time, zone, href="#"):
    """An upcoming match. The right column is the kickoff in VENUE-LOCAL time, and `zone` is
    REQUIRED — every row, every page, no exception.

    ⚠ AN EARLIER VERSION MADE IT CONDITIONAL and it was rejected on sight. The zone sat on the
    GROUP head where a competition has one country, and moved onto the ROW only where a
    competition spans zones (MLS: four US zones; any national-team competition: played in
    whichever nation is at home). Both variants then appeared on one screen, a group-level "CET"
    above one block and per-row "CET"/"EET" in the next.

    The rule: *"this is a repetitive content block ... it has to be consistent everywhere
    we show this type of content block"*. **A reusable block must not change shape according to
    its context.** So the zone is part of the time, always — repeating "CET" down a Bundesliga
    list is the price, and it is the right price.

    Dropping the zone entirely is NOT the alternative: Germany 20:45 CET and Finland 21:45 EET
    are the same moment, and rendering them bare reads as an hour apart.

    ⚠ NO DATE ON THE ROW — it is a `date_head` above the rows it applies to. Putting it in the
    right-hand column repeated one value down a whole round and made the schedule hard to read."""
    return ('<a class="fxrow" href="%s">%s'
            '<span class="when"><b class="t">%s</b><span class="rowtz">%s</span></span></a>'
            % (href, _sides(kind, home, away), E(time), E(zone)))


def result_row(kind, home, hg, away, ag, href="#"):
    """A played match. THE SAME ROW as `upcoming_row` (*"let's keep the design consistent
    with the next matches block design"*) — same sides, same badges. The score goes
    inline at the end of each side, so home and away need no extra label, and the kick-off column
    is dropped: a finished match's start time is not information.

    The winner is shown by TONE + WEIGHT, never by hue — green stays reserved for "better value"
    and red for a Loss pill, so a draw leaves both sides muted, which is the honest reading.

    ⚠ ALWAYS A LINK. An earlier version rendered played rows inert because the match report page
    does not exist (#861). The rule: *"we are creating the pages one by one. there will always
    be some page that's not wired ... until we have created all of them"* — so an unbuilt target
    no longer blocks the design. Nothing is exposed meanwhile: the site is unpublished and every
    page is noindex.

    ⚠ A "Report" / "No report yet" chip lived in the right column and is GONE. It was a second
    thing in the slot that carries the kick-off on every other surface — the block's own
    never-move rule."""
    # ⚠ THE MODIFIER IS `played`, NOT `res`. `.res` is ALREADY TAKEN by system.css:155 — it is the
    # W/D/L result chip of the `.rmatch` row, and it carries `width: 24px; height: 24px`. Naming
    # the played-row modifier `res` made every played row 24 PIXELS WIDE, which collapsed the name
    # to nothing and overlapped the rows. Four rounds of layout "fixes" chased that and none could
    # have worked, because none of them touched the cause. A block's modifier must not reuse a
    # class the design system already defines; `check_row_consistency.py` now enforces that.
    # ⚠ NO KICK-OFF ON A PLAYED ROW. Once a match is finished the time it started
    # tells a reader nothing — the score is the whole content — so the right-hand column is
    # dropped rather than filled with something less useful. This is the standard's OMIT rule, not
    # a move: the slot is absent, and nothing else takes it over.
    return ('<a class="fxrow played" href="%s">%s</a>'
            % (href, _sides(kind, home, away, hg, ag)))


def date_head(label):
    """A DATE inside a competition group. The second and last level of grouping.

    ⚠ This replaced the date-on-every-row version, which could not be scanned: *"now it's hard
    to see when the games are"*. A round runs Friday to Sunday, so the date repeated down the
    right-hand column as a value when it is really a heading. As a divider it is read once and
    the rows underneath carry only a kick-off.

    It also keeps ONE grouping order on every surface — competition, then date. The version
    before this grouped the Matches page by DAY and then competition, and the competition page by
    matchday, which is two different blocks."""
    return '<div class="dh">%s</div>' % E(label)


def group_head(slug, name):
    """THE GROUP: one competition. League logo + competition name. Nothing else.

    ⚠ NO MATCHDAY (*"leave out the match day — you can see that on the details page
    anyway"*). It also could not be shown honestly: the warehouse stores the provider's raw
    `"Regular Season - 25"`, which shipped untranslated to all three locales once already (#866),
    and turning it into a phase plus a number is taxonomy mapping the consumption layer forbids.

    ⚠ THE COMPETITION MUST BE UNMISSABLE — *"you scroll down and barely notice that the
    competition has changed"*. Hence the larger name, the wider space above the group and the
    heavier rule in the stylesheet, rather than the 14px label this started as.

    The competition name is the link that makes a match list a HUB rather than a list: every
    group head is an outbound edge to a competition, every row one to a match.

    ⚠ NOT CALLED AT ALL ON A COMPETITION'S OWN PAGE. A `here=True` variant rendered the name as
    plain text there, which put "Bundesliga" directly under the `<h1>Bundesliga</h1>` — the page
    already IS level 1.

    THE RULE THIS SETTLES: **a block may OMIT a level the page itself supplies; it may never
    MOVE information from one slot to another.** Dropping the competition level on the
    competition's page is omission. Putting the timezone on a group head for some competitions
    and on the row for others was relocation, and that is what was rejected.

    ⚠ NO TIMEZONE HERE, for the same reason. The zone lives on the row — see `upcoming_row`."""
    # ⚠ THE CHEVRON IS THE AFFORDANCE, and it is present AT REST. The heading used to announce
    # itself as a link only by underlining on hover — which a phone never shows, so on touch the
    # link was invisible. See `interaction.py`.
    return ('<div class="gh"><a class="cnm" href="/en/%s/">'
            '<span class="clogo">%s</span><span class="nm">%s</span>%s</a></div>'
            % (E(slug), LEAGUE_LOGO, E(name), CHEVRON))

