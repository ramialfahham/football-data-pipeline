"""The one match row (`.fxrow`), imported by every mock generator that shows a match."""
import html

from interaction import CHEVRON

E = html.escape

# The mocks draw neutral placeholder badges instead of hotlinking the provider's images.

CREST = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M12 3.2l6.6 2.35v5.65c0 3.95-2.73 7.15-6.6 8.95'
    '-3.87-1.8-6.6-5-6.6-8.95V5.55L12 3.2z"'
    ' fill="none" stroke="currentColor" stroke-width="1.6" opacity=".42"/></svg>'
)

FLAG = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<rect x="3" y="6" width="18" height="12" rx="1.5" fill="none" stroke="currentColor"'
    ' stroke-width="1.6" opacity=".42"/>'
    '<path d="M3 10h18M3 14h18" stroke="currentColor" stroke-width="1.2" opacity=".3"/></svg>'
)

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
            # `win` is the design system's hidden-panel class, so the winner modifier is `winner`.
            g = '<b class="g%s num">%d</b>' % (" winner" if won else "", goals)
        return ('<span class="side"><span class="crest xs">%s</span>'
                '<span class="nm">%s</span>%s</span>' % (badge(kind), E(name), g))
    if hg is None:
        return '<span class="sides">%s%s</span>' % (side(home, None, False), side(away, None, False))
    return '<span class="sides">%s%s</span>' % (side(home, hg, hg > ag), side(away, ag, ag > hg))


def upcoming_row(kind, home, away, time, zone, href="#"):
    """Kickoff in venue-local time; `zone` is always shown so the block never changes shape."""
    return ('<a class="fxrow" href="%s">%s'
            '<span class="when"><b class="t">%s</b><span class="rowtz">%s</span></span></a>'
            % (href, _sides(kind, home, away), E(time), E(zone)))


def result_row(kind, home, hg, away, ag, href="#"):
    """A played match: the upcoming row with the score inline and no kickoff column."""
    # `res` is a design-system class, so the played modifier is `played`.
    return ('<a class="fxrow played" href="%s">%s</a>'
            % (href, _sides(kind, home, away, hg, ag)))


def date_head(label):
    """A date heading inside a competition group; every surface groups competition, then date."""
    return '<div class="dh">%s</div>' % E(label)


def group_head(slug, name):
    """A competition group head: league logo and name only; omitted on the competition's own page."""
    # The chevron is visible at rest because touch screens have no hover.
    return ('<div class="gh"><a class="cnm" href="/en/%s/">'
            '<span class="clogo">%s</span><span class="nm">%s</span>%s</a></div>'
            % (E(slug), LEAGUE_LOGO, E(name), CHEVRON))
