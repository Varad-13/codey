# Installation

## Requirements

- **Python 3.7 or newer** (Python 3.10+ recommended; the wheel is pure Python).
- **`pip`** (any recent version).
- **An OpenAI-compatible API key** — either OpenAI (`sk-proj-…`) or OpenRouter (`sk-or-…`). See [configuration.md](configuration.md) for details.
- **~120 MB of disk space** for the Playwright Chromium browser that powers the `web` tool. It auto-downloads the first time the tool is invoked; you can also pre-install it.

### Platform notes

| Platform | Status |
|---|---|
| Linux (x86_64, aarch64) | ✅ Fully supported |
| macOS (Intel & Apple Silicon) | ✅ Fully supported |
| Windows 10 / 11 | ✅ Fully supported. PowerShell is used for the `terminal` tool; the `shell` tool picks PowerShell automatically on Windows. |

## Install from a GitHub Release wheel (recommended)

Codey isn't published to PyPI — install it from a GitHub Release or from a local source checkout.

1. Visit the [Releases page](https://github.com/Varad-13/codey/releases).
2. Download the `codey-<version>-py3-none-any.whl` asset.
3. Install it:

   ```bash
   pip install ./codey-<version>-py3-none-any.whl
   ```

This pulls in the runtime dependencies: `openai`, `python-dotenv`, `prompt_toolkit`, `playwright`, `Pillow`.

### Pre-install the browser

The `web` tool needs Chromium. `setup.py` runs `playwright install chromium` automatically after `pip install <wheel>`, but if that step was skipped (or fails), run it manually:

```bash
playwright install chromium
```

You should see a single ~120 MB download the first time.

## Install for development

```bash
git clone https://github.com/Varad-13/codey.git
cd codey
pip install -e .
playwright install chromium
```

Editable installs also trigger the Chromium download via `setup.py`. See [contributing.md](contributing.md) for the rest of the dev workflow.

## Configure your API key

Create a `.env` file in the project directory you'll be working in (or in your home directory for a global default):

```dotenv
OPENAI_API_KEY=sk-or-v1-...
```

Or export it in your shell. See [configuration.md](configuration.md) for the full list of environment variables, including `PROVIDER` overrides and `ENABLED_TOOLS` allowlists.

## Verify the install

```bash
codey --version
# -> codey 0.4.3

codey
# -> session picker, then the chat prompt
```

If `codey` isn't on your `PATH`, run it as a module: `python -m codey`. Or activate the virtualenv where you installed it.

## Upgrading

```bash
codey update
```

This queries the GitHub Releases API for the latest tag, finds the matching wheel asset, verifies its SHA-256 against the GitHub `digest` field, prompts for confirmation, and runs `pip install --upgrade` on it. Exit code is `0` when already current or updated successfully; `1` for genuine failures (network, hash mismatch, pip error, or user cancellation).

## Uninstalling

```bash
pip uninstall codey
# optionally:
playwright uninstall chromium
rm -rf ~/.codey        # session history
```

## Troubleshooting

- **`NoConsoleScreenBufferError` on Windows when running non-interactively** — fixed in this codebase. The `prompt_toolkit.PromptSession` is constructed lazily, so `codey --version` and `codey update` work from CI / piped input.
- **Browser fails to launch** — re-run `playwright install chromium`. If you're on a headless server, set `CODEY_WEB_HEADLESS=true`.
- **`UnicodeDecodeError` from `shell` / `terminal` on Windows** — Codey's tool layer uses `encoding_safety.safe_decode` and never raises from decoding. If you still see this, please file an issue with the failing command.
- **Update check hangs** — set `CODEY_NO_UPDATE_CHECK=1` to disable it.
- **First-run is slow** — Chromium download. Set `CODEY_NO_UPDATE_CHECK=1` to skip the GitHub check at startup.