"""Tests for scripts/upstream_bump.py: the upstream detector and pin rewriter.

Network calls are replaced with fakes, so these tests are deterministic and do
not depend on the live Docker Hub or GitHub state.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("upstream_bump", ROOT / "scripts" / "upstream_bump.py")
ub = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ub)

DIGEST = "a" * 64
PIN_0_23_2 = (
    'FROM nousresearch/hermes-agent:v0.23.2-desktop@sha256:' + "b" * 64 + "\n"
)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    app = tmp_path / "hermes_agent"
    app.mkdir()
    (app / "Dockerfile").write_text(PIN_0_23_2, encoding="utf-8")
    (app / "config.yaml").write_text('name: x\nversion: "0.23.2"\n', encoding="utf-8")
    monkeypatch.setattr(ub, "DOCKERFILE", app / "Dockerfile")
    monkeypatch.setattr(ub, "CONFIG", app / "config.yaml")
    return app


def _fake_feeds(monkeypatch, tag="v0.23.3", prerelease=False, draft=False,
                archs=("amd64", "arm64"), digest=f"sha256:{DIGEST}"):
    """Route each endpoint to its own fake answer, so both calls can be faked at once."""
    release = {"tag_name": tag, "prerelease": prerelease, "draft": draft}
    index = {"digest": digest, "images": [{"architecture": a} for a in archs]}

    def route(url):
        if "api.github.com" in url:
            return release
        if "hub.docker.com" in url:
            return index
        raise AssertionError(f"unexpected URL in test: {url}")

    monkeypatch.setattr(ub, "_get_json", route)


def _fake_release(monkeypatch, tag, prerelease=False, draft=False):
    _fake_feeds(monkeypatch, tag=tag, prerelease=prerelease, draft=draft)


def _fake_index(monkeypatch, archs=("amd64", "arm64"), digest=f"sha256:{DIGEST}"):
    _fake_feeds(monkeypatch, archs=archs, digest=digest)


def test_newest_stable_release_is_picked(monkeypatch):
    _fake_release(monkeypatch, "v0.23.3")
    assert ub.latest_stable_upstream() == "v0.23.3"


def test_prerelease_is_refused(monkeypatch):
    _fake_release(monkeypatch, "v0.23.4", prerelease=True)
    with pytest.raises(ub.Refused, match="prerelease"):
        ub.latest_stable_upstream()


def test_draft_is_refused(monkeypatch):
    _fake_release(monkeypatch, "v0.23.4", draft=True)
    with pytest.raises(ub.Refused, match="draft"):
        ub.latest_stable_upstream()


@pytest.mark.parametrize("tag", ["v0.23.3+canary.20261120", "rc.1-v0.23.3", "0.23.3", "latest"])
def test_non_stable_tag_formats_are_refused(monkeypatch, tag):
    _fake_release(monkeypatch, tag)
    with pytest.raises(ub.Refused):
        ub.latest_stable_upstream()


def test_index_missing_an_architecture_is_refused(monkeypatch):
    _fake_index(monkeypatch, archs=("arm64",))
    with pytest.raises(ub.Refused, match="missing architectures"):
        ub.desktop_index("v0.23.3")


def test_index_without_digest_is_refused(monkeypatch):
    _fake_index(monkeypatch, digest="")
    with pytest.raises(ub.Refused, match="no index digest"):
        ub.desktop_index("v0.23.3")


def test_bump_rewrites_pin_and_version(repo, monkeypatch):
    _fake_release(monkeypatch, "v0.23.3")
    _fake_index(monkeypatch)
    assert ub.bump() == 0
    text = (repo / "Dockerfile").read_text(encoding="utf-8")
    assert f"FROM nousresearch/hermes-agent:v0.23.3-desktop@sha256:{DIGEST}" in text
    assert 'version: "0.23.3"' in (repo / "config.yaml").read_text(encoding="utf-8")


def test_bump_is_idempotent_when_already_current(repo, monkeypatch):
    _fake_release(monkeypatch, "v0.23.2")
    before = (repo / "Dockerfile").read_text(encoding="utf-8")
    assert ub.bump() == 0
    assert (repo / "Dockerfile").read_text(encoding="utf-8") == before


def test_refusal_changes_nothing(repo, monkeypatch):
    _fake_release(monkeypatch, "v0.23.3")
    _fake_index(monkeypatch, archs=("arm64",))
    before_df = (repo / "Dockerfile").read_text(encoding="utf-8")
    before_cfg = (repo / "config.yaml").read_text(encoding="utf-8")
    with pytest.raises(ub.Refused):
        ub.bump()
    assert (repo / "Dockerfile").read_text(encoding="utf-8") == before_df
    assert (repo / "config.yaml").read_text(encoding="utf-8") == before_cfg
