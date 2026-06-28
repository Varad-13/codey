# Frequently Asked Questions

## General

### What is Codey?

Codey is a Python package that runs an OpenAI-compatible chat model in your terminal, with a tool layer for reading files, editing code, running shell commands, browsing the web, driving interactive CLIs, managing git, and spawning focused subagents. See [introduction.md](introduction.md) for an overview.

### How does it differ from a chat web UI?

A chat UI can suggest code. Codey can actually **run** code — read your files, edit them, execute commands, browse docs, commit changes. The REPL is the workflow.

### Which AI providers are supported?

Any OpenAI-compatible API. Out of the box, Codey auto-detects:

- OpenAI direct (`sk-proj-…`) → `https://api.openai.com/v1`
- OpenRouter (`sk-or-…`) → `https://openrouter.ai/api/v1`

Set `OPENAI_BASE_URL` to use a local gateway (Ollama, LM Studio, vLLM, etc.) or `PROVIDER` to force a specific provider for unrecognized keys. See [configuration.md](configuration.md).

### What models work?

Any model that supports OpenAI chat completions with function calling. `gpt-4.1-mini` is the default for direct OpenAI; pick anything you like via `UNLOCKED_MODEL` or by setting `OPENAI_BASE_URL` to a local server.

### Does Codey work offline?

Partially. The chat model requires a working connection to the API. The tools themselves are local — `shell`, `terminal`, `read_files`, `edit_file`, `git`, `grep`, and `calculate` work without internet. The `web` tool requires Playwright Chromium (~120 MB, downloads on first use). The `update` tool requires GitHub. Set `CODEY_NO_UPDATE_CHECK=1` to silence the startup release check.

---

## Installation & setup

### How do I install Codey?

Codey isn't on PyPI. The two supported install paths are:

```bash
# From a downloaded GitHub Release wheel:
pip install ./codey-<version>-py3-none-any.whl

# Or from a local source checkout (dev installs):
git clone https://github.com/Varad-13/codey.git
cd codey
pip install -e .
```

For full instructions including wheels and dev installs, see [installation.md](installation.md).

### I get `RuntimeError: Please set the OPENAI_API_KEY environment variable`.

You didn't set your API key. Either `export OPENAI_API_KEY=...` in your shell, or put `OPENAI_API_KEY=...` in a `.env` file in the directory you launch `codey` from. `python-dotenv` loads `.env` automatically.

See [configuration.md](configuration.md).

### Will installing Codey download Chromium automatically?

Yes — `setup.py` runs `playwright install chromium` after install. If that step is skipped (or fails), you can run it manually:

```bash
playwright install chromium
```

The download is ~120 MB and only happens once.

### How do I update Codey?

```bash
codey update
```

This polls GitHub Releases, verifies SHA-256, and pip-installs the new wheel. See [usage.md](usage.md) for details.

### How do I uninstall Codey?

```bash
pip uninstall codey
rm -rf ~/.codey        # session history
playwright uninstall chromium   # optional
```

---

## Using the REPL

### What are the keyboard shortcuts?

| Key | Action |
|---|---|
| `Enter` | Submit your message |
| `Ctrl+N` | Insert a newline |
| `Ctrl+C` | Cancel the current generation |
| `Ctrl+D` | Exit the REPL |
| `exit` / `quit` | Same as `Ctrl+D` |

See [usage.md](usage.md) for the full interaction guide.

### How do I attach a file to my message?

Paste the path — quoted or unquoted — anywhere in your message:

```
You: explain what's wrong with C:\code\app\auth.py
You: review "C:\code\app\server.ts" for bugs
```

Images are sent as vision content blocks; text files are inlined. The REPL scans every message for paths automatically. See [usage.md](usage.md) § Attachments.

### How do I attach a screenshot?

Type `@image` in your message. Codey grabs whatever's on your system clipboard and attaches it as a PNG.

Requires Pillow (installed by default). If no image is on the clipboard, you'll see a notice and the message is still sent.

### Can I resume a previous session?

Yes. When you launch `codey` in a project directory that has saved sessions, you'll see the **session picker**. Type the number of the session you want to resume. Sessions are stored under `~/.codey/history/<project>-<hash>/`.

### Where are sessions stored?

`~/.codey/history/<project-name>-<md5(cwd)[:8]>/` as JSONL files plus sibling `.meta.json` for token counters. Each session file is named `YYYYMMDD-HHMMSS.jsonl`.

### How do I start a fresh session?

At the session picker, type `N` or press Enter (when there are no saved sessions, you skip the picker entirely and get a new session).

---

## Configuration

### How do I switch models?

```bash
export UNLOCKED_MODEL=anthropic/claude-3.5-sonnet
export UNLOCKED_MODEL=gpt-4o
export UNLOCKED_MODEL=qwen/qwen-2.5-coder-32b-instruct
```

See [configuration.md](configuration.md) § Persona & model.

### How do I disable specific tools?

```bash
export ENABLED_TOOLS=read_files,grep,read_codebase,ask
```

The default enables all 15 tools. Any tool not in the list returns an error if the model tries to call it. See [configuration.md](configuration.md) § `ENABLED_TOOLS`.

### How do I make Codey prompt before every shell command?

```bash
export CONFIRM_SHELL=true
```

Currently this fires for **every** tool call (not only shell-like ones). For finer-grained gating, use `ENABLED_TOOLS`.

### How do I run the browser headlessly?

```bash
export CODEY_WEB_HEADLESS=true
```

The browser opens visibly by default so you can watch what the model is doing.

### How do I suppress the startup update check?

```bash
export CODEY_NO_UPDATE_CHECK=1
```

The 6-hour cache means the check only fires once per session on most machines anyway, but this is useful in CI or behind strict firewalls. It does **not** affect `codey update`.

---

## Tooling

### What's the difference between `shell` and `terminal`?

- `shell` is for one-shot, non-interactive commands: `npm run build`, `git log`, `pytest`.
- `terminal` keeps a persistent process alive across multiple model turns — use it for commands that prompt for input: `npm init`, `apt-get`, anything that asks `Y/N`.

See [tools.md](tools.md).

### When should I use `delegate`?

For any task that would take 3+ sequential tool calls, multi-step research, or anything decomposable into independent subtasks. Each subagent has its own tool scope and a 25-round cap, and **cannot call back** to the orchestrator. See [tools.md](tools.md) § `delegate`.

### Does Codey create backup files before editing?

No. Edits are atomic via `tempfile.mkstemp` + `os.replace`, but no `.bak` files are written. **Git history is your undo log.** Make a commit before letting Codey make non-trivial edits.

### Why does `edit_file` fail with "0 matches"?

The `find_replace` mode requires an exact substring match, including whitespace. Double-check indentation, trailing spaces, and line endings. The error message includes a hint.

### Can the model read files outside the project directory?

By default, no — `assert_within_project` blocks paths that resolve outside `cwd`. The exception is `view_image`, which intentionally accepts arbitrary paths because users frequently reference screenshots in `~/Downloads`.

### How do I see exactly which tools are active?

The startup banner prints the full list:

```
Provider: openrouter  Model: ...  Tools: ask, shell, terminal, delegate, ...  — type 'exit' to quit
```

This is the resolved `ENABLED_TOOLS` value. See [configuration.md](configuration.md).

---

## Troubleshooting

### `codey` hangs at startup.

It's probably the GitHub update check. Set `CODEY_NO_UPDATE_CHECK=1` or wait — the 5-second timeout will trip. On firewalls, the check fails silently and you'll see no notice.

### The model can't see my image attachment.

- The file must be one of: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`.
- The path must exist and be readable.
- The model itself must support vision. Most modern models do; tiny OSS models often don't.

### `UnicodeDecodeError` from `shell` on Windows.

This shouldn't happen — Codey uses `encoding_safety.safe_decode` precisely to avoid it. If you still see it, please file an issue with the failing command and platform details.

### The REPL prints literal escape sequences (`^[[95m` etc.).

Your terminal doesn't support ANSI escape codes. Most modern terminals do. Try Windows Terminal, iTerm2, GNOME Terminal, or set `TERM=xterm-256color`.

### `NoConsoleScreenBufferError` when running from CI / scripts.

Codey lazy-constructs the prompt session, so `codey --version` and `codey update` work fine from non-interactive contexts. If you see this error, you're probably running the chat REPL itself without a console — which is by design impossible.

---

## Reporting issues

- **Bugs:** <https://github.com/Varad-13/codey/issues/new?template=bug_report.md>
- **Feature requests:** <https://github.com/Varad-13/codey/issues/new>
- **Security issues:** please email rather than filing a public issue.

When reporting a bug, include:

1. Codey version (`codey --version`).
2. Operating system and Python version.
3. Provider and model (`codey` startup banner).
4. The exact command/message that triggered the issue.
5. Full output, including any traceback.

See [contributing.md](contributing.md) for the dev workflow.