# Configuration

Codey is configured entirely through environment variables. There is no config file format of its own — you set env vars in your shell, in your CI, or in a `.env` file (loaded automatically by `python-dotenv` from the current working directory on import).

## Quick reference

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | *required* | API key. Prefix auto-detects the provider. |
| `OPENAI_BASE_URL` | derived | Override the API base URL. |
| `PROVIDER` | auto-detect | Force `openai` or `openrouter`. |
| `DEFAULT_PERSONA` | `gpt-5` | Selects a `(model, prompt)` pair. |
| `UNLOCKED_MODEL` | per-provider | Model name override for the `gpt-5` persona. |
| `PROMPT_NAME` | `codey-unlocked.txt` | System prompt file from `codey/prompts/`. |
| `ENABLED_TOOLS` | all 15 tools | Comma-separated allowlist. |
| `SHOW_TOOL_CALLS` | `true` | Print each tool call as it runs. |
| `SHOW_TOOL_RESULTS` | `false` | Print each tool's raw result. |
| `CONFIRM_SHELL` | `false` | Prompt `[y/N]` before shell/terminal commands. |
| `MAX_TOOL_ROUNDS` | `25` | Cap consecutive tool-call rounds per turn. |
| `CODEY_NO_UPDATE_CHECK` | unset | Skip the startup release check. |
| `CODEY_WEB_HEADLESS` | `false` | Run Playwright headlessly. |

Each variable is described in detail below, grouped by area.

---

## Provider & API key

### `OPENAI_API_KEY` *(required)*

The single source of truth for credentials. Codey inspects the prefix:

- `sk-proj-…` → **OpenAI** (`https://api.openai.com/v1`, default model `gpt-4.1-mini`).
- `sk-or-…` → **OpenRouter** (`https://openrouter.ai/api/v1`, default model `minimax/minimax-m3`).
- anything else → falls back to `PROVIDER` env var (default `openrouter`).

If unset, Codey raises `RuntimeError: Please set the OPENAI_API_KEY environment variable` on import. There is no interactive login flow.

### `OPENAI_BASE_URL` *(optional)*

Override the API base URL. Normally you don't need this — Codey picks one based on the detected provider. Useful for:

- Local LLM gateways like Ollama, LM Studio, or vLLM that expose an OpenAI-compatible endpoint.
- Self-hosted proxies or mirror sites.

Example:

```bash
export OPENAI_BASE_URL="http://localhost:11434/v1"   # Ollama
export OPENAI_BASE_URL="https://my-gateway.internal/v1"
```

### `PROVIDER` *(optional)*

Force the provider when the key prefix isn't recognized. Set to `openai` or `openrouter`. Most users will never need this — it's a fallback for custom keys issued by enterprise proxies.

---

## Persona & model

Codey uses a **persona** system: each persona is a `(model, prompt)` pair. The active persona is selected by `DEFAULT_PERSONA`, which currently maps to the only registered persona: `gpt-5`.

### `DEFAULT_PERSONA`

```bash
export DEFAULT_PERSONA=gpt-5
```

The default is `gpt-5`. Adding new personas requires editing `PERSONAS` in `codey/config.py` and adding a prompt file to `codey/prompts/`.

### `UNLOCKED_MODEL`

Override the model used by the `gpt-5` persona. If unset:

- OpenAI → `gpt-4.1-mini`
- OpenRouter → `minimax/minimax-m3`

```bash
export UNLOCKED_MODEL=anthropic/claude-3.5-sonnet
export UNLOCKED_MODEL=gpt-4o
export UNLOCKED_MODEL=qwen/qwen-2.5-coder-32b-instruct
```

The model just needs to be reachable on the configured base URL and support the OpenAI chat-completions function-calling schema.

### `PROMPT_NAME`

The system prompt file inside `codey/prompts/` to load. Defaults to `codey-unlocked.txt` (the only fully-maintained persona at the moment). Other files in that directory — `default_prompt.txt`, `builder_prompt.txt`, `educator_prompt.txt`, `static_app.txt` — exist but are not currently wired into any registered persona. See [architecture.md](architecture.md) for how prompts are loaded.

---

## Tools

### `ENABLED_TOOLS`

Comma-separated allowlist of tool names. The model can only call tools in this list.

```bash
# Only let Codey read files and search:
export ENABLED_TOOLS=read_files,grep,read_codebase

# Disable the web tool for offline use:
export ENABLED_TOOLS=ask,shell,terminal,delegate,read_codebase,read_files,view_image,calculate,create_file,edit_file,git,grep,update
```

Default value (every tool):

```
ask,shell,terminal,delegate,web,read_codebase,read_files,view_image,calculate,create_file,edit_file,git,grep,update
```

The active list is appended to the system prompt so the model always knows what's available. Disabled tools that the model tries to call get a clear error string returned in the tool message rather than being silently dropped — this prevents malformed tool-call sequences from poisoning history.

### `SHOW_TOOL_CALLS`

```bash
export SHOW_TOOL_CALLS=true   # default
```

When `true`, prints each tool call (name + truncated args) in magenta before it runs. Set to `false` for quieter output.

### `SHOW_TOOL_RESULTS`

```bash
export SHOW_TOOL_RESULTS=false  # default
```

When `true`, also prints each tool's raw result after it returns. Useful for debugging but very noisy with image-heavy sessions.

### `CONFIRM_SHELL`

```bash
export CONFIRM_SHELL=false  # default
export CONFIRM_SHELL=true   # prompt before every shell/terminal/git command
```

When `true`, every shell or terminal command (and anything in `git` that changes state) prompts `Approve? [y/N]` before running. **Note:** this confirmation is implemented in `chat_runner.call_tool` and currently fires for *every* tool, not only shell-like ones. Use `ENABLED_TOOLS` for finer-grained gating.

### `MAX_TOOL_ROUNDS`

```bash
export MAX_TOOL_ROUNDS=25  # default
```

Maximum number of consecutive model→tool-call loops per user turn. When the limit is hit, the assistant is forced to give a final text response (a `[Stopped after N tool-call rounds]` message is appended if the model doesn't produce one). This is the safety net against runaway tool-call loops.

---

## Updates

### `CODEY_NO_UPDATE_CHECK`

```bash
export CODEY_NO_UPDATE_CHECK=1
```

Disables the startup check that polls `https://api.github.com/repos/Varad-13/codey/releases/latest`. Accepts `1`, `true`, `yes`, `on` (case-insensitive). Use this in CI, in tests, or if you're behind a strict firewall.

The 6-hour cache in `~/.cache/codey/update_check.json` (or OS-appropriate location) means the check only fires once per session on most machines anyway.

The `codey update` subcommand is **not** affected by this flag.

---

## Web tool (Playwright)

### `CODEY_WEB_HEADLESS`

```bash
export CODEY_WEB_HEADLESS=false  # default — show browser window
export CODEY_WEB_HEADLESS=true   # run invisibly
```

The `web` tool launches a Chromium instance for the duration of the session. By default it runs **headed** so you can watch what the model is doing. Set this to `true` for headless servers or when you don't want a window popping up.

The browser is launched on the first `web` action and lives until `codey` exits (or you call `web(action="close")`). All Playwright work runs in a dedicated background thread so it doesn't conflict with `prompt_toolkit` on the main thread.

---

## Setting variables

### Shell (Unix)

```bash
export OPENAI_API_KEY='sk-or-v1-...'
export PROVIDER='openrouter'
export UNLOCKED_MODEL='anthropic/claude-3.5-sonnet'
export CODEY_WEB_HEADLESS=true
```

### Shell (Windows PowerShell)

```powershell
$env:OPENAI_API_KEY = "sk-or-v1-..."
$env:PROVIDER = "openrouter"
$env:UNLOCKED_MODEL = "anthropic/claude-3.5-sonnet"
$env:CODEY_WEB_HEADLESS = "true"
```

### Windows `set`

```cmd
set OPENAI_API_KEY=sk-or-v1-...
set PROVIDER=openrouter
```

### `.env` file

Put a `.env` in the directory you launch `codey` from (or in your home directory — `python-dotenv` walks up):

```dotenv
# .env
OPENAI_API_KEY=sk-or-v1-...
PROVIDER=openrouter
UNLOCKED_MODEL=anthropic/claude-3.5-sonnet
ENABLED_TOOLS=ask,shell,terminal,delegate,web,read_codebase,read_files,view_image,calculate,create_file,edit_file,git,grep,update
SHOW_TOOL_CALLS=true
SHOW_TOOL_RESULTS=false
CONFIRM_SHELL=false
MAX_TOOL_ROUNDS=25
CODEY_WEB_HEADLESS=false
# CODEY_NO_UPDATE_CHECK=1
```

`python-dotenv` does **not** overwrite existing environment variables — your shell exports win.

---

## Validating the config

Run `codey` once and look at the banner it prints before the chat loop:

```
Provider: openrouter  Model: anthropic/claude-3.5-sonnet  Tools: ask, shell, terminal, delegate, ...  — type 'exit' to quit
```

If the provider is wrong, the key isn't being read, or your env vars aren't reaching Python, it will show up here immediately.

For deeper validation, run `python -c "from codey import config; print(config.PROVIDER, config.MODEL_NAME)"` and check that the values match your expectations.