"""Runs the apply recipe in `deploy/nightly/README.md` against a stubbed Monitoring API.

Every policy declared in `alert-policy.json` must receive a write; running the snippet under `exec`
tests its behaviour rather than its spelling.
"""

from __future__ import annotations

import ast
import json
import os
import re
import tempfile
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
README = REPO / "deploy" / "nightly" / "README.md"
POLICY_FILE = REPO / "deploy" / "nightly" / "alert-policy.json"

SECTION_START = "### Create the alert policies"
SECTION_END = "### Checking and silencing it"

_FAKE_CHANNEL = "projects/fake/notificationChannels/1"
_FAKE_PROJECT = "projects/football-data-pipeline-gcp"


def _section() -> str:
    text = README.read_text(encoding="utf-8")
    assert SECTION_START in text, "the %r section is gone - retarget this test" % SECTION_START
    body = text.split(SECTION_START, 1)[1]
    assert SECTION_END in body, "the %r section is gone - retarget this test" % SECTION_END
    return body.split(SECTION_END, 1)[0]


def _declared_policy_names() -> list[str]:
    return [
        p["displayName"]
        for p in json.loads(POLICY_FILE.read_text(encoding="utf-8"))["policies"]
    ]


def _recipe_python_source() -> str:
    """The Python heredoc inside the apply block — the thing that actually does the work."""
    match = re.search(r"<<'EOF'\n(.*?)\nEOF\b", _section(), re.DOTALL)
    assert match, (
        "The apply recipe no longer contains a `python - <<'EOF' ... EOF` block. If it was "
        "deliberately reshaped, retarget this test at whatever now performs the apply - do NOT "
        "delete it. It is the only thing standing between this recipe and a silent repeat of "
        "GitLab #61."
    )
    return match.group(1)


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


def _run_recipe(
    existing: list[dict],
    policies: list[dict] | None = None,
) -> list[tuple[str, str, dict | None]]:
    """Run the recipe on a stubbed API; `policies` replaces the file's content so a baked-in count fails."""
    calls: list[tuple[str, str, dict | None]] = []

    def fake_urlopen(req, *args, **kwargs):  # noqa: ANN001 - mirrors urlopen's loose signature
        method = req.get_method()
        url = req.full_url
        body = json.loads(req.data.decode("utf-8")) if req.data else None
        calls.append((method, url, body))
        if method == "GET" and url.endswith("/notificationChannels"):
            return _FakeResponse({"notificationChannels": [{"name": _FAKE_CHANNEL}]})
        if method == "GET" and url.endswith("/alertPolicies"):
            return _FakeResponse({"alertPolicies": existing})
        return _FakeResponse({})

    source = _recipe_python_source()
    real_urlopen = urllib.request.urlopen
    real_token = os.environ.get("TOKEN")
    cwd = os.getcwd()
    urllib.request.urlopen = fake_urlopen
    os.environ["TOKEN"] = "fake-token-for-tests"

    with tempfile.TemporaryDirectory() as tmp:
        # The recipe opens `deploy/nightly/alert-policy.json` by relative path.
        root = Path(tmp)
        target = root / "deploy" / "nightly" / "alert-policy.json"
        target.parent.mkdir(parents=True)
        if policies is None:
            target.write_text(POLICY_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            target.write_text(json.dumps({"policies": policies}), encoding="utf-8")
        os.chdir(root)
        try:
            exec(  # noqa: S102 - executing the runbook IS the test; see the module docstring
                compile(source, "<deploy/nightly/README.md apply recipe>", "exec"),
                {"__name__": "__recipe__"},
            )
        finally:
            os.chdir(cwd)
            urllib.request.urlopen = real_urlopen
            if real_token is None:
                os.environ.pop("TOKEN", None)
            else:
                os.environ["TOKEN"] = real_token
    return calls


def _synthetic_policies(count: int) -> list[dict]:
    """A policy set deliberately UNLIKE the real one: different size, different names."""
    return [
        {
            "displayName": "synthetic policy %d" % i,
            "combiner": "OR",
            "enabled": True,
            "_comment": ["reader-only key, must be stripped before sending"],
            "conditions": [
                {
                    "displayName": "synthetic condition %d" % i,
                    "conditionThreshold": {
                        "filter": 'resource.type = "cloud_run_job"',
                        "comparison": "COMPARISON_GT",
                        "thresholdValue": 0,
                        "duration": "0s",
                        "trigger": {"count": 1},
                    },
                }
            ],
        }
        for i in range(count)
    ]


def _written_display_names(calls, method: str) -> set[str]:
    return {
        body["displayName"]
        for verb, _url, body in calls
        if verb == method and isinstance(body, dict) and "displayName" in body
    }


def test_recipe_creates_every_declared_policy_on_an_empty_project():
    declared = set(_declared_policy_names())
    calls = _run_recipe(existing=[])
    created = _written_display_names(calls, "POST")

    missing = declared - created
    assert not missing, (
        "The apply recipe never sends %s. Every policy declared in alert-policy.json must be "
        "applied - a declared policy that is never written is GitLab #61 exactly, and the one "
        "it dropped was the alert that watches the monitoring itself." % sorted(missing)
    )
    assert created == declared, "recipe wrote policies not in the file: %s" % sorted(created - declared)


def test_recipe_updates_every_declared_policy_and_creates_nothing_when_all_exist():
    declared = _declared_policy_names()
    existing = [
        {"displayName": name, "name": "%s/alertPolicies/%d" % (_FAKE_PROJECT, i)}
        for i, name in enumerate(declared)
    ]
    calls = _run_recipe(existing=existing)

    updated = _written_display_names(calls, "PATCH")
    missing = set(declared) - updated
    assert not missing, (
        "On a re-run the recipe never updates %s. Every declared policy must be reconciled, "
        "not just the ones that happen to come first." % sorted(missing)
    )

    posts = [url for verb, url, _ in calls if verb == "POST"]
    assert not posts, (
        "The recipe POSTed %d time(s) when every declared policy already existed. That creates "
        "DUPLICATE alert policies, and duplicates are how people learn to ignore alerts."
        % len(posts)
    )


# Several sizes, odd and even, so no single baked-in bound or parity-based skip can pass them all.
_SIZES = [1, 2, 3, 5, 8, 17]


@pytest.mark.parametrize("size", _SIZES)
def test_recipe_applies_every_policy_at_any_set_size(size: int):
    synthetic = _synthetic_policies(size)
    declared = {p["displayName"] for p in synthetic}
    created = _written_display_names(_run_recipe(existing=[], policies=synthetic), "POST")
    assert created == declared, (
        "Given a %d-policy file the recipe created %d of them. It must apply every declared "
        "policy at any count." % (size, len(created))
    )


@pytest.mark.parametrize("size", _SIZES)
def test_recipe_reconciles_every_policy_at_any_set_size(size: int):
    synthetic = _synthetic_policies(size)
    declared = {p["displayName"] for p in synthetic}
    calls = _run_recipe(existing=_as_existing(synthetic), policies=synthetic)
    updated = _written_display_names(calls, "PATCH")
    assert updated == declared, (
        "Given a %d-policy file where all already exist, the recipe reconciled %d of them. "
        "Every declared policy must be updated on a re-run, at any count." % (size, len(updated))
    )
    assert not [u for verb, u, _ in calls if verb == "POST"], "duplicate POST on a re-run"


def test_recipe_applies_a_policy_set_LARGER_than_todays_file():
    """A bound that equals today's policy count passes every test that uses the real file."""
    synthetic = _synthetic_policies(5)
    declared = {p["displayName"] for p in synthetic}
    calls = _run_recipe(existing=[], policies=synthetic)
    created = _written_display_names(calls, "POST")

    assert created == declared, (
        "Given a %d-policy file the recipe applied %d of them (%s). It must apply every "
        "policy the file declares, whatever that number turns out to be - a bound that "
        "matches today's count is exactly how GitLab #61 shipped looking correct."
        % (len(synthetic), len(created), sorted(created))
    )


def test_recipe_applies_a_policy_set_SMALLER_than_todays_file():
    """Catches a recipe that hardcodes today's policy names instead of reading the file."""
    synthetic = _synthetic_policies(1)
    declared = {p["displayName"] for p in synthetic}
    calls = _run_recipe(existing=[], policies=synthetic)
    created = _written_display_names(calls, "POST")

    assert created == declared, (
        "Given a 1-policy file the recipe applied %s. Anything other than exactly the declared "
        "set means it is not reading the file - most likely the policy names are hardcoded in "
        "the recipe." % sorted(created)
    )


def _as_existing(policies: list[dict]) -> list[dict]:
    """Declared policies as the API would report them deployed, with distinct ids per policy."""
    return [
        {"displayName": p["displayName"], "name": "%s/alertPolicies/%d" % (_FAKE_PROJECT, 100 + i)}
        for i, p in enumerate(policies)
    ]


def test_every_patch_targets_the_resource_named_in_its_own_body():
    """Each PATCH must hit the id of the policy it carries, which name counts alone do not show."""
    synthetic = _synthetic_policies(4)
    existing = _as_existing(synthetic)
    id_by_name = {e["displayName"]: e["name"].rsplit("/", 1)[1] for e in existing}

    calls = _run_recipe(existing=existing, policies=synthetic)
    patches = [(url, body) for verb, url, body in calls if verb == "PATCH"]
    assert len(patches) == len(synthetic), (
        "expected one PATCH per declared policy, got %d for %d" % (len(patches), len(synthetic))
    )

    for url, body in patches:
        name = body["displayName"]
        expected_id = id_by_name[name]
        assert url.rsplit("/", 1)[1] == expected_id, (
            "PATCH for %r was sent to resource id %r but that policy is %r. The recipe is "
            "aiming updates at the wrong resource: every policy would overwrite one victim "
            "and the rest would never be reconciled." % (name, url.rsplit("/", 1)[1], expected_id)
        )

    targeted = {url.rsplit("/", 1)[1] for url, _ in patches}
    assert len(targeted) == len(synthetic), (
        "the %d PATCHes hit only %d distinct resources (%s) - policies are overwriting each "
        "other." % (len(patches), len(targeted), sorted(targeted))
    )


def test_recipe_updates_a_policy_set_LARGER_than_todays_file():
    """A bound inside the update branch is invisible to a set the size of today's file."""
    synthetic = _synthetic_policies(5)
    declared = {p["displayName"] for p in synthetic}
    calls = _run_recipe(existing=_as_existing(synthetic), policies=synthetic)

    updated = _written_display_names(calls, "PATCH")
    assert updated == declared, (
        "Given a %d-policy file where all %d already exist, the recipe reconciled %d of them "
        "(%s). Every declared policy must be updated on a re-run, whatever the count - a bound "
        "inside the update branch is GitLab #61 relocated, not fixed."
        % (len(synthetic), len(synthetic), len(updated), sorted(updated))
    )
    posts = [url for verb, url, _ in calls if verb == "POST"]
    assert not posts, "recipe POSTed %d duplicate(s) when everything already existed" % len(posts)


def test_recipe_reconciles_a_MIXED_set_of_existing_and_new_policies():
    """A policy added to the file while the rest exist needs both branches live in one run."""
    synthetic = _synthetic_policies(5)
    declared = {p["displayName"] for p in synthetic}
    already = _as_existing(synthetic[:2])

    calls = _run_recipe(existing=already, policies=synthetic)
    written = _written_display_names(calls, "PATCH") | _written_display_names(calls, "POST")

    missing = declared - written
    assert not missing, (
        "With 2 of 5 policies already deployed the recipe never wrote %s. Adding a policy to "
        "the file must apply it while the existing ones are reconciled - that is the exact "
        "situation #61 was found in." % sorted(missing)
    )
    assert _written_display_names(calls, "PATCH") == {p["displayName"] for p in synthetic[:2]}, (
        "the 2 pre-existing policies must be PATCHed, not re-created"
    )
    assert _written_display_names(calls, "POST") == {p["displayName"] for p in synthetic[2:]}, (
        "the 3 new policies must be POSTed, not skipped"
    )


def test_recipe_never_deletes_anything():
    """A cleanup pass that removes a policy after applying it would undo the apply."""
    for existing in ([], [{"displayName": n, "name": "%s/alertPolicies/%d" % (_FAKE_PROJECT, i)}
                          for i, n in enumerate(_declared_policy_names())]):
        calls = _run_recipe(existing=existing)
        deletes = [url for verb, url, _ in calls if verb == "DELETE"]
        assert not deletes, (
            "The apply recipe issues a DELETE (%s). Applying policies must not remove one - "
            "that is the same end state as never creating it." % deletes
        )


def test_recipe_sends_a_notification_channel_on_every_policy():
    """A policy with no channel is armed and silent, which is the failure this area exists for."""
    calls = _run_recipe(existing=[])
    written = [b for verb, _u, b in calls if verb in ("POST", "PATCH") and isinstance(b, dict)]
    assert written, "the recipe wrote nothing at all"
    for body in written:
        assert body.get("notificationChannels"), (
            "policy %r is applied with no notificationChannels - it would fire into nowhere."
            % body.get("displayName")
        )


def test_recipe_strips_underscore_prefixed_keys_before_sending():
    """`_comment` keys are for the reader; the API rejects unknown fields."""
    calls = _run_recipe(existing=[])
    for verb, _url, body in calls:
        if verb in ("POST", "PATCH") and isinstance(body, dict):
            leaked = [k for k in body if k.startswith("_")]
            assert not leaked, (
                "policy %r is sent with reader-only key(s) %s, which the Monitoring API "
                "rejects." % (body.get("displayName"), leaked)
            )


def test_recipe_python_block_is_valid_python():
    try:
        ast.parse(_recipe_python_source())
    except SyntaxError as exc:  # pragma: no cover - the message is the point
        raise AssertionError(
            "The documented apply snippet is not valid Python (%s at line %s)."
            % (exc.msg, exc.lineno)
        ) from exc


def test_prose_states_no_policy_count_that_disagrees_with_the_file():
    declared = len(_declared_policy_names())
    words = {2: "both", 3: "three", 4: "four", 5: "five"}
    section = _section().lower()

    wrong = [
        word
        for count, word in words.items()
        if count != declared and re.search(r"\b%s\b[^.]{0,40}\bpolic" % word, section)
    ]
    assert not wrong, (
        "The apply section claims %s polic(y/ies) while alert-policy.json declares %d. "
        "State no number, or state the right one - a stale count is how #61 read as correct."
        % (" and ".join(wrong), declared)
    )


def test_every_declared_policy_has_a_unique_display_name():
    """The recipe keys create-vs-update on displayName, so a collision overwrites a policy."""
    names = _declared_policy_names()
    assert all(n and n.strip() for n in names), "a declared policy has an empty displayName"
    assert len(names) == len(set(names)), (
        "two declared policies share a displayName, so an idempotent apply cannot tell them "
        "apart and one would PATCH over the other: %s" % names
    )
