# Hermes Agent — Home Assistant app (M0, experimental)

A Home Assistant **app repository** that runs
[Hermes Agent](https://github.com/NousResearch/hermes-agent) with its dashboard
in the sidebar via Ingress. Design: [`concepts/public-hermes-agent-ha-app.md`](https://github.com/thomaskonrad/hermes-agent-ha)
(the concept lives in the maintainer's workspace, not in this repo).

> **Status: experimental, private, not published.** This is milestone **M0**
> of the concept (§19): skeleton, metadata, safe bootstrap and proxy access
> control. It is **not** a release. Nothing here has passed the on-device
> gates in concept §16.

## What M0 contains

| Area | Files | Status |
|---|---|---|
| App metadata (Supervisor schema) | `hermes_agent/config.yaml`, `hermes_agent/translations/en.yaml`, `repository.yaml` | tested (`tests/test_metadata.py`) |
| Image | `Dockerfile` (base pinned by index digest to `nousresearch/hermes-agent:v0.22.5-desktop`) | builds `linux/arm64` and `linux/amd64` |
| Ingress proxy | `rootfs/etc/nginx/*`, `rootfs/etc/s6-overlay/.../ingress-proxy` | `nginx -t` in the build; live checks |
| Supervisor-source allowlist | `rootfs/usr/local/lib/hermes-ingress/access.py`, `rootfs/etc/cont-init.d/40-ingress-access` | fail-closed; unit-tested |
| Option seeding (first start only) | `rootfs/etc/cont-init.d/50-hermes-app-options`, `rootfs/usr/local/bin/hermes-app-seed` | tested against the image's real `python-dotenv` |

## Options

Exactly two, both **first-start bootstrap** values (concept §6):

- `openrouter_api_key` — seeds `OPENROUTER_API_KEY` in Hermes' `.env` if absent or empty.
- `ha_token` — seeds `HASS_TOKEN` (and `HASS_URL=http://homeassistant:8123` if absent).

After the first start, changing these fields does **not** change Hermes. A
completion marker (`.hermes-app-bootstrap-done`) prevents reseeding, including
after restore. Manage credentials inside Hermes.

## Security posture (M0)

- No published ports, no `hassio_api` / `homeassistant_api` / `docker_api`, no
  host networking, no privileges, no device access, AppArmor on.
- The dashboard binds loopback. nginx on `:8099` is the only front door and
  allows **only** the Supervisor address from the container's `supervisor`
  hosts entry. Anything else gets `403`, including `/ha-health`.
- No `allow all` fallback. A missing, ambiguous or unroutable supervisor address
  leaves ingress down and logs why.
- Spoofed `X-Ingress-Path`, `X-Forwarded-For` or user headers grant nothing.

**Residual risk, stated plainly:** the allowlist is source-IP based. It is not
cryptographic peer authentication. A privileged app, a host process or anything
able to spoof or intercept traffic on the shared network can bypass it. The
dashboard has no second login because it sits on loopback. Treat the Hermes
terminal and browser as sensitive.

## What M0 does NOT prove (open gates)

These are concept §16 gates. They are **not** claimed by this repository yet:

- The real Supervisor's TCP source address, including the watchdog, on a real
  Home Assistant install (only simulated with a test network here).
- Non-admin denial through HA Ingress, on real Supervisor versions.
- The Bot Screen / browser takeover on either architecture.
- Backup, restore, migration and rollback (concept §7, §13.5, M2).
- Upstream sync, digest promotion and automatic publishing (M3/M4).
- Behaviour on Home Assistant hardware (Yellow / Green / Pi). No device test has run.

## Build and test

Requirements: Docker (arm64 and amd64 build via emulation), Python 3.9+ for the
host test venv.

```sh
python3 -m venv .venv && .venv/bin/pip install pytest pyyaml
.venv/bin/python -m pytest tests/test_metadata.py tests/test_access.py tests/test_ingress_config.py

docker build --platform linux/arm64 -t hermes-agent-ha:m0-arm64 .
docker build --platform linux/amd64 -t hermes-agent-ha:m0-amd64 .

sh tests/wheels-fetch.sh
sh tests/run-in-image.sh hermes-agent-ha:m0-arm64 linux/arm64   # seeder, real dotenv
```

The amd64 build pins the **amd64 child digest** of the same upstream tag,
because the local classic builder does not select a platform from the
multi-arch index. Index pin in the `Dockerfile` remains the source of truth.

## Repository layout

```
repository.yaml              repository name + maintainer
hermes_agent/                the app (config, translations, docs later)
Dockerfile                   the image
rootfs/                      everything copied into the image
tests/                       host tests, in-image seeder tests, live checks
concepts/                    (not here) design document in the maintainer's workspace
```

## Licence

MIT for this wrapper. Hermes Agent is MIT, Copyright (c) 2025 Nous Research.
