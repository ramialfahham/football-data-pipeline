import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import merge_ready as mr  # noqa: E402

TESTED = "a" * 40
CURRENT = "b" * 40


def test_tested_sha_read_from_job_trace():
    trace = f"noise\n2026-11-16T08:42:55.741620Z 01O Merged result {'c' * 40}: branch {'d' * 40} + main {TESTED}\nmore"
    assert mr.tested_target_sha(trace) == TESTED


def test_tested_sha_absent_when_no_merged_result_line():
    assert mr.tested_target_sha("Merged result abc") is None


def test_model_names_take_models_and_seeds_only():
    files = [
        "dbt_project/models/3_core/dim_team.sql",
        "dbt_project/seeds/fixture_card_corrections.csv",
        "dbt_project/models/3_core/schema.yml",
        "scripts/merge_ready.py",
    ]
    assert mr.model_names(files) == ["dim_team", "fixture_card_corrections"]


def test_lineage_paths_prefix_and_drop_dbt_banner_lines():
    out = "Running with dbt=1.7.19\nmodels/3_core/dim_team.sql\nseeds/x.csv\n"
    assert mr.lineage_paths(out) == {"dbt_project/models/3_core/dim_team.sql", "dbt_project/seeds/x.csv"}


def test_no_overlap_when_moved_files_are_unrelated():
    assert mr.overlaps({"scripts/a.py"}, {"dbt_project/models/x.sql"}, {"docs/y.md"}, True) == []


def test_overlap_on_file_changed_by_both():
    hits = mr.overlaps({"docs/a.md"}, set(), {"docs/a.md"}, True)
    assert len(hits) == 1 and "also changed" in hits[0]


def test_overlap_on_dbt_lineage():
    hits = mr.overlaps({"dbt_project/models/a.sql"}, {"dbt_project/models/b.sql"},
                       {"dbt_project/models/b.sql"}, True)
    assert len(hits) == 1 and "lineage" in hits[0]


def test_ci_definition_move_overlaps_every_mr():
    assert mr.overlaps({"docs/a.md"}, set(), {".gitlab-ci.yml"}, True)


def test_unreadable_lineage_counts_any_dbt_file_as_overlap():
    moved = {"dbt_project/models/z.sql"}
    assert mr.overlaps({"dbt_project/models/a.sql"}, set(), moved, False)
    assert not mr.overlaps({"dbt_project/models/a.sql"}, set(), moved, True)


def test_macro_move_overlaps_an_mr_with_dbt_files():
    assert mr.overlaps({"dbt_project/models/a.sql"}, set(), {"dbt_project/macros/m.sql"}, True)
    assert not mr.overlaps({"docs/a.md"}, set(), {"dbt_project/macros/m.sql"}, True)


@pytest.fixture()
def fake(monkeypatch):
    calls = {"glab": {}, "git": {}}
    monkeypatch.setattr(mr, "glab_json", lambda p: calls["glab"][p.split("?")[0]] if p.split("?")[0] in calls["glab"]
                        else (_ for _ in ()).throw(AssertionError(p)))
    monkeypatch.setattr(mr, "tested_sha_of", lambda m: TESTED)
    monkeypatch.setattr(mr, "blockers", lambda *a: [])

    def fake_run(cmd, cwd=None, check=True):
        key = " ".join(cmd[:3])
        for k, v in calls["git"].items():
            if key.startswith(k):
                return v
        return ""

    monkeypatch.setattr(mr, "run", fake_run)
    return calls


def _mr(state="opened"):
    return {"iid": 7, "state": state, "target_branch": "main", "sha": "e" * 40,
            "head_pipeline": {"id": 1, "status": "success"}}


def test_decide_ready_when_main_did_not_move(fake):
    fake["glab"]["projects/:id/merge_requests/7"] = _mr()
    fake["git"]["git rev-parse --show-toplevel"] = "/x\n"
    fake["git"]["git rev-parse gitlab/main"] = TESTED + "\n"
    code, lines = mr.decide("7")
    assert code == 0 and "has not moved" in lines[0]


def test_decide_refuses_a_closed_mr(fake):
    fake["glab"]["projects/:id/merge_requests/7"] = _mr("merged")
    with pytest.raises(mr.Undecided):
        mr.decide("7")


def test_decide_names_the_blocker_before_anything_else(fake, monkeypatch):
    fake["glab"]["projects/:id/merge_requests/7"] = _mr()
    fake["git"]["git rev-parse --show-toplevel"] = "/x\n"
    fake["git"]["git rev-parse gitlab/main"] = CURRENT + "\n"
    monkeypatch.setattr(mr, "blockers", lambda *a: ["open MR !5 also changes the shared file x"])
    code, lines = mr.decide("7")
    assert code == 1 and lines[0] == "BLOCKED" and "!5" in lines[1]


def test_main_requires_an_iid(capsys):
    assert mr.main(["merge_ready.py"]) == 2
    assert mr.main(["merge_ready.py", "abc"]) == 2


# --- the full design sweep of an MR that changes the rendered site ---
WIDTHS = "280,320,360,375,700,1010"
FULL = [280, 320, 360, 375, 700, 1010]
STAMP = "2026-11-17T10:00:00.000000Z 01O "


def _gap(widths, off, note=""):
    return f"{STAMP}gap counts: 14334 pages counted at {widths} px · {note}{off} off the baseline\n"


def _off(line):
    return f"{STAMP}FAIL  (counts) · 0 · - · (baseline) · {line}\n"


def test_the_full_widths_are_the_baselines():
    assert mr.full_widths() == FULL


@pytest.mark.parametrize("files, full", [
    (["site_v2/src/pages/index.astro"], True),
    (["docs/design/components.yml"], True),
    (["site_v2/scripts/check-font-coverage.mjs", "scripts/merge_ready.py"], False),
    ([], False),
])
def test_needs_full_sweep_reads_validate_ui_rule(files, full):
    assert mr.needs_full_sweep(files) is full


def test_a_quick_sweep_is_not_the_full_one():
    trace = _gap("280,1010", 0) + _gap("320", 0)
    assert mr.sweep_findings(trace, FULL) == (False, [])


def test_a_sweep_whose_counts_were_not_compared_is_not_the_full_one():
    assert mr.sweep_findings(_gap(WIDTHS, 0, "rendered counts not compared: x · "), FULL) == (False, [])


def test_a_full_sweep_on_its_pins():
    assert mr.sweep_findings(_gap(WIDTHS, 0), FULL) == (True, [])


def test_a_full_sweep_names_each_count_off_its_pin():
    rose = "count rose · Match page · scroll · 2180, baseline 2175"
    fell = "count fell · Team page · overflow · 0, baseline 3: lower the baseline"
    ran, off = mr.sweep_findings(_off(rose) + _off(fell) + _gap(WIDTHS, 2), FULL)
    assert ran and off == [rose, fell]


@pytest.fixture()
def ui_job(monkeypatch):
    state = {"jobs": [{"id": 5, "name": "validate:ui", "status": "success"}], "trace": _gap(WIDTHS, 0)}
    monkeypatch.setattr(mr, "glab_json", lambda p: state["jobs"])
    monkeypatch.setattr(mr, "run", lambda cmd, cwd=None, check=True: state["trace"])
    return state


SITE = ["site_v2/src/pages/index.astro"]


def test_sweep_refusal_ignores_an_mr_off_the_rendered_site(ui_job):
    ui_job["trace"] = _gap("280,1010", 3)
    assert mr.sweep_refusal(_mr(), ["scripts/x.py"]) == []


def test_sweep_refusal_passes_a_full_sweep_on_its_pins(ui_job):
    assert mr.sweep_refusal(_mr(), SITE) == []


def test_sweep_refusal_refuses_counts_off_the_baseline(ui_job):
    ui_job["jobs"][0]["status"] = "failed"
    ui_job["trace"] = _off("count fell · Team page · overflow · 0, baseline 3: lower the baseline") + _gap(WIDTHS, 1)
    lines = mr.sweep_refusal(_mr(), SITE)
    assert lines[0].startswith("NOT READY") and "Team page" in lines[1]


def test_sweep_refusal_refuses_a_pipeline_that_swept_only_the_quick_scope(ui_job):
    ui_job["trace"] = _gap("280,1010", 0) + _gap("320", 0)
    assert mr.sweep_refusal(_mr(), SITE)[0].startswith("NOT READY")


def test_sweep_refusal_refuses_a_pipeline_without_validate_ui(ui_job):
    ui_job["jobs"] = [{"id": 6, "name": "test:python", "status": "success"}]
    assert mr.sweep_refusal(_mr(), SITE)[0].startswith("NOT READY")


def test_sweep_refusal_leaves_a_running_sweep_to_the_pipeline_check(ui_job):
    ui_job["jobs"][0]["status"] = "running"
    ui_job["trace"] = ""
    assert mr.sweep_refusal(_mr(), SITE) == []


def test_decide_refuses_a_site_mr_with_counts_off_before_reading_the_tested_commit(fake, monkeypatch):
    fake["glab"]["projects/:id/merge_requests/7"] = _mr()
    fake["glab"]["projects/:id/pipelines/1/jobs"] = [{"id": 5, "name": "validate:ui", "status": "failed"}]
    fake["git"]["git rev-parse --show-toplevel"] = "/x\n"
    fake["git"]["git diff --name-only"] = "site_v2/src/pages/index.astro\n"
    fake["git"]["glab api projects/:id/jobs/5/trace"] = (
        _off("count rose · Match page · scroll · 2180, baseline 2175") + _gap(WIDTHS, 1))
    monkeypatch.setattr(mr, "tested_sha_of", lambda m: (_ for _ in ()).throw(AssertionError("reached")))
    code, lines = mr.decide("7")
    assert code == 1 and lines[0].startswith("NOT READY") and "Match page" in lines[1]


# --- the parts that read the contract and GitLab ---
def _contract(depends="  - !449\n", shared="  - none: t\n"):
    return f"objective: >\n  t\ndepends_on:\n{depends}shared_files:\n{shared}done_when:\n  - t\n"


@pytest.fixture()
def gitlab(monkeypatch):
    state = {"opened": [{"iid": 449}, {"iid": 450}], "diffs": {}}

    def fake(path):
        if "state=opened" in path:
            return state["opened"] if "page=1" in path else []
        for iid, diffs in state["diffs"].items():
            if f"merge_requests/{iid}/diffs" in path:
                return diffs if "page=1" in path else []
        raise AssertionError(path)

    monkeypatch.setattr(mr, "glab_json", fake)
    return state


def test_blockers_names_another_mr_changing_a_shared_file(gitlab, monkeypatch):
    shared = "tests/fixtures/design_inventory/baseline.json"
    monkeypatch.setattr(mr, "own_contract", lambda files, ref, cwd=None: _contract(
        depends="  - none: t\n", shared=f"  - {shared}\n"))
    gitlab["diffs"] = {449: [{"new_path": shared}], 450: [{"new_path": "docs/x.md"}]}
    out = mr.blockers({"iid": 7}, "h", ["x"])
    assert len(out) == 1 and "!449" in out[0] and shared in out[0]


def test_blockers_ignores_the_mr_itself(gitlab, monkeypatch):
    shared = "tests/fixtures/design_inventory/baseline.json"
    monkeypatch.setattr(mr, "own_contract", lambda files, ref, cwd=None: _contract(
        depends="  - none: t\n", shared=f"  - {shared}\n"))
    gitlab["diffs"] = {449: [{"new_path": shared}], 450: [{"new_path": "docs/x.md"}]}
    assert mr.blockers({"iid": 449}, "h", ["x"]) == []


def test_blockers_empty_when_no_shared_file_is_listed(gitlab, monkeypatch):
    monkeypatch.setattr(mr, "own_contract", lambda files, ref, cwd=None: _contract())
    assert mr.blockers({"iid": 7}, "h", ["x"]) == []


def test_blockers_empty_without_a_contract(gitlab, monkeypatch):
    monkeypatch.setattr(mr, "own_contract", lambda files, ref, cwd=None: None)
    assert mr.blockers({"iid": 7}, "h", ["x"]) == []


def test_own_contract_is_the_one_in_the_task_folder(monkeypatch):
    seen = []
    monkeypatch.setattr(mr, "run", lambda cmd, cwd=None, check=True: seen.append(cmd) or "text")
    assert mr.own_contract(["other.py", ".claude/task/2-own/contract.md"], "HEAD") == "text"
    assert seen[-1] == ["git", "show", "HEAD:.claude/task/2-own/contract.md"]
    assert mr.own_contract(["other.py"], "HEAD") is None


def test_tested_sha_is_the_oldest_across_jobs(monkeypatch):
    t_old, t_new = "1" * 40, "2" * 40
    traces = {1: f"Merged result {'c' * 40}: branch {'d' * 40} + main {t_new}",
              2: f"Merged result {'c' * 40}: branch {'d' * 40} + main {t_old}"}
    monkeypatch.setattr(mr, "glab_json", lambda p: [{"id": 1, "status": "success"}, {"id": 2, "status": "success"},
                                                    {"id": 3, "status": "failed"}])
    monkeypatch.setattr(mr, "run", lambda cmd, cwd=None, check=True: traces[int(cmd[2].split("/")[3])]
                        if cmd[0] == "glab" else "")
    monkeypatch.setattr(mr, "commit_time", lambda ref, cwd: 1 if ref == t_old else 2)
    assert mr.tested_sha_of({"head_pipeline": {"id": 9, "status": "success"}}) == t_old


def test_tested_sha_refuses_a_red_pipeline():
    with pytest.raises(mr.Undecided):
        mr.tested_sha_of({"head_pipeline": {"id": 9, "status": "failed"}})


def test_changed_yaml_macro_or_singular_test_is_unmapped():
    files = ["dbt_project/models/a.sql", "dbt_project/models/schema.yml", "dbt_project/macros/m.sql",
             "dbt_project/tests/t.sql", "docs/x.md"]
    assert mr.unmapped_dbt_files(files) == [
        "dbt_project/models/schema.yml", "dbt_project/macros/m.sql", "dbt_project/tests/t.sql"]


def test_yaml_only_mr_counts_any_moved_dbt_file_as_overlap():
    assert mr.overlaps({"dbt_project/models/schema.yml"}, set(), {"dbt_project/models/mart_x.sql"}, False)


# --- decide() after main moved, on a real repository ---
def _git(cwd, *args):
    import subprocess
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture()
def moved(tmp_path, monkeypatch):
    remote, work = tmp_path / "remote.git", tmp_path / "work"
    _git(tmp_path, "init", "-q", "--bare", str(remote))
    _git(tmp_path, "clone", "-q", str(remote), str(work))
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        _git(work, "config", k, v)
    _git(work, "checkout", "-q", "-b", "main")
    (work / "a.txt").write_text("a\n")
    (work / "b.txt").write_text("b\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-qm", "base")
    tested = _git(work, "rev-parse", "HEAD")
    _git(work, "push", "-q", "origin", "main")
    _git(work, "checkout", "-q", "-b", "mrbranch")
    (work / "a.txt").write_text("a mr\n")
    _git(work, "commit", "-qam", "mr")
    head = _git(work, "rev-parse", "HEAD")
    _git(work, "push", "-q", "origin", "HEAD:refs/merge-requests/7/head")
    _git(work, "checkout", "-q", "main")
    monkeypatch.chdir(work)
    monkeypatch.setattr(mr, "REMOTE", "origin")
    monkeypatch.setattr(mr, "blockers", lambda *a: [])
    monkeypatch.setattr(mr, "tested_sha_of", lambda m: tested)
    monkeypatch.setattr(mr, "lineage_in", lambda *a: set())
    monkeypatch.setattr(mr, "glab_json", lambda p: {"iid": 7, "state": "opened", "target_branch": "main",
                                                    "sha": head, "head_pipeline": {}})

    def move(path, text):
        (work / path).write_text(text)
        _git(work, "add", "-A")
        _git(work, "commit", "-qm", "main moves")
        _git(work, "push", "-q", "origin", "main")

    return move


def test_decide_ready_when_main_moved_elsewhere(moved):
    moved("b.txt", "b2\n")
    code, lines = mr.decide("7")
    assert code == 0 and "nothing that moved touches" in lines[-1]


def test_decide_overlap_when_main_moved_the_same_file(moved):
    moved("a.txt", "a main\n")
    code, lines = mr.decide("7")
    assert code == 1 and any("a.txt" in x for x in lines)
