"""Tests for scripts/upstream_bump.py: the upstream detector, the app version rule and the pin rewriter.

Network calls are replaced with fakes, so these tests are deterministic and do
not depend on the live Docker Hub or GitHub state.
"""

from __future__ import annotations

import importlib.util
import pathlib
import urllib.parse

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("upstream_bump", ROOT / "scripts" / "upstream_bump.py")
ub = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ub)

DIGEST = "a" * 64
PIN_HERMES_0_23_4 = (
    'FROM nousresearch/hermes-agent:v0.23.4-desktop@sha256:' + "b" * 64 + "\n"
)


def _make_repo(tmp_path, monkeypatch, app_version="0.1.0", pin=PIN_HERMES_0_23_4):
    app = tmp_path / "hermes_agent"
    app.mkdir()
    (app / "Dockerfile").write_text(pin, encoding="utf-8")
    (app / "config.yaml").write_text(f'name: x\nversion: "{app_version}"\n', encoding="utf-8")
    monkeypatch.setattr(ub, "DOCKERFILE", app / "Dockerfile")
    monkeypatch.setattr(ub, "CONFIG", app / "config.yaml")
    return app


@pytest.fixture
def repo(tmp_path, monkeypatch):
    return _make_repo(tmp_path, monkeypatch)


def _fake_feeds(monkeypatch, tag="v0.23.5", prerelease=False, draft=False,
                archs=("amd64", "arm64"), digest=f"sha256:{DIGEST}"):
    """Route each endpoint to its own fake answer, so both calls can be faked at once."""
    release = {"tag_name": tag, "prerelease": prerelease, "draft": draft}
    index = {"digest": digest, "images": [{"architecture": a} for a in archs]}

    def route(url):
        host = urllib.parse.urlsplit(url).hostname
        if host == "api.github.com":
            return release
        if host == "hub.docker.com":
            return index
        raise AssertionError(f"unexpected URL in test: {url}")

    monkeypatch.setattr(ub, "_get_json", route)


def _fake_release(monkeypatch, tag, prerelease=False, draft=False):
    _fake_feeds(monkeypatch, tag=tag, prerelease=prerelease, draft=draft)


def _fake_index(monkeypatch, archs=("amd64", "arm64"), digest=f"sha256:{DIGEST}"):
    _fake_feeds(monkeypatch, archs=archs, digest=digest)


# --- upstream detection -----------------------------------------------------

def test_newest_stable_release_is_picked(monkeypatch):
    _fake_release(monkeypatch, "v0.23.5")
    assert ub.latest_stable_upstream() == "v0.23.5"


def test_prerelease_is_refused(monkeypatch):
    _fake_release(monkeypatch, "v0.23.6", prerelease=True)
    with pytest.raises(ub.Refused, match="prerelease"):
        ub.latest_stable_upstream()


def test_draft_is_refused(monkeypatch):
    _fake_release(monkeypatch, "v0.23.6", draft=True)
    with pytest.raises(ub.Refused, match="draft"):
        ub.latest_stable_upstream()


@pytest.mark.parametrize("tag", ["v0.23.5+canary.20261120", "rc.1-v0.23.5", "0.23.5", "latest"])
def test_non_stable_tag_formats_are_refused(monkeypatch, tag):
    _fake_release(monkeypatch, tag)
    with pytest.raises(ub.Refused):
        ub.latest_stable_upstream()


def test_index_missing_an_architecture_is_refused(monkeypatch):
    _fake_index(monkeypatch, archs=("arm64",))
    with pytest.raises(ub.Refused, match="missing architectures"):
        ub.desktop_index("v0.23.5")


def test_index_without_digest_is_refused(monkeypatch):
    _fake_index(monkeypatch, digest="")
    with pytest.raises(ub.Refused, match="no index digest"):
        ub.desktop_index("v0.23.5")


# --- app version rule (the app has its own X.Y.Z scheme) --------------------

@pytest.mark.parametrize(
    "app, hermes_old, hermes_new, expected",
    [
        ("0.1.0", "0.23.4", "0.23.5", "0.1.1"),   # Hermes patch -> app Z + 1
        ("0.1.1", "0.23.4", "0.23.9", "0.1.2"),   # Hermes patch, several releases later
        ("0.1.2", "0.23.4", "0.24.0", "0.2.0"),   # Hermes minor -> app Y + 1, Z reset
        ("0.2.3", "0.24.1", "0.24.2", "0.2.4"),   # patch after a minor, same rule
        ("0.2.3", "0.24.1", "0.25.0", "0.3.0"),   # next Hermes minor
        ("1.4.2", "0.23.4", "0.23.5", "1.4.3"),   # the app's X is kept
    ],
)
def test_app_version_follows_the_scheme(app, hermes_old, hermes_new, expected):
    assert ub.next_app_version(app, hermes_old, hermes_new) == expected


@pytest.mark.parametrize(
    "hermes_new, reason",
    [
        ("1.0.0", "major"),       # major change needs a human decision
        ("0.23.4", "not newer"),  # same version
        ("0.23.3", "not newer"),  # downgrade
    ],
)
def test_unsafe_hermes_steps_are_refused(hermes_new, reason):
    with pytest.raises(ub.Refused, match=reason):
        ub.next_app_version("0.1.0", "0.23.4", hermes_new)


@pytest.mark.parametrize("bad", ["0.1", "v0.1.0", "0.1.0-rc1", "x.y.z"])
def test_malformed_versions_are_refused(bad):
    with pytest.raises(ub.Refused, match="X.Y.Z"):
        ub.next_app_version(bad, "0.23.4", "0.23.5")


# --- pin rewriter -----------------------------------------------------------

def test_bump_rewrites_pin_and_app_patch(repo, monkeypatch):
    _fake_feeds(monkeypatch, tag="v0.23.5")
    assert ub.bump() == 0
    text = (repo / "Dockerfile").read_text(encoding="utf-8")
    assert f"FROM nousresearch/hermes-agent:v0.23.5-desktop@sha256:{DIGEST}" in text
    assert 'version: "0.1.1"' in (repo / "config.yaml").read_text(encoding="utf-8")


def test_bump_to_hermes_minor_bumps_app_minor(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path, monkeypatch, app_version="0.1.3")
    _fake_feeds(monkeypatch, tag="v0.24.0")
    assert ub.bump() == 0
    assert 'version: "0.2.0"' in (repo / "config.yaml").read_text(encoding="utf-8")
    assert "v0.24.0-desktop" in (repo / "Dockerfile").read_text(encoding="utf-8")


def test_bump_refuses_major_and_changes_nothing(repo, monkeypatch):
    _fake_feeds(monkeypatch, tag="v1.0.0")
    before_df = (repo / "Dockerfile").read_text(encoding="utf-8")
    before_cfg = (repo / "config.yaml").read_text(encoding="utf-8")
    with pytest.raises(ub.Refused, match="major"):
        ub.bump()
    assert (repo / "Dockerfile").read_text(encoding="utf-8") == before_df
    assert (repo / "config.yaml").read_text(encoding="utf-8") == before_cfg


def test_check_refuses_major_before_a_proposal_is_opened(repo, monkeypatch):
    _fake_release(monkeypatch, "v1.0.0")
    with pytest.raises(ub.Refused, match="major"):
        ub.check()


def test_bump_is_idempotent_when_already_current(repo, monkeypatch):
    _fake_release(monkeypatch, "v0.23.4")
    before_df = (repo / "Dockerfile").read_text(encoding="utf-8")
    before_cfg = (repo / "config.yaml").read_text(encoding="utf-8")
    assert ub.bump() == 0
    assert (repo / "Dockerfile").read_text(encoding="utf-8") == before_df
    assert (repo / "config.yaml").read_text(encoding="utf-8") == before_cfg


def test_refusal_changes_nothing(repo, monkeypatch):
    _fake_feeds(monkeypatch, tag="v0.23.5", archs=("arm64",))
    before_df = (repo / "Dockerfile").read_text(encoding="utf-8")
    before_cfg = (repo / "config.yaml").read_text(encoding="utf-8")
    with pytest.raises(ub.Refused):
        ub.bump()
    assert (repo / "Dockerfile").read_text(encoding="utf-8") == before_df
    assert (repo / "config.yaml").read_text(encoding="utf-8") == before_cfg


# --- token handling ---------------------------------------------------------

@pytest.mark.parametrize(
    "url, sends_token",
    [
        ("https://api.github.com/repos/NousResearch/hermes-agent/releases/latest", True),
        # A substring match would have sent the token to these hosts.
        ("https://example.invalid/?x=api.github.com", False),
        ("https://api.github.com.example.invalid/releases", False),
    ],
)
def test_token_is_sent_only_to_the_github_api(monkeypatch, url, sends_token):
    monkeypatch.setenv("GH_TOKEN", "FAKE-TEST-GH-TOKEN")
    seen = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(request, timeout):
        seen["auth"] = request.get_header("Authorization")
        return _Resp()

    monkeypatch.setattr(ub.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(ub.json, "load", lambda resp: {})
    ub._get_json(url)
    if sends_token:
        assert seen["auth"] == "Bearer FAKE-TEST-GH-TOKEN"
    else:
        assert seen["auth"] is None
