# Hermes Agent for Home Assistant

Run [Hermes Agent](https://github.com/NousResearch/hermes-agent), a self-hosted
AI agent, on your Home Assistant. It adds **Hermes Agent** to your sidebar.

> **Experimental.** Not yet tested on a real Home Assistant installation. Read
> [the documentation](hermes_agent/DOCS.md) before you install.

## Install

The quickest way: click the button, which opens your Home Assistant with this
repository already filled in.

[![Open your Home Assistant instance and show the add app repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fthomaskonrad%2Fhermes-agent-ha)

Or do it by hand:

1. In Home Assistant, go to **Settings → Apps → Install app**.
2. Open the ⋮ menu (top right) and choose **Repositories**.
3. Add this URL and close the dialog:

   ```
   https://github.com/thomaskonrad/hermes-agent-ha
   ```

4. Find **Hermes Agent** in the store, install it, and start it.
5. Open **Hermes Agent** from the sidebar.

Full setup, options and troubleshooting are in
[the documentation](hermes_agent/DOCS.md).

## What you need

- Home Assistant OS or Supervised, on a 64-bit system (aarch64 or amd64).
- About 1.5 GB of free memory and about 4 GB of free disk space for the app.
- A model provider, such as [OpenRouter](https://openrouter.ai).

## Support

- Questions and bugs: open an issue in this repository.
- Hermes Agent itself (features, providers, messaging): see the
  [Hermes documentation](https://hermes-agent.nousresearch.com/docs).

## About this project

This is an unofficial packaging of Hermes Agent for Home Assistant. It is not
made by or affiliated with Nous Research.

It was built with the help of an AI coding agent (Cline), and
reviewed and maintained by a human. Changes are tested before they are merged,
but treat the app as experimental.

- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)

## License

This app wrapper is licensed as described in [LICENSE](LICENSE). Hermes Agent
is licensed by Nous Research; see [NOTICE](NOTICE) for attribution.
