"""Option seeding tests.

These import the real seeder and run it with the image's own python-dotenv,
so the round-trip assertions use the same parser Hermes uses at runtime.
Run inside the pinned image (see tests/run-in-image.sh). Without python-dotenv
the whole module is skipped rather than silently passing.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import os
import pathlib
import stat

import pytest

pytest.importorskip("dotenv", reason="needs python-dotenv (run inside the pinned image)")
from dotenv.main import DotEnv  # noqa: E402
from dotenv.variables import parse_variables  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "hermes_agent"
SEED_PATH = APP / "rootfs" / "usr" / "local" / "bin" / "hermes-app-seed"
_loader = importlib.machinery.SourceFileLoader("hermes_app_seed", str(SEED_PATH))
_spec = importlib.util.spec_from_loader("hermes_app_seed", _loader)
seed = importlib.util.module_from_spec(_spec)
_loader.exec_module(seed)


def hermes_read(path: pathlib.Path) -> dict:
    """Read a .env exactly as Hermes does (interpolate=False, then ${VAR} resolution)."""
    text = path.read_text(encoding="utf-8")
    out = {}
    for name, value in DotEnv(dotenv_path=None, stream=io.StringIO(text), interpolate=False).parse():
        if name is not None and value is not None:
            out[name] = "".join(atom.resolve({}) for atom in parse_variables(value))
    return out


@pytest.fixture
def home(tmp_path):
    return tmp_path


def test_blank_first_start_writes_marker_and_empty_env(home):
    assert seed.seed({"openrouter_api_key": "", "ha_token": ""}, home) == "nothing-to-add"
    assert (home / seed.MARKER_NAME).exists()
    assert (home / seed.ENV_NAME).read_text() == ""


def test_blank_first_start_does_not_reseed_on_later_start(home):
    seed.seed({"openrouter_api_key": "", "ha_token": ""}, home)
    assert seed.seed({"openrouter_api_key": "sk-new"}, home) == "already-done"
    assert hermes_read(home / seed.ENV_NAME) == {}


def test_openrouter_key_is_seeded_and_round_trips(home):
    key = "FAKE-TEST-OPENROUTER-KEY"
    assert seed.seed({"openrouter_api_key": key}, home) == "seeded"
    assert hermes_read(home / seed.ENV_NAME)["OPENROUTER_API_KEY"] == key


def test_ha_token_seeds_token_and_default_url(home):
    token = "FAKE-TEST-HA-TOKEN"
    seed.seed({"ha_token": token}, home)
    got = hermes_read(home / seed.ENV_NAME)
    assert got["HASS_TOKEN"] == token
    assert got["HASS_URL"] == "http://homeassistant:8123"


@pytest.mark.parametrize(
    "value",
    [
        "plain",
        "with space and # hash",
        "back\\slash\\\\double",
        "it's a \"quote\"",
        "dollar $HOME and $ alone",
        "eq=sign==two",
        "unicode-äöü-€",
        "  padded  ",
        "trailing-backslash\\",
        "\\$already",
    ],
)
def test_special_characters_round_trip_exactly(home, value):
    seed.seed({"openrouter_api_key": value}, home)
    assert hermes_read(home / seed.ENV_NAME)["OPENROUTER_API_KEY"] == value


def test_value_with_variable_reference_is_refused_not_changed(home):
    with pytest.raises(seed.SeedError, match="variable reference"):
        seed.seed({"openrouter_api_key": "sk-${HOME}"}, home)
    assert not (home / seed.MARKER_NAME).exists()
    assert not (home / seed.ENV_NAME).exists()


@pytest.mark.parametrize("bad", ["line1\nline2", "cr\rvalue", "nul\x00byte"])
def test_line_break_or_nul_is_refused(home, bad):
    with pytest.raises(seed.SeedError):
        seed.seed({"ha_token": bad}, home)
    assert not (home / seed.MARKER_NAME).exists()


def test_non_string_option_is_refused(home):
    with pytest.raises(seed.SeedError, match="not a string"):
        seed.seed({"openrouter_api_key": 123}, home)



def test_failed_env_write_leaves_no_marker_so_retry_is_possible(home, monkeypatch):
    def boom(src, dst):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(seed.os, "replace", boom)
    with pytest.raises(seed.SeedError):
        seed.seed({"openrouter_api_key": "k"}, home)
    assert not (home / seed.MARKER_NAME).exists()
    assert not (home / seed.ENV_NAME).exists()

    monkeypatch.undo()
    assert seed.seed({"openrouter_api_key": "k"}, home) == "seeded"
    assert (home / seed.MARKER_NAME).exists()



def test_nonempty_existing_value_wins(home):
    (home / seed.ENV_NAME).write_text("OPENROUTER_API_KEY='user-key'\n")
    seed.seed({"openrouter_api_key": "option-key"}, home)
    assert hermes_read(home / seed.ENV_NAME)["OPENROUTER_API_KEY"] == "user-key"


def test_empty_existing_assignment_is_filled(home):
    (home / seed.ENV_NAME).write_text("OPENROUTER_API_KEY=\nOTHER='keep'\n")
    seed.seed({"openrouter_api_key": "option-key"}, home)
    got = hermes_read(home / seed.ENV_NAME)
    assert got["OPENROUTER_API_KEY"] == "option-key"
    assert got["OTHER"] == "keep"


def test_existing_lines_are_preserved_byte_for_byte(home):
    original = "# my comment\nFOO='bar'\nexport BAZ=qux\n"
    (home / seed.ENV_NAME).write_text(original)
    seed.seed({"openrouter_api_key": "k"}, home)
    assert (home / seed.ENV_NAME).read_text().startswith(original)


def test_existing_hass_url_is_not_overwritten(home):
    (home / seed.ENV_NAME).write_text("HASS_URL='http://custom:8123'\n")
    seed.seed({"ha_token": "t"}, home)
    assert hermes_read(home / seed.ENV_NAME)["HASS_URL"] == "http://custom:8123"


def test_env_is_written_mode_0600(home):
    seed.seed({"openrouter_api_key": "k"}, home)
    assert stat.S_IMODE(os.stat(home / seed.ENV_NAME).st_mode) == 0o600


def test_symlinked_env_is_refused(home, tmp_path):
    target = tmp_path / "elsewhere"
    target.write_text("")
    (home / seed.ENV_NAME).symlink_to(target)
    with pytest.raises(seed.SeedError):
        seed.seed({"openrouter_api_key": "k"}, home)
    assert target.read_text() == ""


def test_non_regular_env_is_refused(home):
    (home / seed.ENV_NAME).mkdir()
    with pytest.raises(seed.SeedError):
        seed.seed({"openrouter_api_key": "k"}, home)


def test_restored_marker_prevents_reseeding(home):
    (home / seed.MARKER_NAME).write_text("1\n")
    assert seed.seed({"openrouter_api_key": "new"}, home) == "already-done"
    assert not (home / seed.ENV_NAME).exists()


def test_error_messages_never_contain_the_secret(home):
    secret = "FAKE-SECRET-VALUE-${HOME}"
    with pytest.raises(seed.SeedError) as exc:
        seed.seed({"openrouter_api_key": secret}, home)
    assert "SECRET" not in str(exc.value)
