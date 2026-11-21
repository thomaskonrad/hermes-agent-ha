# Contributing

Thanks for helping! This project packages Hermes Agent for Home Assistant. The
app's behaviour is decided by the checks below, so please run them before you
open a pull request.

## Set up

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

You need Docker to build the image and to run the in-image tests.

## Run the checks

```sh
# 1. Official app linter, the same version CI uses (action-app-linter v2.21)
git clone --depth 1 --branch v2.21 https://github.com/frenck/action-app-linter.git /tmp/al
docker build -t local/app-linter:2.21 /tmp/al/src
docker run --rm -v "$PWD:/github/workspace" -w /github/workspace \
  -e INPUT_PATH=./hermes_agent -e INPUT_COMMUNITY=false local/app-linter:2.21
# 2. Host tests (metadata, allowlist, ingress config)
.venv/bin/python -m pytest tests/test_metadata.py tests/test_access.py tests/test_ingress_config.py
# 3. Build the image for both architectures
docker build --platform linux/arm64 -t hermes-agent-ha:dev-arm64 hermes_agent
docker build --platform linux/amd64 -t hermes-agent-ha:dev-amd64 hermes_agent
# 4. Seeder tests, run inside the image so they use its real python-dotenv
sh tests/wheels-fetch.sh
sh tests/run-in-image.sh hermes-agent-ha:dev-arm64 linux/arm64
```

CI runs all of these on every pull request. The `Tests` and `Lint` jobs must
pass.

## Pull requests

- Keep changes focused. One topic per pull request.
- Add or update a test for any behaviour change.
- Update `hermes_agent/CHANGELOG.md` for anything users will notice.
- Do not change the Hermes Agent version pin without also updating the
  documentation and the changelog.
- Do not commit secrets, `.env` files, tokens or options fixtures with real
  values.

## Ground rules

- **Least privilege.** The app gets no Supervisor, Home Assistant admin or
  Docker access. New permissions need a clear reason in the pull request.
- **Documentation is for users.** Write `hermes_agent/DOCS.md` for people who
  run Home Assistant, not for developers. Avoid internal names in user-facing
  text.
- **Claims need evidence.** If something is not verified on a real Home
  Assistant installation, say so in the documentation.

## Security issues

Do not open a public issue for a vulnerability. See [SECURITY.md](SECURITY.md).

## Code of conduct

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
