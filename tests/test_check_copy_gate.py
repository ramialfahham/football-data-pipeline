import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import check_copy_gate as gate  # noqa: E402


def _strings(en_unit: str, other_unit: str) -> str:
    """A synthetic strings.ts whose only word-shaped value is `unit`, EN against DE and FI."""
    out = []
    for loc, unit in (("EN", en_unit), ("DE", "Min."), ("FI", other_unit)):
        body = "".join(f'  key{i}: "v{i}",\n' for i in range(40)) + f'  unit: "{unit}",\n'
        out.append(f"const {loc}: Dict = {{\n{body}}};\n")
    for loc in ("EN", "DE", "FI"):
        body = "".join(f'  "metrics.m{i}.label": "m{i}",\n' for i in range(18))
        out.append(f"const METRIC_LABELS_{loc}: MetricLabels = {{\n{body}}};\n")
    return "\n".join(out)


def _untranslated(tmp_path, monkeypatch, capsys, en_unit, other_unit):
    path = tmp_path / "strings.ts"
    path.write_text(_strings(en_unit, other_unit), encoding="utf-8")
    monkeypatch.setattr(gate, "STRINGS", path)
    monkeypatch.setattr(gate, "_seed_label_keys", lambda *_a: {})
    gate.main()
    return [line for line in capsys.readouterr().out.splitlines() if "untranslated: fi.unit" in line]


def test_a_listed_unit_symbol_may_read_the_same_in_two_languages(tmp_path, monkeypatch, capsys):
    assert "min" in gate.UNIT_SYMBOLS
    assert _untranslated(tmp_path, monkeypatch, capsys, "min", "min") == []


@pytest.mark.parametrize("word", ["mins", "minutes", "min."])
def test_a_word_not_on_the_list_still_fails_when_left_untranslated(tmp_path, monkeypatch, capsys, word):
    assert word not in gate.UNIT_SYMBOLS
    assert len(_untranslated(tmp_path, monkeypatch, capsys, word, word)) == 1
