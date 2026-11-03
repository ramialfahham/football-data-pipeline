"""The chart screenshot check: pins compared by hash, pins written on Linux only, every chart mark's
computed colour held to the theme, and the scatter plot's difference label placed in a reader's flow,
each red on the defect it guards against."""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_chart_screenshots as ccs  # noqa: E402

DIST = ccs.DIST


def _chromium_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            pw.chromium.launch().close()
        return True
    except Exception:
        return False


needs_site = pytest.mark.skipif(not (DIST / "en").is_dir() or not _chromium_available(),
                                reason="needs the built site and Playwright's Chromium")


def test_compare_names_every_changed_new_and_gone_pin():
    pinned = {"platform": "linux", "shots": {"a.png": "1", "b.png": "2", "c.png": "3"}}
    now = {"platform": "linux", "shots": {"a.png": "1", "b.png": "9", "d.png": "4"}}
    assert ccs.compare(pinned, now) == ["b.png · changed", "d.png · new", "c.png · gone"]
    assert ccs.compare(pinned, pinned) == []


def test_the_manifest_holds_the_platform_and_each_hash():
    m = ccs.manifest_of({"b.png": b"x", "a.png": b"y"}, "linux")
    assert m["platform"] == "linux" and list(m["shots"]) == ["a.png", "b.png"]
    assert len(m["shots"]["a.png"]) == 64


def _ci():
    yaml = pytest.importorskip("yaml")
    return yaml.safe_load((ccs.REPO / ".gitlab-ci.yml").read_text(encoding="utf-8"))


def test_validate_ui_runs_both_chart_checks_and_their_tests_after_the_design_check():
    job = _ci()["validate:ui"]
    script = " ".join(job["script"])
    steps = ["scripts/check_chart_components.py", "scripts/check_chart_screenshots.py --dist site_v2/dist",
             "tests/test_check_chart_components.py tests/test_check_chart_screenshots.py"]
    for step in steps:
        assert step in script, step
    assert script.index("tests/test_design_inventory.py") < script.index(steps[0])
    folder = script.split("check_chart_screenshots.py", 1)[1].split("--artifacts", 1)[1].split()[0]
    assert folder in job["artifacts"]["paths"]


def test_the_ui_paths_trigger_validate_ui_on_the_chart_checks_and_their_pins():
    paths = _ci()[".ui_paths"]
    for p in ("scripts/check_chart_components.py", "scripts/check_chart_screenshots.py",
              "tests/test_check_chart_components.py", "tests/test_check_chart_screenshots.py",
              "tests/fixtures/chart_screenshots/*"):
        assert p in paths, p


def _measured(monkeypatch, shots, labels=(), measured=1224):
    monkeypatch.setattr(ccs, "measure", lambda dist: ([], shots, [], list(labels), measured))


def _pin(folder: Path, shots: dict, platform: str = "linux") -> None:
    ccs.write(folder, shots, ccs.manifest_of(shots, platform))


def test_a_changed_chart_fails_on_linux_and_writes_the_new_screenshots(tmp_path, monkeypatch):
    pins, out = tmp_path / "pins", tmp_path / "out"
    _pin(pins, {"scatter-en-dark-375.png": b"old"})
    _measured(monkeypatch, {"scatter-en-dark-375.png": b"new"})
    monkeypatch.setattr(ccs, "PLATFORM", "linux")
    assert ccs.main(["--pins", str(pins), "--artifacts", str(out)]) == 1
    assert (out / "scatter-en-dark-375.png").read_bytes() == b"new"
    assert '"platform": "linux"' in (out / "manifest.json").read_text(encoding="utf-8")


def test_unchanged_charts_pass_on_linux(tmp_path, monkeypatch):
    _pin(tmp_path, {"a.png": b"same"})
    _measured(monkeypatch, {"a.png": b"same"})
    monkeypatch.setattr(ccs, "PLATFORM", "linux")
    assert ccs.main(["--pins", str(tmp_path)]) == 0


def test_missing_pins_fail_on_linux(tmp_path, monkeypatch):
    _measured(monkeypatch, {"a.png": b"x"})
    monkeypatch.setattr(ccs, "PLATFORM", "linux")
    assert ccs.main(["--pins", str(tmp_path)]) == 1


@pytest.mark.parametrize("running", ["linux", "win32", "darwin"])
def test_pins_from_another_platform_fail_everywhere(tmp_path, monkeypatch, running):
    _pin(tmp_path, {"a.png": b"same"}, platform="win32")
    _measured(monkeypatch, {"a.png": b"same"})
    monkeypatch.setattr(ccs, "PLATFORM", running)
    assert ccs.main(["--pins", str(tmp_path)]) == 1


def test_off_linux_the_screenshots_are_not_compared_and_no_artifact_is_written(tmp_path, monkeypatch):
    pins, out = tmp_path / "pins", tmp_path / "out"
    _pin(pins, {"a.png": b"old"})
    _measured(monkeypatch, {"a.png": b"new"})
    monkeypatch.setattr(ccs, "PLATFORM", "win32")
    assert ccs.main(["--pins", str(pins), "--artifacts", str(out)]) == 0
    assert not out.exists()


@pytest.mark.parametrize("running", ["linux", "win32"])
def test_a_manifest_whose_images_differ_from_its_hashes_fails(tmp_path, monkeypatch, running):
    _pin(tmp_path, {"a.png": b"old"})
    (tmp_path / "a.png").write_bytes(b"stale image beside a new hash")
    _measured(monkeypatch, {"a.png": b"old"})
    monkeypatch.setattr(ccs, "PLATFORM", running)
    assert ccs.main(["--pins", str(tmp_path)]) == 1


@pytest.mark.parametrize("running", ["linux", "win32"])
def test_a_pinned_image_missing_or_unnamed_fails(tmp_path, monkeypatch, running):
    _pin(tmp_path, {"a.png": b"x", "b.png": b"y"})
    (tmp_path / "b.png").unlink()
    (tmp_path / "c.png").write_bytes(b"z")
    _measured(monkeypatch, {"a.png": b"x", "b.png": b"y"})
    monkeypatch.setattr(ccs, "PLATFORM", running)
    assert ccs.main(["--pins", str(tmp_path)]) == 1
    assert ccs.pin_findings(tmp_path, ccs.manifest_of({"a.png": b"x", "b.png": b"y"}, "linux")) == [
        "b.png · in the manifest, not in the pins", "c.png · in the pins, not in the manifest"]


def test_writing_the_pins_removes_an_image_no_longer_taken(tmp_path):
    _pin(tmp_path, {"a.png": b"x", "gone.png": b"y"})
    ccs.write(tmp_path, {"a.png": b"x"}, ccs.manifest_of({"a.png": b"x"}, "linux"))
    assert sorted(p.name for p in tmp_path.glob("*.png")) == ["a.png"]


def test_a_run_that_measures_no_scatter_plot_fails(tmp_path, monkeypatch):
    _pin(tmp_path, {"a.png": b"same"})
    _measured(monkeypatch, {"a.png": b"same"}, measured=0)
    monkeypatch.setattr(ccs, "PLATFORM", "linux")
    assert ccs.main(["--pins", str(tmp_path)]) == 1


@pytest.mark.parametrize("running", ["win32", "darwin"])
def test_pins_are_never_written_off_linux(tmp_path, monkeypatch, running):
    monkeypatch.setattr(ccs, "PLATFORM", running)
    assert ccs.main(["--update", "--pins", str(tmp_path)]) == 2
    assert not any(tmp_path.iterdir())


def _on_built_site(run, html=None, css=None, init=None):
    """Run `run(page, base)` on the served built site; `html` and `css` rewrite every page and
    stylesheet on the way in, `init` runs before the page's own scripts."""
    from playwright.sync_api import sync_playwright

    srv, base = ccs.serve(DIST)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1010, "height": 812})
            if init:
                page.add_init_script(init)
            def served(url: str) -> str:
                path = DIST / url.split("://", 1)[1].split("/", 1)[1].split("?")[0]
                return (path / "index.html" if path.is_dir() else path).read_text(encoding="utf-8")

            for pattern, edit, kind in (("**/*/", html, "text/html"), ("**/_astro/*.css", css, "text/css")):
                if edit:
                    page.route(pattern, lambda route, _request=None, edit=edit, kind=kind: route.fulfill(
                        body=edit(served(route.request.url)), content_type=kind))
            found = run(page, base)
            browser.close()
    finally:
        srv.shutdown()
    return found


def _reader(path, width):
    def run(page, base):
        page.set_viewport_size({"width": width, "height": 812})
        page.goto(base + path, wait_until="domcontentloaded")
        return page.evaluate(ccs.READER_JS)
    return run


@needs_site
def test_every_scatter_page_is_found_by_its_markup():
    pages = ccs.scatter_pages(DIST)
    assert "en/teams/1-fc-koln" in pages and "fi/joukkueet/1-fc-koln" in pages and len(pages) % 3 == 0


@needs_site
def test_every_mark_on_the_built_pages_has_its_theme_colour():
    assert _on_built_site(ccs.colour_findings) == []


@needs_site
def test_a_better_colour_rule_another_rule_outranks_fails():
    found = _on_built_site(ccs.colour_findings, css=lambda s: s.replace(".cmp-val.chart-better{", ":where(.cmp-val.chart-better){"))
    assert any(".cmp-val.chart-better · color" in f for f in found), found


@needs_site
def test_a_renamed_mark_class_fails_for_matching_nothing():
    found = _on_built_site(ccs.colour_findings, html=lambda h: re.sub(r'<span class="chart-better"><span style=',
                                                                         '<span class="better"><span style=', h))
    assert any(".chart-bar > .chart-better > span · matches nothing" in f for f in found), found


@needs_site
def test_a_reader_clicking_the_tab_sees_a_placed_difference_label():
    assert _on_built_site(_reader("en/teams/1-fc-koln/", 375)) == []


@needs_site
def test_a_chart_script_that_waits_for_a_rendered_frame_fails_the_reader_flow():
    blocked = """(() => { const add = EventTarget.prototype.addEventListener;
      EventTarget.prototype.addEventListener = function (type, fn, opts) { if (type !== 'change') add.call(this, type, fn, opts); }; })()"""
    found = _on_built_site(_reader("en/teams/1-fc-koln/", 375), init=blocked)
    assert "the deserved points line" in found, found
