"""Metadata invariants for the Home Assistant app.

Checks the app manifest against the Supervisor schema rules verified in
supervisor/apps/validate.py (2026-11-02): data mapping, hardening defaults,
no published ports, and the experimental stage.
"""

from __future__ import annotations

import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "hermes_agent"


def _config() -> dict:
    return yaml.safe_load((APP / "config.yaml").read_text(encoding="utf-8"))


def test_stage_is_experimental_for_m0():
    # Stays experimental until the app is verified on real Home Assistant installations.
    assert _config()["stage"] == "experimental"


# The official linter flags keys that equal their default, so the hardening
# defaults are not written out. These tests assert the *absence* of each
# privilege key (the Supervisor default is the safe value) and that no key
# requests a privilege.
_PRIVILEGE_KEYS = (
    "host_network", "host_pid", "host_ipc", "host_dbus", "hassio_api",
    "homeassistant_api", "docker_api", "full_access", "apparmor_disabled",
)


def test_no_privilege_is_requested():
    cfg = _config()
    for key in _PRIVILEGE_KEYS:
        assert key not in cfg or cfg[key] in (False, None), key
    assert cfg.get("privileged", []) == []
    assert cfg.get("devices", []) == []
    assert cfg.get("apparmor", True) is True


def test_no_published_ports_or_webui():
    cfg = _config()
    assert "ports" not in cfg
    assert "webui" not in cfg
    assert cfg["ingress"] is True


def test_data_is_mounted_at_upstream_path_only():
    cfg = _config()
    assert cfg["map"] == [{"type": "data", "path": "/opt/data", "read_only": False}]


def test_backup_is_cold():
    assert _config()["backup"] == "cold"


def test_only_two_bootstrap_options():
    cfg = _config()
    assert set(cfg["options"]) == {"openrouter_api_key", "ha_token"}
    assert cfg["schema"] == {"openrouter_api_key": "password?", "ha_token": "password?"}


def test_arch_is_64_bit_only():
    assert set(_config()["arch"]) == {"aarch64", "amd64"}


def test_watchdog_key_is_removed_and_healthcheck_owns_liveness():
    # The linter reports `watchdog` as obsolete; liveness moved to a Dockerfile
    # HEALTHCHECK that probes the dashboard on loopback (see Dockerfile).
    assert "watchdog" not in _config()
    dockerfile = (APP / "Dockerfile").read_text(encoding="utf-8")
    assert "HEALTHCHECK" in dockerfile
    assert "http://127.0.0.1:9119/api/status" in dockerfile


def test_translations_cover_every_option():
    translations = yaml.safe_load((APP / "translations" / "en.yaml").read_text(encoding="utf-8"))
    options = set(_config()["options"])
    assert set(translations["configuration"]) == options
    for key in options:
        assert translations["configuration"][key]["name"]
        assert translations["configuration"][key]["description"]


def test_dockerfile_base_is_pinned_by_digest():
    text = (APP / "Dockerfile").read_text(encoding="utf-8")
    from_lines = [line for line in text.splitlines() if line.startswith("FROM ")]
    assert len(from_lines) == 1
    assert re.search(r"@sha256:[0-9a-f]{64}$", from_lines[0]), from_lines[0]


def test_repository_yaml_present():
    repo = yaml.safe_load((ROOT / "repository.yaml").read_text(encoding="utf-8"))
    assert repo["name"] == "Hermes Agent"
    assert repo["url"].startswith("https://github.com/")


def test_app_version_uses_own_scheme():
    # X.Y.Z of the app itself (AGENTS.md, Versioning), not the Hermes version.
    assert re.fullmatch(r"\d+\.\d+\.\d+", _config()["version"])


def test_changelog_has_an_entry_for_the_app_version():
    version = _config()["version"]
    changelog = (APP / "CHANGELOG.md").read_text(encoding="utf-8")
    assert re.search(rf"^## {re.escape(version)}$", changelog, re.MULTILINE), version
