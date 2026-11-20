"""Metadata invariants for the Home Assistant app (concept §10, §13.4 Metadata).

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
    # Concept §10.1: stays experimental until every §16 release gate is closed.
    assert _config()["stage"] == "experimental"


def test_hardening_is_the_safest_value():
    cfg = _config()
    for key in ("host_network", "host_pid", "host_ipc", "host_dbus", "hassio_api",
                "homeassistant_api", "docker_api", "full_access"):
        assert cfg[key] is False, key
    assert cfg["privileged"] == []
    assert cfg["devices"] == []
    assert cfg["apparmor"] is True


def test_no_published_ports_or_webui():
    cfg = _config()
    assert "ports" not in cfg
    assert "webui" not in cfg
    assert cfg["ingress"] is True
    assert cfg["ingress_port"] == 8099


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


def test_watchdog_targets_health_on_ingress_port():
    assert _config()["watchdog"] == "http://[HOST]:[PORT:8099]/ha-health"


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
