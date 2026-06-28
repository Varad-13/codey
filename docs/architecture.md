# Architecture Overview

Codey is a single-process Python application that wires together an OpenAI-compatible chat API, a tool layer, a streaming chat runner, a persistent session store, and an optional Playwright browser. The whole thing runs from a `prompt_toolkit` REPL.

## Top-level layout

```
codey/
├── __init__.py            # __version__
├── __main__.py            # python -m codey
├── cli.py                 # REPL, session picker, attachment parsing, dispatch
├── chat_runner.py         # streaming loop, tool-call dispatch, context trim/compress
├── config.py              # env-driven configuration & OpenAI client
├── persistence.py         # session storage under ~/.codey/history/
├── update.py              # GitHub Releases polling & self-update flow
├── utils.py               # history trim, path safety, tool-sequence sanitization
├── encoding_safety.py     # safe_decode + run_capture for subprocess output
├── prompts/               # system prompt templates
│   ├── codey-unlocked.txt # the default persona
│   └── ...                # other (currently unused) personas
└── tools/                 # the 15 built-in tools
    ├── __init__.py        # TOOL_MAP + tool_schemas list
    ├── ask.py
    ├── calculate.py
    ├── create_file.py
    ├── delegate.py        # spawns a subagent loop
    ├── edit_file.py
    ├── git.py
    ├── grep.py
    ├── read_codebase.py
    ├── read_files.py
    ├── shell.py
    ├── terminal.py        # persistent interactive shell sessions
    ├── update.py          # the self-update tool
    ├── view_image.py
    └── web.py             # Playwright Chromium
```

## Component responsibilities

### `cli.py` — the REPL

Owns the user-facing experience:

- Dispatches `--version` and `update` subcommands via `_dispatch_argv` before doing any other work (so `codey update` works from CI / non-interactive contexts).
- Loads the persona's system prompt and appends a live list of enabled tools so the model always knows what's available.
- Calls `check_for_update()` and prints a single-line notice on stderr if a newer release is found.
- Shows the **session picker** (`_pick_session`) — lists existing sessions for `cwd`, with date, message count, and (if known) token usage and cost.
- Lazily constructs `PromptSession` and `KeyBindings` so non-interactive invocations don't touch the Win32 console.
- Parses each user message with `_extract_paths` (regex for quoted and unquoted file paths) and `_build_content` (attaches images / inlines text files / handles the `@image` clipboard trigger).
- Maintains the `history` list (system prompt + resumed prior messages + new turns) and the `session_tokens` accumulator, persisting both after every turn.

### `chat_runner.py` — the streaming loop

`process_history(history, model)` is the workhorse. For each user turn:

1. **Trim** history via `utils.trim_history` — drops messages past `max_messages=100`, truncates oversized tool results in older turns, and sanitizes orphan tool-call/tool-result pairs.
2. **Compress** if the total character count exceeds `CONTEXT_CACHE_THRESHOLD = 500_000` (~125K tokens). Older turns are summarized by the same model with `stream=False`, preserving the system prompt and the most recent 20 messages.
3. **Stream** a chat completion with `stream=True` and `stream_options={"include_usage": True}`. Token-by-token deltas are printed in green after a `Codey: ` prefix. Tool-call deltas are accumulated into `tool_calls_map` by index.
4. **Dispatch** any tool calls — see below.
5. **Repeat** until the assistant returns a response without tool calls, then return `(history, final_text, usage)`.

Tool-call dispatch happens through `call_tool(name, args)`, which:

- Optionally prompts `Approve? [y/N]` if `CONFIRM_SHELL` is true.
- Looks up the tool in `TOOL_MAP` (from `codey/tools/__init__.py`).
- Calls `func(**args)` and returns the result. Image-bearing results (dicts with a `__image__` key, returned by `view_image` and `web`) are converted to multimodal content arrays so vision-capable models can see them.
- Appends both the assistant turn and the tool result back to history so the next iteration has the full context.
- Enforces `MAX_TOOL_ROUNDS` — after 25 consecutive tool-call rounds, the loop breaks with a `[Stopped after 25 tool-call rounds]` message.

### `config.py` — single source of truth for env vars

Reads every environment variable at import time:

- Detects provider from the `OPENAI_API_KEY` prefix.
- Resolves the active persona's `(model, prompt)` pair.
- Builds the `client = OpenAI(base_url=..., api_key=...)` used by `chat_runner` and `delegate`.
- Exports `TOOL_MAP`, `ENABLED_TOOLS`, and the various `SHOW_*` / `CONFIRM_*` flags.

### `persistence.py` — session storage

`~/.codey/history/<project>-<hash>/` contains one `YYYYMMDD-HHMMSS.jsonl` per session plus a sibling `.meta.json` per session for token counters. The "project" key is `basename(realpath) + ":" + md5(realpath)[:8]` — same path on different machines maps to different sessions.

`load_session` excludes system messages when resuming so the system prompt can be rebuilt fresh from the active persona.

### `tools/` — the tool layer

Every tool follows the same pattern: a callable function plus a `schema` dict matching the OpenAI function-calling format. `tools/__init__.py` aggregates them into:

- `TOOL_MAP` — `name → callable`, used by `chat_runner.call_tool` and `delegate._call`.
- `tools` (the list of schemas) — passed to every chat completion as the `tools` parameter, filtered by `ENABLED_TOOLS`.

Notable internals:

- **`edit_file`** supports three modes (`find_replace`, `replace_range`, `insert`) and uses `assert_within_project` to prevent path traversal. Edits are atomic via `tempfile.mkstemp` + `os.replace`.
- **`delegate`** runs a *recursive* chat loop with its own system prompt ("focused subagent"), its own round cap (25), and a scoped tool set. This is what makes Codey scale to multi-step work.
- **`web`** runs Playwright inside a dedicated single-thread executor so the asyncio event loop never touches the main thread (critical for `prompt_toolkit` compatibility on Python 3.12+).
- **`terminal`** maintains a dict of `_Session` objects keyed by `session_id` — each holds a subprocess.Popen plus a buffered output queue, so the model can `start` → `send` → `peek` over multiple model turns.
- **`update`** checks GitHub Releases, downloads the wheel, verifies SHA-256 against the asset's `digest` field, and prompts before pip-installing.

### `update.py` — self-update

Decoupled from `tools/update.py` for a reason: `update.py` must work *before* the rest of the package is initialized (it's reachable via `codey update` which exits before the chat loop starts). It uses only `urllib.request`, `json`, `subprocess`, and stdlib. All network errors are swallowed — an update check must never crash the CLI.

### `utils.py` — shared helpers

- `assert_within_project(filepath, base_dir)` — raises `ValueError` if `realpath(filepath)` escapes `base_dir`. Used by `edit_file`, `delegate`, and anywhere else that accepts user-supplied paths.
- `sanitize_tool_sequences(msgs)` — removes orphan tool messages (no matching `tool_calls` ID) and orphan assistant `tool_calls` (no matching results), running two passes to handle cascading drops. Important when resuming sessions saved mid-crash.
- `trim_history(history)` — combines trimming + sanitization + tool-result truncation. Always preserves the system message.

### `encoding_safety.py` — Windows decoding workaround

Windows consoles default to code pages 437/1252, while child processes often emit UTF-8. The naive `subprocess.run(text=True)` raises `UnicodeDecodeError` on certain byte sequences (classically the C1 range 0x80–0x9F). This module provides:

- `safe_decode(data, *, preferred="utf-8", fallback="latin-1")` — tries UTF-8 with `errors="replace"`; if the result still contains replacement characters, retries with `latin-1` (which can decode any byte). Never raises.
- `run_capture(cmd, ...)` — `subprocess.run` wrapper that captures bytes and runs them through `safe_decode`. Returns a `CompletedProcess` with `.stdout` / `.stderr` as `str`.

Used by `tools/shell.py` and `tools/terminal.py`.

## Request flow

A single user turn:

```
User types message
        │
        ▼
cli._build_content()
   │  regex-extracts file paths
   │  triggers @image clipboard grab
   │  inlines images / text files
        ▼
chat_runner.process_history(history, model)
   │
   ├─ utils.trim_history(history)
   │     │  drop messages > 100
   │     │  truncate tool results > 3000 chars in older turns
   │     │  sanitize orphan tool sequences
   │     ▼
   ├─ _compress_context() if size > 500K chars
   │     │  summarize older turns with model
   │     ▼
   └─ loop up to MAX_TOOL_ROUNDS:
         │
         ├─ client.chat.completions.create(stream=True, ...)
         │     │
         │     ├─ stream text deltas → print in green, accumulate
         │     └─ stream tool_calls deltas → accumulate by index
         │
         ├─ if tool_calls:
         │     │
         │     ├─ append assistant turn + tool_calls to history
         │     ├─ for each tool call:
         │     │     ├─ ENABLED_TOOLS check (else error string)
         │     │     ├─ call_tool(name, args)
         │     │     │     ├─ if CONFIRM_SHELL: prompt [y/N]
         │     │     │     ├─ TOOL_MAP[name](**args)
         │     │     │     └─ if result is dict with __image__: multimodal content
         │     │     └─ append tool message with tool_call_id
         │     └─ continue loop
         │
         └─ else (final text response):
               └─ return (history, text, usage)
        ▼
cli saves messages + meta to session_path
```

The `delegate` flow is similar but recursive: instead of returning text to the user, the subagent's final message becomes its tool-result string, which gets fed back to the orchestrator.

## Data formats

### Session files (JSONL)

One JSON object per line. Roles follow OpenAI's chat-completion schema: `system`, `user`, `assistant`, `tool`. Tool calls appear as `tool_calls` arrays on assistant messages; tool results appear as `role: "tool"` messages with `tool_call_id` linking back.

### Update cache

`~/.cache/codey/update_check.json` (or `%LOCALAPPDATA%\codey\update_check.json` on Windows):

```json
{
  "checked_at": 1700000000.0,
  "info": {
    "version": "0.4.4",
    "url": "https://github.com/Varad-13/codey/releases/tag/v0.4.4",
    "notes": "## What's Changed\n...",
    "wheel_url": "https://github.com/Varad-13/codey/releases/download/v0.4.4/codey-0.4.4-py3-none-any.whl",
    "wheel_sha256": "abcdef1234...",
    "published_at": "2024-01-01T00:00:00Z"
  }
}
```

TTL is 6 hours (`CACHE_TTL_SECONDS`).

## Why these choices

- **`prompt_toolkit`** over `input()`: real multi-line editing, customizable key bindings, ANSI-friendly output, and `Ctrl+C`/`Ctrl+D` handling that doesn't fight the REPL.
- **Streamed completions**: lower time-to-first-token, and lets `Ctrl+C` cancel mid-stream without losing the session.
- **Per-tool schemas passed every call**: the model decides at every turn which tools to call; nothing is implicit.
- **Subagent delegation as a tool, not a CLI flag**: it composes naturally — a subagent can itself delegate further.
- **Atomic file writes** (`tempfile.mkstemp` + `os.replace`): a crash mid-edit can never leave a partial file on disk. Git history is the undo log.
- **`assert_within_project`** on every path-bearing tool: prevents the model from accidentally reading or writing outside the project directory even with a user-supplied path.