"""Static invariants for the ingress proxy config.

Behavioural checks (real nginx, real allowlist, live peers) run in the image
via tests/run-in-image.sh and tests/live_checks.sh. These tests pin the parts
of the config that must never regress silently.
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "hermes_agent"
NGINX = APP / "rootfs" / "etc" / "nginx" / "nginx.conf"
INGRESS = APP / "rootfs" / "etc" / "nginx" / "conf.d" / "ingress.conf"


def test_access_include_is_server_scoped_and_precedes_all_locations():
    text = INGRESS.read_text(encoding="utf-8")
    directive = re.search(r"^\s*include /run/hermes-ingress/supervisor-access\.conf;", text, re.MULTILINE)
    server = re.search(r"^server \{", text, re.MULTILINE)
    first_location = re.search(r"^\s*location\b", text, re.MULTILINE)
    assert directive and server and first_location, "directive, server block and location must exist"
    assert server.start() < directive.start() < first_location.start(), (
        "allowlist must be a server-scoped include that precedes every location"
    )


def test_no_allow_all_anywhere():
    for path in (NGINX, INGRESS):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"^\s*allow\s+all\s*;", text, re.MULTILINE), path


def test_no_real_ip_trust_of_forwarded_headers():
    for path in (NGINX, INGRESS):
        text = path.read_text(encoding="utf-8")
        assert "real_ip_header" not in text, path
        assert "set_real_ip_from" not in text, path


def test_health_is_proxied_only_through_the_same_server():
    text = INGRESS.read_text(encoding="utf-8")
    assert "location = /ha-health" in text
    assert "proxy_pass http://127.0.0.1:9119/api/status;" in text


def test_dashboard_host_and_origin_are_rewritten_for_loopback_guard():
    text = INGRESS.read_text(encoding="utf-8")
    assert "proxy_set_header Host   127.0.0.1:9119;" in text
    assert "proxy_set_header Origin $normalized_origin;" in text


def test_websocket_upgrade_and_long_timeouts_present():
    text = INGRESS.read_text(encoding="utf-8")
    assert "proxy_set_header Upgrade    $http_upgrade;" in text
    assert "proxy_read_timeout 3600s;" in text
    assert "proxy_buffering    off;" in text


def test_sub_filter_pattern_keeps_quote_and_prefix_map_has_no_quote():
    # Regression guard: a doubled quote ("") or root-absolute /assets/ broke lazy chunks.
    ingress = INGRESS.read_text(encoding="utf-8")
    nginx = NGINX.read_text(encoding="utf-8")
    assert "sub_filter '\"assets/' '\"$ingress_asset_prefix';" in ingress
    assert "''      'assets/';" in nginx
    assert 'default "$http_x_ingress_path/assets/";' in nginx


def test_proxy_limits_body_size_like_ha_ingress():
    assert "client_max_body_size 16m;" in INGRESS.read_text(encoding="utf-8")
