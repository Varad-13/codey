# Codey

**Codey** is an in-terminal AI coding assistant. It runs an OpenAI-compatible chat model with a tool layer that can read files, edit code, run shell commands, browse the web, drive interactive CLIs, manage git, and spawn focused subagents — all from a single REPL in your terminal.

- Website: <https://codey.dev-genio.com/>
- Repository: <https://github.com/Varad-13/codey>

---

## Highlights

- **Streaming chat REPL** with markdown-aware ANSI output and inline tool-call visibility.
- **15 built-in tools** including `ask`, `delegate`, `web`, `view_image`, `terminal`, `edit_file`, `git`, `grep`, `calculate`, and more.
- **Multi-session persistence** — every project gets its own session history under `~/.codey/history/` with token/cost tracking.
- **Subagent delegation** — `delegate` spins up an isolated agent loop with its own tool scope, perfect for research or focused code edits.
- **Vision support** — paste a file path to attach it, or type `@image` to attach the current clipboard image.
- **Web browsing** via Playwright (Chromium auto-installs on first use).
- **Persistent terminals** — drive interactive wizards (`npm init`, `apt-get`, etc.) step by step.
- **Provider-agnostic** — works with OpenAI directly or OpenRouter, picked automatically from your API key prefix.
- **Self-update** — `codey update` checks GitHub Releases, verifies SHA-256, and reinstalls via pip.
- **Smart context management** — auto-truncates oversized tool results and summarizes older turns when the conversation grows.

## Installation

Codey isn't on PyPI — install it from a GitHub Release or from a local source checkout.

### From a GitHub Release (recommended)

1. Visit the [Releases page](https://github.com/Varad-13/codey/releases).
2. Download the `codey-<version>-py3-none-any.whl` asset.
3. Install it:

   ```bash
   pip install ./codey-<version>-py3-none-any.whl
   ```

### From a local source checkout

```bash
git clone https://github.com/Varad-13/codey.git
cd codey
pip install -e .
```

The first run will also download a Playwright Chromium build (~120 MB) the first time the `web` tool is invoked. To pre-install:

```bash
playwright install chromium
```

> Requires Python **3.7+**. The wheel is pure Python and works on Windows, macOS, and Linux.

For full instructions see **[docs/installation.md](docs/installation.md)**.

## Quick start

```bash
# 1. Set your API key (or put it in a .env file)
export OPENAI_API_KEY=sk-or-...   # OpenRouter
# export OPENAI_API_KEY=sk-proj-...  # or OpenAI directly

# 2. Launch
codey
```

You'll see a session picker for the current project (newest first), then a chat prompt:

```
You (Ctrl+N newline): _add a README to this folder_
```

Type `exit` or `quit` to leave. See **[docs/usage.md](docs/usage.md)** for the full interaction guide, including attachments and keyboard shortcuts.

## CLI subcommands

```bash
codey               # launch the chat REPL
codey --version     # print installed version (e.g. `codey 0.4.3`)
codey -V            # short form
codey update        # check GitHub Releases, verify SHA-256, and pip-install the latest wheel
```

## Configuration

Codey is configured entirely through environment variables (or a `.env` file in the project root):

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | *required* | API key. Prefix auto-detects the provider: `sk-proj-…` → OpenAI, `sk-or-…` → OpenRouter, otherwise `PROVIDER` is honored. |
| `OPENAI_BASE_URL` | derived | Override the API base URL (rarely needed). |
| `PROVIDER` | auto-detect | Force `openai` or `openrouter` if your key prefix isn't recognized. |
| `DEFAULT_PERSONA` | `gpt-5` | Selects a `(model, prompt)` pair from `codey/config.py`. |
| `UNLOCKED_MODEL` | per-provider default | Override the model name for the `gpt-5` persona. |
| `ENABLED_TOOLS` | all 15 tools | Comma-separated allowlist. Use this to lock down which tools the model can call. |
| `SHOW_TOOL_CALLS` | `true` | Print each tool invocation before it runs. |
| `SHOW_TOOL_RESULTS` | `false` | Print each tool's raw result. |
| `CONFIRM_SHELL` | `false` | Prompt `[y/N]` before every shell/terminal command. |
| `MAX_TOOL_ROUNDS` | `25` | Hard cap on consecutive tool-call rounds per turn. |
| `CODEY_NO_UPDATE_CHECK` | unset | If set, suppress the startup update check. |
| `CODEY_WEB_HEADLESS` | `false` | Run the Playwright browser invisibly. |

Full details, including a working `.env` template, are in **[docs/configuration.md](docs/configuration.md)**.

## Documentation

| Doc | Covers |
|---|---|
| [docs/introduction.md](docs/introduction.md) | What Codey is, who it's for |
| [docs/installation.md](docs/installation.md) | Install, upgrade, uninstall |
| [docs/usage.md](docs/usage.md) | Running the REPL, sessions, attachments, shortcuts |
| [docs/configuration.md](docs/configuration.md) | Every environment variable |
| [docs/architecture.md](docs/architecture.md) | Component map and request flow |
| [docs/tools.md](docs/tools.md) | Every tool, with schemas and examples |
| [docs/tool_improvements.md](docs/tool_improvements.md) | Tool internals, safety properties, and known limitations |
| [docs/logging.md](docs/logging.md) | Logging behavior and how to enable file logs |
| [docs/faq.md](docs/faq.md) | Common questions |
| [docs/contributing.md](docs/contributing.md) | Dev setup, PR process, code standards |

## Contributing

Bug reports, feature requests, and PRs are welcome. See **[docs/contributing.md](docs/contributing.md)** for the workflow.

## License

MIT — see [LICENSE](LICENSE).