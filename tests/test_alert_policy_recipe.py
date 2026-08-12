"""The alert-policy apply recipe must apply EVERY declared policy (GitLab #61).

WHY THIS EXISTS
---------------
`deploy/nightly/README.md` documents how the Cloud Monitoring alert policies get created. Its
apply step used to end in `for i in 0 1` — a literal index list — over a generator that writes
one payload per policy declared in `deploy/nightly/alert-policy.json`. The file later grew to
three. Index 2 was generated and never sent.

The policy that went missing was `fdp freshness sentinel itself stopped`: the one that fires
when the freshness sentinel itself dies. So the dropped alert was precisely the alert whose
absence nothing else can reveal. It FAILS OPEN — the broken state looks identical to the
working one — and it sat undeployed until found by accident on 2026-08-11.

HOW IT IS SHAPED, AND TWO REJECTED ATTEMPTS
-------------------------------------------
This test went through two wrong versions before this one, both caught in review, and the
progression is the useful part:

  v1 matched the SHAPE OF THE RETIRED BASH RECIPE (`for i in 0 1`, `{0..1}`, `polN.json`). The
     fixed recipe is Python, so every pattern was already unreachable.
  v2 parsed the recipe with `ast` and forbade a number, slice, `islice` or `break` in the loop
     expression. Better, but still a shape test, and a reviewer produced four rewrites that
     reproduce #61 while passing all of it: hoisting the slice into a variable
     (`policies_to_apply = ...[:2]`), a `continue` that skips one policy, a filter baked into a
     generator expression, and a second statement that undoes the loop afterwards.

The lesson both times: a static check on a snippet tests how the code LOOKS, and the defect is
about what it DOES. Any shape test can be walked around by writing the same bug differently.

So this version RUNS the documented recipe against a stubbed Monitoring API and asserts the
only thing that actually matters: **every policy declared in `alert-policy.json` receives a
write.** Truncation, filtering, early exit, hoisting and post-hoc deletion all fail it
identically, because they all end in a declared policy that never got written.

Running repo-controlled, version-controlled, reviewed documentation under `exec` is deliberate.
It is the only way to test a runbook snippet's behaviour rather than its spelling, and it has
the side benefit of proving the documented commands are executable at all — a runbook that does
not run is the failure mode this whole area keeps producing.

`tests/test_nightly_entrypoint_parity.py` is the precedent for pinning a deploy artefact.
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
    """Execute the documented recipe against a stubbed API. Returns every request it made.

    `existing` is what the fake API reports as already deployed, so the caller can drive both
    the create path (empty) and the update path (everything already there).

    `policies` replaces the CONTENT of `alert-policy.json` for the run. This is what makes the
    suite count-independent, and it is not a refinement — it is the whole difference between
    catching #61 and re-shipping it. A test that only ever runs against the real file cannot
    tell "iterates every policy" from "hardcoded to a bound that equals today's count", and the
    second is precisely what #61 was: `for i in 0 1` was CORRECT on the day it was written,
    when the file declared two. Running against a set of a different size makes any baked-in
    count fail at the moment it is written instead of silently, later, when a policy is added.
    """
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
        # The recipe opens `deploy/nightly/alert-policy.json` by relative path, so the run
        # happens in a directory where that path holds whatever this call is testing against.
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
    """THE LOAD-BEARING CHECK, create path. Nothing declared may be silently skipped."""
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
    """THE LOAD-BEARING CHECK, update path. This is the idempotency claim, executed."""
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


# Sizes the count-independence tests run at. MORE THAN ONE, ON PURPOSE.
#
# An earlier version used 5 everywhere, and a reviewer pointed out that this had simply MOVED
# the hardcoded number rather than removed it: a bound of exactly 5 - the size the suite itself
# had standardised on - was invisible to every test. The same defect as #61, one layer up.
#
# No finite set of sizes proves a universal property. What this does is make a surviving bound
# absurd: it would have to be >= 17 to pass, which is not a number anyone writes by accident
# while a file declares 3. The odd/even mix also kills parity-based skips.
_SIZES = [1, 2, 3, 5, 8, 17]


@pytest.mark.parametrize("size", _SIZES)
def test_recipe_applies_every_policy_at_any_set_size(size: int):
    """COUNT-INDEPENDENCE, create path, across sizes so no single constant can hide."""
    synthetic = _synthetic_policies(size)
    declared = {p["displayName"] for p in synthetic}
    created = _written_display_names(_run_recipe(existing=[], policies=synthetic), "POST")
    assert created == declared, (
        "Given a %d-policy file the recipe created %d of them. It must apply every declared "
        "policy at any count." % (size, len(created))
    )


@pytest.mark.parametrize("size", _SIZES)
def test_recipe_reconciles_every_policy_at_any_set_size(size: int):
    """COUNT-INDEPENDENCE, update path, across sizes. Kills a bound inside the PATCH branch."""
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
    """COUNT-INDEPENDENCE, and the single most important test in this file.

    Every other test compares the recipe against the real `alert-policy.json`, so a bound that
    happens to equal today's count — `[:3]` against three declared policies, or a hardcoded
    list of today's three names — passes them all. That is not a hypothetical: it is #61's
    exact mechanism. `for i in 0 1` was CORRECT when it was written, and became a silent
    data-loss bug only when a third policy was added.

    Running against a synthetic set of a DIFFERENT size makes any baked-in count fail the
    moment it is written, which is the only time it is cheap to fix.
    """
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
    """The other side of count-independence: it must not invent policies either.

    Catches a recipe that stopped reading the file and hardcoded today's names as literals -
    which the deleted static check used to catch, and which a larger-set test alone does not.
    """
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
    """Turn declared policies into what the API would report as already deployed.

    The ids are deliberately distinct per policy so a test can check that each PATCH is aimed
    at the RIGHT one - see test_every_patch_targets_the_resource_named_in_its_own_body.
    """
    return [
        {"displayName": p["displayName"], "name": "%s/alertPolicies/%d" % (_FAKE_PROJECT, 100 + i)}
        for i, p in enumerate(policies)
    ]


def test_every_patch_targets_the_resource_named_in_its_own_body():
    """Each PATCH must hit the id of the policy it is carrying, not merely SOME id.

    Every other assertion in this file reads `body["displayName"]` and ignores the URL. That
    leaves a worse bug than #61 completely uncovered: a recipe that derives the target id
    wrongly - `list(existing.values())[0]["name"]` instead of `existing[name]["name"]` - still
    sends one PATCH per declared policy, each carrying its own correct displayName, so the
    counts and the name sets all come out right. In production every PATCH lands on the SAME
    alert policy: one gets overwritten repeatedly and the rest silently go stale forever, while
    the recipe prints "updated" for each of them.

    #61 left one policy undeployed. This would leave N-1 permanently unreconciled.
    """
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
    """COUNT-INDEPENDENCE ON THE UPDATE BRANCH.

    The create-path tests above pass `existing=[]`, so they never enter `if name in existing`.
    A bound placed inside THAT branch — `if patch_count >= 3: continue` — passes them and also
    passes the real-file update test, because the real file has exactly three pre-existing
    policies and the counter runs out exactly as the loop ends. It then silently stops
    reconciling the fourth policy forever. Same #61 shape, one branch over.
    """
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
    """The real steady state: a policy is added to the file and everything else already exists.

    This is the exact situation #61 was discovered in, and neither an all-new nor an all-existing
    test reproduces it - the bug needs both branches live in one run to show itself.
    """
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
    """A 'cleanup' pass that removes a policy after applying it reproduces #61 from the far end."""
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
    """A runbook whose documented snippet does not parse is a runbook that fails at 3am."""
    try:
        ast.parse(_recipe_python_source())
    except SyntaxError as exc:  # pragma: no cover - the message is the point
        raise AssertionError(
            "The documented apply snippet is not valid Python (%s at line %s)."
            % (exc.msg, exc.lineno)
        ) from exc


def test_prose_states_no_policy_count_that_disagrees_with_the_file():
    """The second half of the original rot: 'holds BOTH policies' over a three-policy file."""
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
