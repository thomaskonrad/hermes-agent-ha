#!/usr/bin/env python3
"""Pin third-party GitHub Actions to full commit SHAs, keeping the version as a comment.

Each SHA below was resolved from the upstream repository with the GitHub API
(see the commit that added this script). Dependabot's github-actions ecosystem
keeps SHA pins current and writes the new version in the trailing comment.

Usage: pin_actions.py          (rewrites .github/workflows/*.yaml in place)
"""

from __future__ import annotations

import pathlib
import re
import sys

PINS = {
    "actions/checkout@v7.0.1": ("3d3c42e5aac5ba805825da76410c181273ba90b1", "v7.0.1"),
    "actions/create-github-app-token@v2": ("fee1f7d63c2ff003460e3d139729b119787bc349", "v2"),
    "actions/setup-python@v7": ("6d4fd22b20465ccc0f7354476588e8df7c9ca0e0", "v7"),
    "docker/build-push-action@v7": ("c3c9e263c25d99ce0380d002d59b67737d91b0dc", "v7"),
    "docker/setup-buildx-action@v4": ("f87e5991a6d7451dcb8d9637bfbc97413f497069", "v4"),
    "frenck/action-addon-linter@v2.21": ("d51677290aef26cdfc835271dd3c7343ce502809", "v2.21"),
    "tj-actions/changed-files@v47": ("24d32ffd492484c1d75e0c0b894501ddb9d30d62", "v47"),
    "home-assistant/builder/actions/build-image@2026.09.0": ("7412f0023ea9b6e58e8bb5059f1660f51376f49a", "2026.09.0"),
    "home-assistant/builder/actions/prepare-multi-arch-matrix@2026.09.0": ("7412f0023ea9b6e58e8bb5059f1660f51376f49a", "2026.09.0"),
    "home-assistant/builder/actions/publish-multi-arch-manifest@2026.09.0": ("7412f0023ea9b6e58e8bb5059f1660f51376f49a", "2026.09.0"),
    "home-assistant/actions/helpers/find-addons@master": ("07f46fd2e19967768b5fd3000f91f857452b767c", "master"),
    "home-assistant/actions/helpers/info@master": ("07f46fd2e19967768b5fd3000f91f857452b767c", "master"),
}


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[1] / ".github" / "workflows"
    total = 0
    for path in sorted(root.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        for ref, (sha, label) in PINS.items():
            name, _, _ = ref.partition("@")
            pattern = re.compile(r"uses: " + re.escape(ref) + r"(?=\s|$)", re.MULTILINE)
            count = len(pattern.findall(text))
            if count:
                text = pattern.sub(f"uses: {name}@{sha} # {label}", text)
                total += count
        path.write_text(text, encoding="utf-8")
    print(f"pinned {total} references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
