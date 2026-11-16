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
