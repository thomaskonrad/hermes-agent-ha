"""Unit tests for the Supervisor-source allowlist renderer (concept §9.5).

Pure logic, no Docker. The renderer must fail closed: anything other than a
single, routable IPv4 `supervisor` entry is refused.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "hermes_agent"
ACCESS_PATH = APP / "rootfs" / "usr" / "local" / "lib" / "hermes-ingress" / "access.py"

_spec = importlib.util.spec_from_file_location("access", ACCESS_PATH)
access = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(access)


def test_renders_single_supervisor_address():
    hosts = "127.0.0.1\tlocalhost\n172.30.32.2\tsupervisor hassio\n"
    assert access.render(hosts) == "allow 172.30.32.2;\ndeny all;\n"


def test_ignores_comments_and_unrelated_names():
    hosts = "# supervisor is commented\n172.30.32.2 supervisor # comment\n172.17.0.4 98e3e153ed4a\n"
    assert access.render(hosts) == "allow 172.30.32.2;\ndeny all;\n"


def test_duplicate_identical_entry_is_accepted():
    hosts = "172.30.32.2 supervisor\n172.30.32.2 hassio supervisor\n"
    assert access.render(hosts) == "allow 172.30.32.2;\ndeny all;\n"


def test_missing_entry_fails_closed():
    with pytest.raises(access.RefuseError, match="no 'supervisor' entry"):
        access.render("127.0.0.1 localhost\n172.17.0.4 abcdef\n")


def test_ambiguous_entries_fail_closed():
    with pytest.raises(access.RefuseError, match="ambiguous"):
        access.render("172.30.32.2 supervisor\n172.30.32.3 supervisor\n")


@pytest.mark.parametrize(
    "address",
    ["127.0.0.1", "0.0.0.0", "224.0.0.1", "169.254.1.1", "::1", "fe80::1", "not-an-ip"],
)
def test_unroutable_or_invalid_address_fails_closed(address):
    with pytest.raises(access.RefuseError):
        access.render(f"{address} supervisor\n")


def test_no_allow_all_is_ever_emitted():
    out = access.render("172.30.32.2 supervisor\n")
    assert "allow all" not in out
    assert out.splitlines()[-1] == "deny all;"


def test_cli_refuses_with_nonzero_status(tmp_path, capsys):
    hosts = tmp_path / "hosts"
    hosts.write_text("127.0.0.1 localhost\n")
    assert access.main(["render", str(hosts)]) == 1
    assert "refused" in capsys.readouterr().err


def test_cli_renders_to_stdout(tmp_path, capsys):
    hosts = tmp_path / "hosts"
    hosts.write_text("172.30.32.2 supervisor\n")
    assert access.main(["render", str(hosts)]) == 0
    assert capsys.readouterr().out == "allow 172.30.32.2;\ndeny all;\n"
