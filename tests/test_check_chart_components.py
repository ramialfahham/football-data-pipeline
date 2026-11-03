"""The chart-component check: green on the tree, red on each look a chart component may not set."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_chart_components as ccc  # noqa: E402

CHART = '---\nconst x = 1;\n---\n<div class="chart">%s</div>\n'


def _site(tmp_path: Path, body: str, name: str = "Chart.astro") -> Path:
    src = tmp_path / "site_v2" / "src"
    (src / "components").mkdir(parents=True)
    (src / "lib").mkdir()
    (src / "lib" / "chartTheme.ts").write_text("export const scatter = { width: 560, gap: \"0.6em\" };\n", encoding="utf-8")
    (src / "components" / name).write_text(body, encoding="utf-8")
    return src


def _run(src: Path, root: Path):
    return ccc.run(src, src / "lib" / "chartTheme.ts", root)


def test_the_tree_is_clean_and_finds_every_chart_component():
    findings, components = ccc.run()
    assert findings == []
    assert components == [
        "site_v2/src/components/fixture/MetricComparison.astro",
        "site_v2/src/components/fixture/MetricRow.astro",
        "site_v2/src/components/team/TeamDeserved.astro",
        "site_v2/src/components/team/TeamLeagueStrips.astro",
        "site_v2/src/components/ui/ChartLegend.astro",
    ]


def test_a_theme_class_and_a_data_position_pass(tmp_path):
    src = _site(tmp_path, CHART % '<span style={`left:${p}%`}><i class="chart-dot"></i></span><text x={c.x} dy="0.6em">a</text>')
    assert _run(src, tmp_path) == ([], ["site_v2/src/components/Chart.astro"])


def test_a_look_attribute_fails(tmp_path):
    for attr in ('font-size="12"', 'fill="#fff"', 'r="3"', "stroke-width={2}", 'width="22"'):
        src = _site(tmp_path / attr.split("=")[0], CHART % ("<circle %s></circle>" % attr))
        findings, _ = _run(src, tmp_path / attr.split("=")[0])
        assert len(findings) == 1 and attr.split("=")[0] in findings[0], attr


def test_a_style_other_than_a_data_position_fails(tmp_path):
    for style in ('style="left:5px"', 'style={`color:${c}`}', 'style={`left:${p}px`}'):
        src = _site(tmp_path / str(abs(hash(style))), CHART % ("<span %s></span>" % style))
        findings, _ = _run(src, tmp_path / str(abs(hash(style))))
        assert len(findings) == 1 and "style=" in findings[0], style


def test_a_style_block_fails(tmp_path):
    src = _site(tmp_path, CHART % "" + "<style>.chart { color: red; }</style>\n")
    findings, _ = _run(src, tmp_path)
    assert any("style block" in f for f in findings)


def test_a_component_without_a_theme_class_is_not_a_chart(tmp_path):
    src = _site(tmp_path, '<div class="lrow"><svg width="22" height="8"></svg></div>\n')
    assert _run(src, tmp_path) == ([], [])


def test_a_tooltip_fails_anywhere_on_the_site(tmp_path):
    cases = {
        "attr": '<div class="lrow"><span title="Team: 3">x</span></div>\n',
        "svg": '<svg viewBox="0 0 10 10"><circle cx="1" cy="1"><title>Team</title></circle></svg>\n',
        "script": '<div class="lrow"></div>\n<script>document.querySelector("i").setAttribute("title", "x");</script>\n',
    }
    for name, body in cases.items():
        src = _site(tmp_path / name, body, "Row.astro")
        findings, _ = _run(src, tmp_path / name)
        assert len(findings) == 1 and "tooltip" in findings[0], (name, findings)


def test_the_page_title_and_a_component_title_prop_pass(tmp_path):
    body = ('---\n// the page\'s <title> comes from the strings\n---\n'
            '<html><head><title>{title}</title></head><body><Layout title={title} /><!-- <title> --></body></html>\n')
    src = _site(tmp_path, body, "Page.astro")
    assert _run(src, tmp_path) == ([], [])


def test_a_colour_or_a_pixel_size_in_the_layout_file_fails(tmp_path):
    src = _site(tmp_path, CHART % "")
    theme = src / "lib" / "chartTheme.ts"
    for look in ('dot: "6px"', 'axis: "#8b9099"', 'line: "var(--ink)"'):
        theme.write_text("export const t = { %s };\n" % look, encoding="utf-8")
        findings, _ = _run(src, tmp_path)
        assert len(findings) == 1 and "layout file" in findings[0], look
