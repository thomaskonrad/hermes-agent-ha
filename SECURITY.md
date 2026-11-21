# Security policy

## Reporting a vulnerability

Please **do not** open a public issue for a security problem.

Report it privately through this repository's **Security** tab →
**Report a vulnerability** (GitHub private vulnerability reporting). If that
option is not shown, contact the maintainer directly through the GitHub profile
of the repository owner.

Include:

- The app version (see the app page or `config.yaml`) and your Home Assistant
  and Supervisor versions.
- Steps to reproduce, and what you expected to happen.
- The impact as you understand it.

You can expect an acknowledgement within a few days. Fixes are released as a new
app version. Please give the maintainer a reasonable time to fix the problem
before you disclose it publicly.

## Supported versions

Only the latest published version of this app receives fixes.

## Scope

**In scope:** this app wrapper: the Dockerfile, the ingress proxy and its
access rules, the first-start option seeding, and the packaging.

**Out of scope:** Hermes Agent itself. Report upstream issues to
[Nous Research's Hermes Agent project](https://github.com/NousResearch/hermes-agent).

## Security model and known limits

This app runs an AI agent that can execute commands inside its container and
use any credentials you provide. Read these limits before you install:

- **The dashboard has no second login.** It listens only on the container's
  loopback address. Access is limited by the Supervisor's source address: only
  Home Assistant's Supervisor may reach the proxy. This is a source-address
  check, not cryptographic authentication. A process with privileges on your
  host, or anything able to spoof or intercept network traffic on the shared
  network, can bypass it.
- **Secrets are stored and backed up.** The first-start options are written to
  Hermes' `.env` file in the app's data folder. Backups contain them. Protect
  your backups.
- **The app container is not a sandbox for your whole system.** It has no
  Home Assistant administrator API, no Supervisor API and no Docker access by
  design. It can still do anything inside its own container.

## Supply chain

- The base image is pinned by digest to a specific upstream Hermes release.
- Dependencies (GitHub Actions, Docker base image, test packages) are kept
  current by Dependabot, and minor and patch updates are merged after the test
  suite passes. Major updates are reviewed by hand.
