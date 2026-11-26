"""The context guard blocks a session's turn end once, past the token threshold, and fails open."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

HOOK = os.path.join(os.path.dirname(__file__), "..", ".claude", "hooks", "context_guard.py")
sys.path.insert(0, os.path.dirname(HOOK))
import context_guard  # noqa: E402

LIMIT = context_guard.CONTEXT_TOKEN_THRESHOLD


def _assistant(input_tokens=0, cache_creation=0, cache_read=0, **extra) -> dict:
    entry = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": "claude-sonnet-5-5",
            "usage": {
                "input_tokens": input_tokens,
                "cache_creation_input_tokens": cache_creation,
                "cache_read_input_tokens": cache_read,
                "output_tokens": 50,
            },
        },
    }
    entry.update(extra)
    return entry


def _write(path, lines) -> str:
    with open(path, "w", encoding="utf-8") as handle:
        for line in lines:
            handle.write((line if isinstance(line, str) else json.dumps(line)) + "\n")
    return str(path)


def _run(tmp_path, transcript, session_id="s-1", **event_extra):
    event = {"hook_event_name": "Stop", "session_id": session_id, "transcript_path": transcript}
    event.update(event_extra)
    env = {**os.environ, "TMP": str(tmp_path / "tmp"), "TEMP": str(tmp_path / "tmp"), "TMPDIR": str(tmp_path / "tmp")}
    os.makedirs(env["TMP"], exist_ok=True)
    proc = subprocess.run(
        [sys.executable, HOOK], input=json.dumps(event), capture_output=True, text=True, env=env, timeout=30
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def _blocks(out: str) -> bool:
    return bool(out) and json.loads(out)["decision"] == "block"


def test_under_the_threshold_does_not_block(tmp_path):
    t = _write(tmp_path / "t.jsonl", [_assistant(1000, 2000, LIMIT - 3001)])
    assert _run(tmp_path, t) == ""


def test_exactly_at_the_threshold_does_not_block(tmp_path):
    t = _write(tmp_path / "t.jsonl", [_assistant(LIMIT)])
    assert _run(tmp_path, t) == ""


def test_over_the_threshold_blocks_with_the_hand_off_instruction(tmp_path):
    t = _write(tmp_path / "t.jsonl", [_assistant(10, 100_000, LIMIT)])
    out = _run(tmp_path, t)
    assert _blocks(out)
    reason = json.loads(out)["reason"]
    assert "CONTEXT GUARD" in reason and "state file" in reason and "coordinator" in reason
    assert f"{LIMIT + 100_010:,}" in reason


def test_all_three_usage_fields_count(tmp_path):
    t = _write(tmp_path / "t.jsonl", [_assistant(LIMIT // 3 + 1, LIMIT // 3 + 1, LIMIT // 3 + 1)])
    assert _blocks(_run(tmp_path, t))


def test_a_second_stop_in_the_same_session_does_not_block(tmp_path):
    t = _write(tmp_path / "t.jsonl", [_assistant(LIMIT + 1)])
    assert _blocks(_run(tmp_path, t))
    assert _run(tmp_path, t) == ""


def test_another_session_is_blocked_on_its_own(tmp_path):
    t = _write(tmp_path / "t.jsonl", [_assistant(LIMIT + 1)])
    assert _blocks(_run(tmp_path, t, session_id="a"))
    assert _blocks(_run(tmp_path, t, session_id="b"))


def test_the_continuation_after_the_block_is_not_blocked_and_leaves_no_second_block(tmp_path):
    t = _write(tmp_path / "t.jsonl", [_assistant(LIMIT + 1)])
    assert _run(tmp_path, t, stop_hook_active=True) == ""
    assert _blocks(_run(tmp_path, t))


def test_the_last_assistant_message_decides_not_the_largest(tmp_path):
    t = _write(tmp_path / "t.jsonl", [_assistant(LIMIT + 1), _assistant(5000)])
    assert _run(tmp_path, t) == ""


def test_no_usage_lines_does_not_block(tmp_path):
    lines = [{"type": "user", "message": {"role": "user", "content": "hi"}},
             {"type": "assistant", "message": {"role": "assistant", "content": []}}]
    assert _run(tmp_path, _write(tmp_path / "t.jsonl", lines)) == ""


def test_an_empty_transcript_does_not_block(tmp_path):
    assert _run(tmp_path, _write(tmp_path / "t.jsonl", [])) == ""


def test_a_malformed_line_is_skipped_and_the_valid_one_before_it_counts(tmp_path):
    t = _write(tmp_path / "t.jsonl", [_assistant(LIMIT + 1), "{not json", '{"type": "assistant", "mess'])
    assert _blocks(_run(tmp_path, t))


def test_only_malformed_lines_do_not_block(tmp_path):
    assert _run(tmp_path, _write(tmp_path / "t.jsonl", ["{not json", "[1, 2]", "null", "7"])) == ""


def test_usage_on_non_assistant_entries_is_ignored(tmp_path):
    big = {"usage": {"input_tokens": LIMIT * 2, "cache_read_input_tokens": LIMIT * 2}}
    lines = [
        _assistant(1000),
        {"type": "user", "message": {"role": "user", "usage": big["usage"]}, "usage": big["usage"]},
        {"type": "system", "usage": big["usage"]},
        {"type": "summary", "message": {"role": "assistant", "usage": big["usage"]}},
        {"type": "assistant", "message": {"role": "user", "usage": big["usage"]}},
    ]
    assert _run(tmp_path, _write(tmp_path / "t.jsonl", lines)) == ""


def test_usage_on_non_assistant_entries_alone_does_not_block(tmp_path):
    lines = [{"type": "user", "message": {"role": "user", "usage": {"input_tokens": LIMIT * 2}}}]
    assert _run(tmp_path, _write(tmp_path / "t.jsonl", lines)) == ""


def test_sidechain_synthetic_and_zero_usage_entries_are_skipped(tmp_path):
    synthetic = _assistant(10)
    synthetic["message"]["model"] = "<synthetic>"
    lines = [_assistant(LIMIT + 1), _assistant(10, isSidechain=True), synthetic, _assistant(0)]
    assert _blocks(_run(tmp_path, _write(tmp_path / "t.jsonl", lines)))


def test_the_block_tells_the_session_to_edit_nothing_but_the_state_file(tmp_path):
    reason = json.loads(_run(tmp_path, _write(tmp_path / "t.jsonl", [_assistant(LIMIT + 1)])))["reason"]
    assert "Make no edit to the tree except the state file" in reason


@pytest.mark.parametrize("bad", ["lots", -5, 1.5, True, [3]])
def test_a_usage_value_that_is_not_a_count_never_blocks(tmp_path, bad):
    entry = _assistant(0)
    entry["message"]["usage"]["input_tokens"] = bad
    entry["message"]["usage"]["cache_read_input_tokens"] = LIMIT + 1
    assert _run(tmp_path, _write(tmp_path / "t.jsonl", [entry])) == ""


def test_a_missing_transcript_does_not_block(tmp_path):
    assert _run(tmp_path, str(tmp_path / "absent.jsonl")) == ""


def test_a_directory_as_transcript_does_not_block(tmp_path):
    assert _run(tmp_path, str(tmp_path)) == ""


def test_a_missing_transcript_path_or_session_id_does_not_block(tmp_path):
    t = _write(tmp_path / "t.jsonl", [_assistant(LIMIT + 1)])
    assert _run(tmp_path, None) == ""
    assert _run(tmp_path, t, session_id=None) == ""
    assert _run(tmp_path, t, session_id="") == ""
    assert _run(tmp_path, t, session_id=7) == ""


def test_an_unreadable_event_does_not_block():
    proc = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0 and proc.stdout.strip() == ""


def test_a_session_id_with_path_characters_stays_inside_the_marker_folder(tmp_path):
    t = _write(tmp_path / "t.jsonl", [_assistant(LIMIT + 1)])
    assert _blocks(_run(tmp_path, t, session_id="../../escape"))
    assert not (tmp_path / "escape").exists()
    assert _run(tmp_path, t, session_id="../../escape") == ""


def test_a_marker_that_cannot_be_written_does_not_block(tmp_path, monkeypatch, capsys):
    t = _write(tmp_path / "t.jsonl", [_assistant(LIMIT + 1)])
    blocker = tmp_path / "blocked"
    blocker.write_text("a file where the folder should be", encoding="utf-8")
    monkeypatch.setattr(context_guard.tempfile, "gettempdir", lambda: str(blocker))
    monkeypatch.setattr(sys, "stdin", __import__("io").StringIO(json.dumps(
        {"session_id": "s-x", "transcript_path": t})))
    assert context_guard.main() == 0
    assert capsys.readouterr().out == ""


def test_the_last_message_is_found_in_a_transcript_larger_than_the_first_read(tmp_path):
    filler = {"type": "user", "message": {"role": "user", "content": "x" * 4000}}
    lines = [_assistant(LIMIT + 1)] + [filler] * 400
    assert os.path.getsize(_write(tmp_path / "t.jsonl", lines)) > context_guard._FIRST_READ_BYTES
    assert _blocks(_run(tmp_path, str(tmp_path / "t.jsonl")))


def test_an_assistant_line_larger_than_the_first_read_is_read_whole(tmp_path):
    entry = _assistant(LIMIT + 1)
    entry["message"]["content"] = [{"type": "text", "text": "y" * (context_guard._FIRST_READ_BYTES * 2)}]
    assert _blocks(_run(tmp_path, _write(tmp_path / "t.jsonl", [entry])))


def test_the_hook_is_registered_next_to_the_stop_gate():
    settings = os.path.join(os.path.dirname(HOOK), "..", "settings.json")
    with open(settings, encoding="utf-8") as handle:
        stop = json.load(handle)["hooks"]["Stop"]
    commands = [h["command"] for group in stop for h in group["hooks"]]
    assert any("stop_gate.py" in c for c in commands)
    assert any("context_guard.py" in c for c in commands)
