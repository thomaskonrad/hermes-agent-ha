# AGENTS.md

Guidance for AI coding agents and for humans working on this repository. Read
it before you change anything.

## What this project is

A Home Assistant app repository that runs Hermes Agent (upstream:
NousResearch/hermes-agent) as an app with its dashboard in the Home Assistant
sidebar. The app folder is `hermes_agent/`. The repository root holds the
metadata for the app store.

## Core principles

1. **Least privilege.** The app gets no Supervisor, Home Assistant admin or
   Docker access, no published ports and no privileges. Do not add any of them
   without an explicit, written reason in the pull request.
2. **Upstream stays upstream.** The image is built on the pinned upstream
   Hermes image. Do not patch, fork or vendor upstream sources. Hermes behaviour
   is configured inside Hermes, not by app options.
3. **Two options, first start only.** The app's options seed Hermes' settings
   once. They must never be re-applied on later starts. Do not add new options
   without a strong reason, because every option is a permanent obligation.
4. **Fail closed.** If the access rules or the seeding cannot be determined
   safely, the service must refuse to start. Never fall back to "allow all".
5. **Users, not developers, read the docs.** `hermes_agent/DOCS.md` and
   `hermes_agent/README.md` describe what users see. No internal names
   (milestones, file names, s6 terms) in user-facing text.
6. **Claims need evidence.** If something is not verified on real Home
   Assistant hardware, the documentation must say so. Do not promise backup,
   restore, or specific device behaviour before it has been tested.

## Publishing rules (hard limits)

- **Never publish** images, releases or packages without an explicit instruction
  from the maintainer. Publishing is only possible through a manual
  `workflow_dispatch` of the builder with `publish=true`.
- **Never make the repository public** without an explicit instruction.
- **Never** commit real secrets, tokens, `.env` files, or options files with
  real values. Test fixtures use obvious placeholders such as `FAKE-TEST-…`.
- **Never** delete packages, releases or repositories without an explicit
  instruction.

## Versioning

- The app `version` in `hermes_agent/config.yaml` is the single source of truth
  for what users see and what the Supervisor compares. Bump it only when the
  app changes in a way users can notice.
- Upstream version pins follow the upstream release: app `0.22.5` runs Hermes
  `0.22.5`.
- Use a new version and a changelog entry for every release. Never reuse a
  version number for a different image.

## Testing

Run the checks in [CONTRIBUTING.md](CONTRIBUTING.md#run-the-checks) before you
propose a change. Also run `actionlint` on `.github/workflows/*.yaml` when you
touch a workflow.

Tests that the change makes obsolete must be updated or removed, not skipped.

## Dependencies

Dependabot proposes updates for GitHub Actions, the Docker base image and test
packages. Minor and patch updates merge automatically after the test suite
passes. Major updates need a human decision. Do not bypass that rule.

## How to work in this repository

- Keep changes small and focused, one topic per pull request.
- Update the changelog for anything users will notice.
- When you are not sure, ask, and say what you verified and what you did not.
