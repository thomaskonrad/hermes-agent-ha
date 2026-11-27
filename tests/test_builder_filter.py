"""Tests for the app filter in .github/workflows/builder.yaml.

The filter decides which apps get built. A manual publish (workflow_dispatch
with publish=true) must build every app, even when the commit changed no app
file. Otherwise the override runs green and publishes nothing.

The test pulls the filter script out of the workflow file and runs it in bash
with the same environment variables GitHub Actions sets, so the workflow file
itself is what is tested.
"""

from __future__ import annotations

import json
import pathlib
import subprocess

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDER = ROOT / ".github" / "workflows" / "builder.yaml"

APPS = "hermes_agent other_app"


def _filter_script() -> str:
    workflow = yaml.safe_load(BUILDER.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["init"]["steps"]
    (step,) = [s for s in steps if s.get("id") == "filter"]
    return step["run"]


def _monitored_files() -> str:
    # MONITORED_FILES is set once at workflow level, not in the filter step.
    workflow = yaml.safe_load(BUILDER.read_text(encoding="utf-8"))
    return workflow["env"]["MONITORED_FILES"]


def _run(*, event: str, publish: str, changed: str) -> list[str]:
    env = {
        "PATH": "/usr/bin:/bin",
        "MONITORED_FILES": _monitored_files(),
        "APPS": APPS,
        "CHANGED_FILES": changed,
        "EVENT_NAME": event,
        "MANUAL_PUBLISH": publish,
        "GITHUB_OUTPUT": "/tmp/_builder_filter_output",
    }
    out = pathlib.Path(env["GITHUB_OUTPUT"])
    out.unlink(missing_ok=True)
    subprocess.run(
        ["bash", "-c", _filter_script()],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    values = dict(line.split("=", 1) for line in out.read_text().splitlines() if "=" in line)
    out.unlink(missing_ok=True)
    return json.loads(values["changed_apps"]) if values.get("changed") == "true" else []


def test_manual_publish_builds_every_app_even_without_app_changes():
    built = _run(event="workflow_dispatch", publish="true", changed="README.md")
    assert built == ["hermes_agent", "other_app"]


def test_manual_run_without_publish_keeps_file_based_selection():
    built = _run(event="workflow_dispatch", publish="false", changed="README.md")
    assert built == []


@pytest.mark.parametrize("changed", ["hermes_agent/config.yaml", "hermes_agent/Dockerfile"])
def test_push_builds_only_the_changed_app(changed):
    built = _run(event="push", publish="false", changed=changed)
    assert built == ["hermes_agent"]


def test_push_without_app_changes_builds_nothing():
    assert _run(event="push", publish="false", changed="README.md") == []
