import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import check_research_fix_mr as chk  # noqa: E402

SKILL_TEXT = open(os.path.join(ROOT, chk.SKILL), encoding="utf-8").read()
CARD = "dbt_project/seeds/fixture_card_corrections.csv"
RESULT = "dbt_project/seeds/fixture_result_corrections.csv"
GOAL = "dbt_project/seeds/fixture_goal_corrections.csv"
CARD_HEADER = "fixture_id,card_order,team_id,player_id,player_name,minute_elapsed,minute_extra,event_detail,source_kind,source,note\n"
RESULT_HEADER = "fixture_id,goals_home,goals_away,awarded,source_kind,source,note\n"
GOAL_HEADER = "fixture_id,goal_order,team_id,player_name,source_kind,source,note\n"
OLD_CARD = "1,1,10,100,A. One,32,,Yellow Card,official,https://www.uefa.com/match/1/,old row on a stopped site\n"
OK_URL = "https://www.premierleague.com/en/match/1/a-vs-b"


def sh(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def write(repo, rel, text):
    path = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


@pytest.fixture()
def repo(tmp_path):
    r = str(tmp_path)
    sh(r, "init", "-q", "-b", "main")
    sh(r, "config", "user.email", "t@t")
    sh(r, "config", "user.name", "t")
    write(r, chk.SKILL, SKILL_TEXT)
    write(r, CARD, CARD_HEADER + OLD_CARD)
    write(r, RESULT, RESULT_HEADER + f"5,1,0,false,official,{OK_URL},m\n")
    write(r, GOAL, GOAL_HEADER + f"7,1,10,B. Two,official,{OK_URL},m\n")
    write(r, "scripts/other.py", "x = 1\n")
    sh(r, "add", "-A")
    sh(r, "commit", "-qm", "base")
    sh(r, "checkout", "-qb", "research-fix/2026-11-20")
    return r


def commit(repo):
    sh(repo, "add", "-A")
    sh(repo, "commit", "-qm", "fix")


def card_row(n, source=OK_URL, kind="official"):
    return f"2,{n},10,100,A. One,32,,Yellow Card,{kind},{source},match checked\n"


def reasons(repo):
    return chk.decide("main", "HEAD", repo)


def test_added_rows_with_allowed_sources_pass(repo):
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1) + card_row(2, source=f"{OK_URL} https://www.skysports.com/x"))
    commit(repo)
    assert reasons(repo) == []


def test_old_rows_on_stopped_sites_are_not_judged(repo):
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1))
    commit(repo)
    assert reasons(repo) == []


def test_changed_row_is_judged_like_an_added_one(repo):
    changed = OLD_CARD.replace("32,,", "33,,")
    write(repo, CARD, CARD_HEADER + changed)
    commit(repo)
    assert any("uefa.com" in r for r in reasons(repo))


def test_task_folder_files_are_allowed(repo):
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1))
    write(repo, ".claude/task/262-research-fix-2026-11-20/contract.md", "c")
    write(repo, ".claude/task/262-research-fix-2026-11-20/review.md", "r")
    commit(repo)
    assert reasons(repo) == []


def test_two_task_folders_refused(repo):
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1))
    write(repo, ".claude/task/a/contract.md", "c")
    write(repo, ".claude/task/b/contract.md", "c")
    commit(repo)
    assert any("more than one task folder" in r for r in reasons(repo))


def test_other_file_refused(repo):
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1))
    write(repo, "scripts/other.py", "x = 2\n")
    commit(repo)
    assert any("scripts/other.py" in r for r in reasons(repo))


def test_other_seed_refused(repo):
    write(repo, "dbt_project/seeds/standings_corrections.csv", "a,b\n1,2\n")
    commit(repo)
    assert any("standings_corrections" in r for r in reasons(repo))


def test_task_folder_only_is_not_a_fix(repo):
    write(repo, ".claude/task/a/contract.md", "c")
    commit(repo)
    assert any("no correction seed" in r for r in reasons(repo))


def test_no_change_refused(repo):
    assert reasons(repo) == ["the MR changes nothing"]


def test_header_change_refused(repo):
    write(repo, CARD, CARD_HEADER.replace("note", "notes") + OLD_CARD)
    commit(repo)
    assert any("header changed" in r for r in reasons(repo))


def test_removed_row_refused(repo):
    write(repo, CARD, CARD_HEADER)
    commit(repo)
    assert any("is removed" in r for r in reasons(repo))


def test_empty_source_refused(repo):
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1, source=""))
    commit(repo)
    assert any("no source" in r for r in reasons(repo))


@pytest.mark.parametrize("url", [
    "https://www.uefa.com/uefachampionsleague/match/1/",
    "https://www.fifa.com/x",
    "https://www.espn.com/soccer/x",
    "https://www.bundesliga.com/x",
    "https://en.wikipedia.org/wiki/X",
    "https://www.transfermarkt.com/x",
    "https://www.fff.fr/x",
])
def test_stopped_and_unlisted_hosts_refused(repo, url):
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1, source=f"{OK_URL} {url}"))
    commit(repo)
    assert any("not on the skill's list" in r for r in reasons(repo))


def test_non_https_source_refused(repo):
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1, source="http://www.premierleague.com/x"))
    commit(repo)
    assert any("not an https URL" in r for r in reasons(repo))


def test_subdomain_of_an_allowed_host_refused(repo):
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1, source="https://www.premierleague.com.evil.example/x"))
    commit(repo)
    assert any("not on the skill's list" in r for r in reasons(repo))


def test_duplicate_key_refused(repo):
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1) + card_row(1))
    commit(repo)
    assert any("appears twice" in r for r in reasons(repo))


def test_wrong_field_count_refused(repo):
    write(repo, CARD, CARD_HEADER + OLD_CARD + "2,1,10\n")
    commit(repo)
    assert any("fields" in r for r in reasons(repo))


def test_result_and_goal_seeds_pass_with_a_row_each(repo):
    write(repo, RESULT, RESULT_HEADER + f"5,1,0,false,official,{OK_URL},m\n6,2,1,false,official,{OK_URL},m\n")
    write(repo, GOAL, GOAL_HEADER + f"7,1,10,B. Two,official,{OK_URL},m\n7,2,10,C. Three,official,{OK_URL},m\n")
    commit(repo)
    assert reasons(repo) == []


def test_skill_on_the_merge_base_decides_not_the_head(repo):
    write(repo, chk.SKILL, SKILL_TEXT.replace("`www.skysports.com`", "`www.uefa.com`"))
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1, source="https://www.uefa.com/x"))
    commit(repo)
    assert any(chk.SKILL in r for r in reasons(repo))


def test_cli_exit_codes(repo):
    script = os.path.join(ROOT, "scripts", "check_research_fix_mr.py")
    write(repo, CARD, CARD_HEADER + OLD_CARD + card_row(1))
    commit(repo)
    ok = subprocess.run([sys.executable, script, "--base", "main"], cwd=repo, capture_output=True, text=True)
    assert ok.returncode == 0
    write(repo, "scripts/other.py", "x = 3\n")
    commit(repo)
    bad = subprocess.run([sys.executable, script, "--base", "main"], cwd=repo, capture_output=True, text=True)
    assert bad.returncode == 1 and "scripts/other.py" in bad.stdout
    undecided = subprocess.run([sys.executable, script, "--base", "no-such-ref"], cwd=repo,
                               capture_output=True, text=True)
    assert undecided.returncode == 2


def test_allowed_hosts_come_from_the_skill_tables():
    hosts = chk.allowed_hosts(SKILL_TEXT)
    assert {"www.premierleague.com", "www.dfb.de", "t-online.de", "www.skysports.com"} <= hosts
    for stopped in ("uefa", "fifa", "mls", "bundesliga", "espn", "rfef", "wikipedia", "transfermarkt",
                    "fff.fr", "conmebol"):
        assert not [h for h in hosts if stopped in h], stopped


def test_seed_set_is_the_set_the_skill_writes_to():
    section = SKILL_TEXT.split("## 7. Write the proposed rows", 1)[1].split("\n## ", 1)[0]
    assert set(re.findall(r"`(fixture_\w+_corrections)`", section)) == set(chk.SEED_KEYS)


def test_key_columns_exist_in_the_real_seed_headers():
    for path, key in chk.SEEDS.items():
        header = open(os.path.join(ROOT, path), encoding="utf-8").readline().strip().split(",")
        assert all(c in header and c != "source" for c in key) and "source" in header, path
