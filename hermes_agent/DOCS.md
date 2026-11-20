# Home Assistant App: Hermes Agent

> **Experimental.** This version has not been tested on a real Home Assistant
> installation yet. Expect rough edges and possible changes.

Hermes Agent is a self-hosted AI agent. This app runs it on your Home Assistant
and adds a **Hermes Agent** entry to your sidebar, where you use the Hermes
dashboard.

## Install

1. Settings → Apps → Install app → ⋮ → Repositories, then add the repository URL.
2. Install **Hermes Agent**.
3. Optional: on the Configuration tab, enter an OpenRouter API key and/or a
   Home Assistant token **before the first start** (see below).
4. Start the app and open **Hermes Agent** in the sidebar.

## Requirements

- Home Assistant OS or Supervised, 64-bit (aarch64 or amd64).
- At least about 1.5 GB free memory and about 4 GB free disk for the app image,
  plus space for your data. These are estimates.
- A model provider, such as OpenRouter.

## Options

Both options are used **only on the first start**.

| Option | What it does |
|---|---|
| `openrouter_api_key` | Optional. Written to Hermes' settings if no key is set yet. |
| `ha_token` | Optional. A long-lived Home Assistant access token. Written to Hermes' settings if no token is set yet. Use a dedicated non-admin user. |

After the first start, changing these fields does **not** change Hermes. Manage
credentials inside Hermes. Clearing the fields does not remove credentials that
were already written.

## Security

- The app publishes no ports. The panel is reachable only through Home
  Assistant's sidebar.
- Access is limited to Home Assistant's Supervisor. Other apps on the network
  cannot open the dashboard.
- The app has no access to the Home Assistant API as an administrator, to the
  Supervisor, or to Docker.
- Credentials are stored in the app's data folder and are included in backups.
  Treat backups as sensitive.
- Hermes can run commands inside the app container. It is not a sandbox for
  your Home Assistant host.

## Known limitations

- Experimental: not yet verified on Home Assistant hardware.
- Backups and restores are not yet verified.

## Help and bugs

Report problems in the repository's issue tracker. Upstream Hermes behaviour
belongs to the Hermes project.

## License

MIT for this app wrapper. Hermes Agent is MIT, copyright Nous Research.
