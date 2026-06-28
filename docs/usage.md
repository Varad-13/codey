# Usage

This doc covers the everyday interaction model: launching the REPL, working with sessions, attaching files and images, and the keyboard shortcuts.

## Launching the REPL

```bash
codey
```

On startup, Codey:

1. Dispatches `--version` / `update` subcommands if passed.
2. Loads the active persona's system prompt and appends the list of currently enabled tools.
3. Calls `check_for_update()` (unless `CODEY_NO_UPDATE_CHECK=1`) and prints a one-line notice on stderr if a newer release is available.
4. Shows a **session picker** for the current working directory.
5. Enters the chat loop.

## Session picker

Every project directory has its own session history stored under `~/.codey/history/<project-name>-<hash>/`. On launch you'll see:

```
Sessions — my-project

  [1] Today      14:32  (12 msgs)    explain this function...
  [2] Yesterday  09:11  (4 msgs)     fix the failing test...    in:842 out:312 tot:1154 $0.0021
  [3] Mon    18:04  (23 msgs)    refactor auth module...      in:2.1k out:1.4k tot:3.5k $0.0118

  [N]  New session

Select [1–3/N]:
```

- Type a number to **resume** that session — its previous messages are loaded back into the chat history.
- Type `N` (or just press Enter) to start a **fresh** session.
- Token and cost columns only appear for sessions where the API reported them (OpenRouter does, OpenAI does not).
- The picker falls through to "New session" automatically if there are no saved sessions.

Sessions are stored as JSONL files (one line per message) plus a sibling `.meta.json` for accumulated token/cost counters. See [architecture.md](architecture.md) for details.

## Inside the chat

```
You (Ctrl+N newline): _
```

The prompt is a multi-line input. Type your message and press **Enter** to send.

### Keyboard shortcuts

| Key | Action |
|---|---|
| `Enter` | Submit your message |
| `Ctrl+N` | Insert a newline (continue typing without sending) |
| `Ctrl+C` | Cancel the current generation — rolls back the in-flight user message and returns to the prompt |
| `Ctrl+D` / `EOF` | Exit the REPL cleanly (prints token summary) |
| `exit` / `quit` | Same as Ctrl+D — type and press Enter |

When the model produces a tool call, you'll see it formatted in magenta:

```
Tool: edit_file({"filename": "README.md", "mode": "find_replace", ...})
Approve? [y/N]
```

(Only prompts when `CONFIRM_SHELL=true`. Otherwise the call runs immediately and is logged.)

When the model returns a final response, it streams token-by-token in green after a `Codey: ` prefix.

Type `exit` or `quit` to leave. On exit, Codey prints the session's accumulated token counts and cost:

```
Tokens — in: 4,521  out: 2,107  total: 6,628  cost: $0.021487
```

## Attachments

The REPL scans each message for file paths and the special `@image` trigger.

### File paths

Type any absolute or `~/`-prefixed path, **quoted or unquoted**:

```
You: explain what's wrong with C:\Users\me\project\auth.py
You: review "C:\code\app\src\server.ts" for bugs
You: diff ~/projects/api/openapi.yaml against the docs
```

Supported extensions are automatically detected:

- **Images** (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`) → sent as `image_url` content blocks so vision-capable models see them directly.
- **Everything else** → inlined as a fenced text block under `[File: <path>]`.

Each attachment produces a confirmation line:

```
Attached image: C:\screens\error.png
Attached file: C:\code\app\server.ts
```

If the path doesn't exist or can't be read, you'll see a `Could not attach ...` notice but the message is still sent.

### Clipboard image (`@image`)

Type `@image` anywhere in your message to attach whatever is currently on the system clipboard as a PNG:

```
You: @image what's wrong with this stack trace screenshot?
```

Requires Pillow (installed by default). Falls back gracefully if no image is on the clipboard.

## CLI subcommands

```bash
codey               # launch chat REPL (default)
codey --version     # print installed version, e.g. `codey 0.4.3`
codey -V            # short form
codey update        # check GitHub Releases and self-upgrade
```

### `codey update`

Flow:

1. `GET https://api.github.com/repos/Varad-13/codey/releases/latest` (cached for 6 hours per user, so this is free on subsequent runs).
2. Find the wheel asset `codey-<version>-py3-none-any.whl`.
3. Read the asset's `digest` field for SHA-256 verification.
4. Print the first 15 lines of release notes.
5. Prompt `Proceed with update to vX.Y.Z? [y/N]:`.
6. On yes, run `pip install --upgrade git+https://github.com/Varad-13/codey.git@vX.Y.Z`.

Exit codes:

- `0` — updated successfully, or already up to date.
- `1` — genuine failure (network error, hash mismatch, pip error, user cancelled with anything other than `y`/`yes`).

## Environment toggles during a session

| Variable | Effect at runtime |
|---|---|
| `SHOW_TOOL_CALLS=true` | Print each tool invocation as it happens |
| `SHOW_TOOL_RESULTS=true` | Also print each tool's raw result |
| `CONFIRM_SHELL=true` | Prompt `[y/N]` before every shell/terminal command |
| `MAX_TOOL_ROUNDS=N` | Cap consecutive tool-call rounds per turn (default 25) |
| `CODEY_WEB_HEADLESS=true` | Run the Playwright browser invisibly |
| `CODEY_NO_UPDATE_CHECK=1` | Skip the startup release check |

These are read at import time in `codey/config.py`, so changing them requires a restart. See [configuration.md](configuration.md).

## Example session

```
$ cd ~/code/my-project
$ codey

Sessions — my-project

  [1] Yesterday  16:22  (8 msgs)     add CLI flags to the tool...

  [N]  New session

Select [1/N]: n

Provider: openrouter  Model: anthropic/claude-3.5-sonnet  Tools: ask, shell, terminal, delegate, ...
Tip: paste a file path to attach it | type @image to attach clipboard image

You (Ctrl+N newline): add a CONTRIBUTING.md with our PR conventions
Codey: I'll start by checking what's already in the repo and looking at the existing README for tone.

Tool: read_codebase()
Attached file: ./README.md
Tool: grep({"term": "PR|pull request"})

Here's a draft that matches your style: ...

[ content elided ]

Tool: create_file({"filename": "CONTRIBUTING.md", ...})
Created CONTRIBUTING.md. Review the diff above and run `git add CONTRIBUTING.md && git commit -m "docs: add CONTRIBUTING.md"` when you're happy.

You (Ctrl+N newline): exit
Goodbye!
Tokens — in: 1,234  out: 567  total: 1,801
```

## What's next

- [configuration.md](configuration.md) — every environment variable.
- [tools.md](tools.md) — every tool with schemas and examples.
- [architecture.md](architecture.md) — what happens between your keystroke and the model response.
- [faq.md](faq.md) — common questions.