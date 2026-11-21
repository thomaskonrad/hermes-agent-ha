"""Render the nginx Supervisor-source allowlist from the container's /etc/hosts.

Only the `supervisor` hosts entry is trusted. Exactly one
distinct, non-loopback, non-multicast, non-unspecified IPv4 address must be
present; anything else is refused so nginx never falls back to `allow all`.

Usage:
    access.py render [HOSTS_FILE]   # prints the nginx include to stdout
Exit status 0 on success, 1 on any refusal (with the reason on stderr).
"""

from __future__ import annotations

import ipaddress
import sys

HOSTS_NAMES = ("supervisor",)


class RefuseError(Exception):
    """The address cannot be trusted; ingress must stay closed."""


def parse_supervisor_addresses(text: str) -> list[str]:
    """Return the IPv4 addresses bound to the supervisor name, in file order."""
    found: list[str] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        address, names = parts[0], parts[1:]
        if any(name in HOSTS_NAMES for name in names):
            found.append(address)
    return found


def validate_address(address: str) -> str:
    try:
        ip = ipaddress.IPv4Address(address)
    except ipaddress.AddressValueError as exc:
        raise RefuseError(f"supervisor entry is not an IPv4 address: {address!r}") from exc
    if ip.is_loopback or ip.is_unspecified or ip.is_multicast or ip.is_link_local:
        raise RefuseError(f"supervisor address is not routable on the ingress network: {ip}")
    return str(ip)


def render(text: str) -> str:
    addresses = parse_supervisor_addresses(text)
    unique = sorted(set(addresses))
    if not unique:
        raise RefuseError("no 'supervisor' entry found in the hosts file")
    if len(unique) != 1:
        raise RefuseError(f"ambiguous 'supervisor' entries: {unique}")
    ip = validate_address(unique[0])
    return f"allow {ip};\ndeny all;\n"


def main(argv: list[str]) -> int:
    if len(argv) not in (1, 2) or argv[0] != "render":
        print("usage: access.py render [HOSTS_FILE]", file=sys.stderr)
        return 2
    hosts_path = argv[1] if len(argv) == 2 else "/etc/hosts"
    try:
        with open(hosts_path, encoding="utf-8") as handle:
            sys.stdout.write(render(handle.read()))
    except (RefuseError, OSError) as exc:
        print(f"[ingress-access] refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
