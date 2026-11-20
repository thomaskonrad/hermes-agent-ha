# Hermes Agent

> **Experimental.** This version has not been tested on a real Home Assistant
> installation yet. Expect rough edges, and back up your Home Assistant before
> you install.

Hermes Agent is a self-hosted AI agent. It chats with you, remembers things,
learns skills, runs scheduled jobs and can use a browser. This app runs it on
your Home Assistant and adds **Hermes Agent** to your sidebar, where you use
the Hermes dashboard.

## Before you install

You need:

- Home Assistant OS or Supervised, on a 64-bit system (aarch64 or amd64).
- About 1.5 GB of free memory and about 4 GB of free disk space for the app.
  These are estimates. More memory helps if you use the browser.
- A model provider. OpenRouter is the easiest choice: create a key at
  [openrouter.ai](https://openrouter.ai). You can also add a provider later,
  inside the Hermes dashboard.

## Install

1. Go to **Settings → Apps → Install app**.
2. Open the ⋮ menu (top right) and choose **Repositories**.
3. Add `https://github.com/thomaskonrad/hermes-agent-ha` and close the dialog.
4. Open **Hermes Agent** in the store and select **Install**.
5. Before you start it, set the options (see below). This is optional.
6. Select **Start**. The first start takes a minute or two, especially on a
   Raspberry Pi. The panel is ready when it loads.
7. Open **Hermes Agent** from the sidebar.

## Options

There are two options. Both are read **only on the first start**.

| Option | What to enter |
|---|---|
| **OpenRouter API key** | Your OpenRouter key. Leave it empty to choose a provider in the dashboard instead. |
| **Home Assistant token** | A long-lived access token from Home Assistant. Lets Hermes control your devices. Use a dedicated user that is not an administrator. |

To create a Home Assistant token, go to your user profile → **Security** →
**Long-lived access tokens**, then create one.

**Important:** after the first start, changing these fields does **not** change
Hermes. Manage your keys and tokens inside Hermes instead. Clearing the fields
does not remove keys that Hermes already saved.

## Using Hermes

Everything else is configured inside Hermes itself, in the dashboard:

- **Model and provider:** Settings, then Model. You can also use the Chat tab.
- **Messaging (Telegram, Discord, and others):** Messaging. Restart the gateway
  from the Chat tab after you change it.
- **Scheduled jobs:** the cron section of the dashboard.
- **Browser:** the Screen pane lets you take over the browser to log in to
  websites yourself. The agent then uses the same session.

For full documentation of Hermes, see the
[Hermes documentation](https://hermes-agent.nousresearch.com/docs).

## Backups and updates

- The app is designed to be backed up as a whole, including your Hermes
  settings, memories, skills, scheduled jobs and browser logins. **Backups contain secrets** such as
  API keys and tokens, so store them somewhere safe.
- Restoring a backup is intended to bring back the app's data as it was.
- Backup and restore have **not yet been tested** on a real installation.
- Updates are published as new versions of this app. Read the changelog first.

## Security

- The app opens no ports on your network. The panel is reachable only through
  the Home Assistant sidebar.
- Only Home Assistant's own Supervisor can reach the dashboard. Other apps and
  devices on your network are refused.
- The app has no administrator access to Home Assistant, to the Supervisor, or
  to Docker.
- Hermes can run commands inside the app's container, and it can use any
  credentials you give it. The container is not a sandbox for your whole system,
  so only give it the access you are comfortable with.
- Use a non-administrator Home Assistant user for the token.

## Troubleshooting

**The sidebar panel shows an error or is blank right after start.**
Wait a minute. On first start Hermes sets itself up. If it still fails, open the
app's **Log** tab. It names the problem, for example that the Supervisor
address could not be determined. Include that message when you report the issue.

**The app will not start.**
Check the **Log** tab for the first error. Restart the app once after fixing
the problem.

**I changed an option and nothing happened.**
That is expected after the first start. Change the setting inside Hermes.

## Known limitations

- Experimental: not yet verified on real Home Assistant installations.
- Backup and restore are not yet verified.
- Messaging connectors that need inbound web access (webhooks) do not work
  with this app, because the app opens no ports.

## Support and bugs

Report problems on this repository's issue tracker. Questions about Hermes
itself belong to the Hermes project.

## License

MIT for this app wrapper. Hermes Agent is MIT, copyright Nous Research.
