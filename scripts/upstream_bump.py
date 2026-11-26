#!/usr/bin/env python3
"""Detect a new stable upstream Hermes Agent release and bump the app pin.

Usage:
    upstream_bump.py check            # print the latest stable tag and whether it differs
    upstream_bump.py bump             # rewrite the Dockerfile pin and app version if needed

Exit codes:
    0  success (also when already up to date; see the printed status)
    1  refused: ambiguous or unsafe input (nothing was changed)

Rules (see AGENTS.md):
    * Only the newest stable release is considered: GitHub's "latest" release
      endpoint excludes prereleases and drafts, and canary tags are prereleases.
    * The desktop image index must exist and provide both linux/amd64 and
      linux/arm64, or nothing is changed.
    * The app version is its own scheme, X.Y.Z, and is not the Hermes version.
      A Hermes patch release (0.23.4 -> 0.23.5) bumps Z. A Hermes minor release
      (0.23 -> 0.24) bumps Y and resets Z to 0. A Hermes major change, or a
      version that is not newer, is refused for a maintainer decision.
    * Nothing is published here. This only edits two files.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "hermes_agent" / "Dockerfile"
CONFIG = ROOT / "hermes_agent" / "config.yaml"
UPSTREAM_REPO = "NousResearch/hermes-agent"
IMAGE = "nousresearch/hermes-agent"
STABLE_TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
FROM_LINE = re.compile(
    r"^FROM nousresearch/hermes-agent:v(\d+\.\d+\.\d+)-desktop@sha256:([0-9a-f]{64})$",
    re.MULTILINE,
)
APP_VERSION = re.compile(r'^version: "(\d+\.\d+\.\d+)"$', re.MULTILINE)


class Refused(Exception):
    """Input is ambiguous or unsafe; the caller must not change anything."""


def _get_json(url: str) -> object:
    token = os.environ.get("GH_TOKEN")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-agent-ha"}
    # Compare the parsed host exactly. A substring test would also match a URL
    # such as https://example.invalid/?x=api.github.com and send the token there.
    if token and urllib.parse.urlsplit(url).hostname == "api.github.com":
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
        return json.load(resp)


def latest_stable_upstream() -> str:
    """Return the newest stable tag, e.g. 'v0.23.3'. Refuses unless it is well-formed."""
    release = _get_json(f"https://api.github.com/repos/{UPSTREAM_REPO}/releases/latest")
    if not isinstance(release, dict):
        raise Refused("unexpected response from the releases API")
    if release.get("prerelease") or release.get("draft"):
        raise Refused("latest release is a prerelease or draft; refusing")
    tag = release.get("tag_name", "")
    if not STABLE_TAG.match(tag):
        raise Refused(f"unrecognised stable tag format: {tag!r}")
    return tag


def desktop_index(tag: str) -> str:
    """Return the index digest of <tag>-desktop, if both architectures exist."""
    data = _get_json(f"https://hub.docker.com/v2/repositories/{IMAGE}/tags/{tag}-desktop")
    if not isinstance(data, dict):
        raise Refused("unexpected response from the registry")
    digest = data.get("digest", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise Refused(f"registry returned no index digest for {tag}-desktop")
    archs = {img.get("architecture") for img in data.get("images", [])}
    missing = {"amd64", "arm64"} - archs
    if missing:
        raise Refused(f"{tag}-desktop is missing architectures: {sorted(missing)}")
    return digest.removeprefix("sha256:")


def current_pin() -> tuple[str, str]:
    text = DOCKERFILE.read_text(encoding="utf-8")
    matches = FROM_LINE.findall(text)
    if len(matches) != 1:
        raise Refused(f"expected exactly one pinned FROM line, found {len(matches)}")
    return matches[0]


def current_app_version() -> str:
    matches = APP_VERSION.findall(CONFIG.read_text(encoding="utf-8"))
    if len(matches) != 1:
        raise Refused("expected exactly one app version line in config.yaml")
    return matches[0]


def _triple(text: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", text)
    if not match:
        raise Refused(f"not a X.Y.Z version: {text!r}")
    return (int(match[1]), int(match[2]), int(match[3]))


def next_app_version(app: str, hermes_old: str, hermes_new: str) -> str:
    """Return the app version that follows a Hermes bump. Refuses unsafe steps.

    Hermes patch (0.23.4 -> 0.23.5): app Z + 1.
    Hermes minor (0.23.x -> 0.24.y): app Y + 1, Z reset to 0.
    Hermes major change, or a version that is not newer: refused.
    The app's X is only changed by a maintainer, never here.
    """
    ax, ay, az = _triple(app)
    old = _triple(hermes_old)
    new = _triple(hermes_new)
    if new <= old:
        raise Refused(f"Hermes {hermes_new} is not newer than {hermes_old}")
    if new[0] != old[0]:
        raise Refused(f"Hermes major change {hermes_old} -> {hermes_new} needs a maintainer decision")
    if new[1] != old[1]:
        return f"{ax}.{ay + 1}.0"
    return f"{ax}.{ay}.{az + 1}"


def check() -> int:
    tag = latest_stable_upstream()
    version = tag.removeprefix("v")
    pinned_version, _ = current_pin()
    if version == pinned_version:
        print(f"up-to-date: {version}")
        return 0
    # Refuse here, before a pull request is opened, if the app version has no safe step.
    next_app_version(current_app_version(), pinned_version, version)
    print(f"update-available: {pinned_version} -> {version}")
    return 0


def bump() -> int:
    tag = latest_stable_upstream()
    version = tag.removeprefix("v")
    pinned_version, _ = current_pin()
    if version == pinned_version:
        print(f"up-to-date: {version}")
        return 0
    app_old = current_app_version()
    app_new = next_app_version(app_old, pinned_version, version)
    digest = desktop_index(tag)

    # Compute both new file contents first. Nothing is written unless both
    # rewrites succeed, so a refusal can never leave the two files disagreeing.
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    new_from = f"FROM nousresearch/hermes-agent:v{version}-desktop@sha256:{digest}"
    dockerfile, n = FROM_LINE.subn(new_from, dockerfile)
    if n != 1:
        raise Refused("could not rewrite the FROM line exactly once")

    config = CONFIG.read_text(encoding="utf-8")
    config = APP_VERSION.sub(f'version: "{app_new}"', config)

    DOCKERFILE.write_text(dockerfile, encoding="utf-8")
    CONFIG.write_text(config, encoding="utf-8")
    print(
        f"bumped: Hermes {pinned_version} -> {version}, "
        f"app {app_old} -> {app_new} (index sha256:{digest[:12]}...)"
    )
    return 0


def main(argv: list[str]) -> int:
    if argv not in (["check"], ["bump"]):
        print(__doc__, file=sys.stderr)
        return 1
    try:
        return check() if argv == ["check"] else bump()
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
