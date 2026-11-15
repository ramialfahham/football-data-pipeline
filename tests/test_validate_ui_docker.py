"""scripts/validate_ui_docker.py runs the validate:ui job of .gitlab-ci.yml and keeps no copy of it."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "validate_ui_docker.py"

spec = importlib.util.spec_from_file_location("validate_ui_docker", SCRIPT)
vud = importlib.util.module_from_spec(spec)
sys.modules["validate_ui_docker"] = vud
spec.loader.exec_module(vud)


def test_every_script_item_of_the_job_becomes_one_step_verbatim(tmp_path):
    job = vud.load_job()
    _before, script = vud.steps_of(job)
    files = vud.write_steps(job, tmp_path)
    assert len(files) == len(script) > 10
    for f, step in zip(files, script):
        assert f.read_text(encoding="utf-8") == step.rstrip("\n") + "\n"
    assert b"\r" not in (tmp_path / "runner.sh").read_bytes()


def test_before_script_is_the_jobs_own(tmp_path):
    job = vud.load_job()
    vud.write_steps(job, tmp_path)
    text = (tmp_path / "before.sh").read_text(encoding="utf-8")
    for line in job["before_script"]:
        assert line in text


def test_the_image_and_variables_come_from_the_ci_file(tmp_path):
    job = vud.load_job()
    cmd = vud.docker_command(job, vud.MR_SOURCE, REPO, tmp_path, tmp_path)
    assert job["image"] in cmd
    assert "mcr.microsoft.com/playwright/python" in job["image"]
    assert "CI_PIPELINE_SOURCE=merge_request_event" in cmd
    assert "PIP_BREAK_SYSTEM_PACKAGES=1" in cmd
    assert any(a.endswith(",readonly") and "target=/src" in a for a in cmd)
    assert "--init" in cmd and cmd[cmd.index("--name") + 1] == vud.CONTAINER


def test_the_container_name_belongs_to_the_checkout():
    assert vud.CONTAINER.startswith("fdp-validate-ui-") and len(vud.CONTAINER) == len("fdp-validate-ui-") + 8


def test_the_script_keeps_no_second_copy_of_a_check():
    text = SCRIPT.read_text(encoding="utf-8")
    for name in ("check_design_inventory", "check_chart_screenshots", "check_page_css",
                 "check-font-coverage", "pytest"):
        assert name not in text.replace("pytest.", ""), name


def test_a_missing_or_old_dist_is_refused(tmp_path):
    src = tmp_path / "src"
    dist = tmp_path / "dist"
    src.mkdir()
    dist.mkdir()
    (src / "a.astro").write_text("x", encoding="utf-8")
    assert "no built site" in vud.dist_is_stale(dist, src)
    (dist / "index.html").write_text("x", encoding="utf-8")
    import os
    os.utime(src / "a.astro", (dist.stat().st_mtime + 100, dist.stat().st_mtime + 100))
    assert "older" in vud.dist_is_stale(dist, src)
    os.utime(dist / "index.html", (dist.stat().st_mtime + 500, dist.stat().st_mtime + 500))
    assert vud.dist_is_stale(dist, src) is None
