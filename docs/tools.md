# Tools Documentation

Every tool that the model can call. Schemas follow the OpenAI function-calling format. Use `ENABLED_TOOLS` (see [configuration.md](configuration.md)) to scope the active set.

| # | Tool | Purpose |
|---|---|---|
| 1 | `ask` | Ask the user a clarifying question with optional numbered choices |
| 2 | `shell` | Run a one-shot shell/PowerShell command |
| 3 | `terminal` | Drive a persistent interactive terminal session |
| 4 | `delegate` | Spawn an autonomous subagent with scoped tools |
| 5 | `web` | Browse the web via Playwright Chromium |
| 6 | `read_codebase` | List all tracked files in the current git repository |
| 7 | `read_files` | Read one or more files, returning numbered lines |
| 8 | `view_image` | Load an image so the model can see it |
| 9 | `calculate` | Evaluate a math expression safely |
| 10 | `create_file` | Create or overwrite a file (atomic write) |
| 11 | `edit_file` | Surgical in-place edit (find/replace, range, or insert) |
| 12 | `git` | Whitelisted git subcommands (add, commit, diff, status, …) |
| 13 | `grep` | Search tracked files for a literal term or regex |
| 14 | `update` | Self-update to the latest GitHub release |
| 15 | `web` | *(see #5)* |

The `web` tool (Playwright) also produces vision content blocks when you `screenshot` — those flow back into the conversation as multimodal tool-result content.

---

## 1. `ask` — Clarifying question

Present a question to the user and wait for a reply. The model is encouraged to use this **before** any non-trivial decision.

- **`question`** *(string, required)* — the question to display.
- **`options`** *(array of strings, optional)* — 2–4 suggested answers. The user can pick by number or type a custom reply.

```json
{
  "type": "function",
  "function": {
    "name": "ask",
    "description": "Ask the user a question and wait for their response before continuing. Use this whenever you need a decision, preference, or clarification. Supply 'options' to offer numbered choices; the user can pick one or type a custom answer.",
    "parameters": {
      "type": "object",
      "properties": {
        "question": {"type": "string"},
        "options":  {"type": "array", "items": {"type": "string"}}
      },
      "required": ["question"],
      "additionalProperties": false
    }
  }
}
```

**Behavior.** Prints `? <question>` in cyan, then numbered options if provided, then prompts `Enter number or type a reply:`. Returns either the chosen option text or the raw reply. EOF / Ctrl+C returns `"(no response)"`.

---

## 2. `shell` — One-shot command

Run a non-interactive shell command and return its output.

- **`command`** *(string, required)* — the command to execute.

On Windows, uses `powershell -Command`. On Unix, uses `/bin/sh -c`. Output is decoded via `encoding_safety.safe_decode` so UTF-8 bytes from child processes never raise `UnicodeDecodeError` even on Windows code-page 437/1252.

```json
{
  "type": "function",
  "function": {
    "name": "shell",
    "description": "Run a shell/PowerShell command, non-interactive.",
    "parameters": {
      "type": "object",
      "properties": {"command": {"type": "string"}},
      "required": ["command"],
      "additionalProperties": false
    }
  }
}
```

Reach for `terminal` instead when the command prompts for input (`npm init`, `apt-get`, etc.).

---

## 3. `terminal` — Persistent interactive session

Drive a long-lived shell process across multiple model turns. Use this when a command prompts for input.

- **`action`** *(enum, required)* — `start`, `send`, `peek`, or `stop`.
- **`command`** *(string, required for `start`)* — the initial command to run.
- **`text`** *(string, required for `send`)* — input to write to stdin (newline appended automatically).
- **`session_id`** *(string, default `"default"`)* — name for the session. Use different IDs to run multiple sessions concurrently.
- **`settle`** *(float, default `0.3`)* — seconds of silence that signal "no more output coming."
- **`timeout`** *(float, default `10.0`)* — total wait cap per `start` / `send` / `peek` call.

Workflow:

```
terminal(action="start", command="npm init")
# → reads prompt, e.g. "package name:"
terminal(action="send", text="my-app")
# → reads next prompt, e.g. "version:"
terminal(action="send", text="1.0.0")
# → ...
terminal(action="peek")       # check for output without sending input
terminal(action="stop")       # terminate
```

A `start` call returns immediately if the process exits (e.g. `python --version`).

```json
{
  "type": "function",
  "function": {
    "name": "terminal",
    "description": "Run an interactive terminal session for commands that prompt for input (Y/N confirmations, setup wizards, multi-step CLI tools). Workflow: start → read output → send responses one at a time → process exits or stop. Use 'peek' to check for output without sending input. Multiple concurrent sessions are supported via session_id.",
    "parameters": {
      "type": "object",
      "properties": {
        "action":      {"type": "string", "enum": ["start", "send", "peek", "stop"]},
        "command":     {"type": "string"},
        "text":        {"type": "string"},
        "session_id":  {"type": "string"},
        "settle":      {"type": "number"},
        "timeout":     {"type": "number"}
      },
      "required": ["action"],
      "additionalProperties": false
    }
  }
}
```

---

## 4. `delegate` — Subagent

Spin up an autonomous subagent with its own chat loop, its own tool scope, and a 25-round cap. The subagent cannot call back into the orchestrator.

- **`task`** *(string, required)* — full description of what to accomplish. Include the goal, constraints, and what "done" looks like.
- **`tools`** *(array of strings, optional)* — tool names to make available. Defaults to `["web", "shell", "read_files", "grep", "create_file", "edit_file", "git", "calculate"]`. Pass `["web"]` for pure research, or `["read_files", "edit_file", "git"]` for code-only edits.
- **`files`** *(array of strings, optional)* — relative paths of files to inline into the subagent's task prompt as fenced snippets.
- **`suggested_patch`** *(string, optional)* — pseudocode or a diff sketch hinting at the intended code change.

Returns a structured summary from the subagent. The subagent's tool calls are printed in yellow (`↳ name(args)`).

```json
{
  "type": "function",
  "function": {
    "name": "delegate",
    "description": "Spin up an autonomous subagent to complete a task end-to-end. The subagent runs its own tool loop — it can browse the web, run shell commands, read/write files, search code, and more. Use for: research, multi-step setup tasks, focused code edits, or anything that needs several tool calls to complete.",
    "parameters": {
      "type": "object",
      "properties": {
        "task":            {"type": "string"},
        "tools":           {"type": "array", "items": {"type": "string"}},
        "files":           {"type": "array", "items": {"type": "string"}},
        "suggested_patch": {"type": "string"}
      },
      "required": ["task"],
      "additionalProperties": false
    }
  }
}
```

**When to delegate:** 3+ sequential tool calls, research + code changes, large-file work that would balloon context, or anything decomposable into independent subtasks. Spawn one subagent per subtask and stitch the results yourself. See the system prompt's "Delegate Liberally" section for the full rules.

---

## 5. `web` — Browser control

Control a local Chromium browser. All Playwright work runs in a dedicated background thread so its asyncio loop never touches the main thread (this matters for `prompt_toolkit` compatibility on Python 3.12+).

- **`action`** *(enum, required)* — `navigate`, `screenshot`, `get_text`, `get_html`, `click`, `fill`, `scroll`, `eval`, `wait`, `close`.
- **`url`** *(string, required for `navigate`)* — page URL.
- **`selector`** *(string, required for `click`, `fill`, `wait`)* — CSS selector.
- **`text`** *(string, for `fill`)* — text to type.
- **`js`** *(string, for `eval`)* — JavaScript expression.
- **`direction`** *(enum, default `"down"`)* — scroll direction.
- **`amount`** *(number, default `500`)* — scroll pixels.
- **`timeout`** *(number, default `10000`)* — max wait in milliseconds.

The first call auto-installs Chromium if it's missing. Use `CODEY_WEB_HEADLESS=true` to run invisibly.

Action summary:

| Action | Returns |
|---|---|
| `navigate` | `"Navigated to <url> — HTTP <status>, title: ..."` |
| `screenshot` | PNG image (sent back to the model as vision content) |
| `get_text` | visible body text |
| `get_html` | full HTML source |
| `click` | confirmation + new URL |
| `fill` | confirmation |
| `scroll` | confirmation |
| `eval` | stringified result of the JS expression |
| `wait` | confirmation when the selector becomes visible |
| `close` | `"Browser closed."` |

```json
{
  "type": "function",
  "function": {
    "name": "web",
    "description": "Control a local Chromium browser. Use navigate to open pages, screenshot to see what's on screen, get_text/get_html to read content, click/fill to interact with forms, scroll to reveal more content, eval to run JavaScript.",
    "parameters": {
      "type": "object",
      "properties": {
        "action":    {"type": "string", "enum": ["navigate","screenshot","get_text","get_html","click","fill","scroll","eval","wait","close"]},
        "url":       {"type": "string"},
        "selector":  {"type": "string"},
        "text":      {"type": "string"},
        "js":        {"type": "string"},
        "direction": {"type": "string", "enum": ["up","down"]},
        "amount":    {"type": "number"},
        "timeout":   {"type": "number"}
      },
      "required": ["action"],
      "additionalProperties": false
    }
  }
}
```

**URL rule:** when the user's message contains a URL, the model is instructed (and the system prompt explicitly says) to call `web(action="navigate", url=<url>)` immediately rather than asking the user to paste the content.

---

## 6. `read_codebase` — List tracked files

List every file tracked by the current git repository. Returns a clear notice (without modifying the repo) if the directory isn't a git repo or has no commits yet.

```json
{
  "type": "function",
  "function": {
    "name": "read_codebase",
    "description": "List files in the git repository (initializes if empty).",
    "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": false}
  }
}
```

Typical response:

```
[Tracked files in current repository]
codey/__init__.py
codey/cli.py
codey/chat_runner.py
...
```

If the directory isn't a git repo: returns `No tracked files; repository appears uninitialized. Run 'git init' if you want to initialize.` (Earlier versions auto-initialized; that behavior was removed.)

---

## 7. `read_files` — Read one or more files

- **`file_list`** *(string, required)* — comma-separated list of paths (absolute or relative to cwd).

Returns numbered lines for each file. Binary files (null bytes in the first 8 KB) are skipped with a notice. Files larger than ~1 MB return a snippet rather than the full content.

```json
{
  "type": "function",
  "function": {
    "name": "read_files",
    "description": "Read one or more files by comma-separated list, returning numbered lines for each file.",
    "parameters": {
      "type": "object",
      "properties": {"file_list": {"type": "string"}},
      "required": ["file_list"],
      "additionalProperties": false
    }
  }
}
```

Example:

```
read_files(file_list="codey/cli.py,codey/chat_runner.py")
```

---

## 8. `view_image` — Load an image

Load an image file so the model can see it as a vision content block.

- **`path`** *(string, required)* — absolute path or path relative to the project directory.

Supported formats: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`.

Returns an image content block plus a one-line description:

```json
{
  "type": "function",
  "function": {
    "name": "view_image",
    "description": "Load an image file from disk so you can see it directly. Use for screenshots, diagrams, UI mockups, error screenshots, or any image you need to inspect.",
    "parameters": {
      "type": "object",
      "properties": {"path": {"type": "string"}},
      "required": ["path"],
      "additionalProperties": false
    }
  }
}
```

You can also attach images implicitly by pasting a path into a chat message (the REPL scans for paths automatically) or by typing `@image` to attach the current clipboard image — see [usage.md](usage.md).

---

## 9. `calculate` — Math

- **`expression`** *(string, required)* — math expression to evaluate.

Built on a regex + restricted-`eval` sandbox. Supports standard arithmetic (`+`, `-`, `*`, `/`, `**`, `%`), parentheses, and a whitelist of `math` functions (`sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sinh`, `cosh`, `tanh`, `log`, `log10`, `log2`, `exp`, `sqrt`, `pow`, `floor`, `ceil`, `fabs`, `pi`, `e`). Trig functions are interpreted in **radians** by default — `sin(x)` style calls are rewritten to `sin(radians(x))` so casual usage matches intuition.

```json
{
  "type": "function",
  "function": {
    "name": "calculate",
    "description": "Evaluate a mathematical expression safely.",
    "parameters": {
      "type": "object",
      "properties": {"expression": {"type": "string"}},
      "required": ["expression"],
      "additionalProperties": false
    }
  }
}
```

See [tool_improvements.md](tool_improvements.md) § "Calculate" for the known limitation around `eval` and the planned AST-based replacement.

---

## 10. `create_file` — Create or overwrite

Write a new file with given content. Creates parent directories if needed.

- **`filename`** *(string, required)* — path. Resolved and constrained to the project directory via `assert_within_project`.
- **`content`** *(string, required)* — full file content.

Atomic write via `tempfile.NamedTemporaryFile` + `os.replace` — a crash mid-write can't leave a partial file. Default mode is `0o644`; pass `make_executable=True` for `0o755`.

```json
{
  "type": "function",
  "function": {
    "name": "create_file",
    "description": "Create a new text file (and any parent dirs) with given content.",
    "parameters": {
      "type": "object",
      "properties": {
        "filename": {"type": "string"},
        "content":  {"type": "string"}
      },
      "required": ["filename", "content"],
      "additionalProperties": false
    }
  }
}
```

For partial edits, use `edit_file` instead.

---

## 11. `edit_file` — Surgical edit

In-place edit with three modes — pick **exactly one** per call.

| Mode | When to use |
|---|---|
| `find_replace` | The snippet is unique and counting lines is awkward. Errors on 0 or 2+ matches. |
| `replace_range` | You know the inclusive `[start_line, end_line]` to replace. |
| `insert` | Add new lines without disturbing existing ones. |

- **`filename`** *(string, required)* — path. Constrained to the project directory.
- **`mode`** *(enum, required)* — `find_replace` | `replace_range` | `insert`.

**`find_replace`:**

- **`search_text`** *(string, required)* — exact substring to find.
- **`replacement`** *(string, required)* — text to insert.
- **`replace_all`** *(bool, default `false`)* — replace every occurrence (default requires exactly one match).

**`replace_range`:**

- **`start_line`** *(int, required)* — 1-indexed first line of the range.
- **`end_line`** *(int, required)* — 1-indexed last line of the range (inclusive).
- **`replacement`** *(string, required)* — text to insert.

**`insert`:**

- **`line`** *(int, required)* — insert AFTER this line. `0` = top of file, `total_lines` = append at end. Values past the end clamp to "append."
- **`content`** *(string, required)* — text to insert.

**Behavior.** Atomic write via `tempfile.mkstemp` + `os.replace` (no partial files). No `.bak` files are created — git history is the undo log. Returns a short summary plus the unified diff from `git diff`. Path safety enforced via `assert_within_project`.

```json
{
  "type": "function",
  "function": {
    "name": "edit_file",
    "description": "Surgical file editor. Three modes: find_replace, replace_range, insert. Use create_file for full-file rewrites. Each call picks ONE mode and passes that mode's keyword args.",
    "parameters": {
      "type": "object",
      "properties": {
        "filename":     {"type": "string"},
        "mode":         {"type": "string", "enum": ["find_replace","replace_range","insert"]},
        "search_text":  {"type": "string"},
        "replacement":  {"type": "string"},
        "replace_all":  {"type": "boolean"},
        "start_line":   {"type": "integer"},
        "end_line":     {"type": "integer"},
        "line":         {"type": "integer"},
        "content":      {"type": "string"}
      },
      "required": ["filename", "mode"],
      "additionalProperties": false
    }
  }
}
```

**Atomic-task test:** before calling `edit_file`, ask yourself "Can I describe the change in ONE sentence with ONE clear success criterion?" If not, decompose further.

---

## 12. `git` — Whitelisted git subcommands

Wraps a curated subset of git. The model cannot pass arbitrary arguments — it picks one of the allowed `command` values and passes its specific args.

- **`command`** *(enum, required)* — `add`, `commit`, `diff`, `status`, `log`, `checkout`, `branch`, `rm`, `merge`, `stash`, `reset`, `revert`.
- **`args`** *(string, optional)* — additional positional arguments passed to git. Use with care — there's no shell escaping because the call is forwarded directly.

```json
{
  "type": "function",
  "function": {
    "name": "git",
    "description": "A tool to handle Git functionality. Supports commands such as add, commit, and more.",
    "parameters": {
      "type": "object",
      "properties": {
        "command": {"type": "string"},
        "args":    {"type": "string"}
      },
      "required": ["command"],
      "additionalProperties": false
    }
  }
}
```

Example:

```
git(command="status")
git(command="diff")
git(command="log", args="-n 5 --oneline")
git(command="checkout", args="-b feature/foo")
```

---

## 13. `grep` — Code search

Search tracked files for a term.

- **`term`** *(string, required)* — literal substring by default.
- **`regex`** *(bool, optional)* — treat `term` as a Python regular expression.
- **`case_insensitive`** *(bool, optional)* — ignore case.

Skips files larger than 1 MB and binary files. Capped at 200 results. Returns file paths, line numbers, and matching content.

```json
{
  "type": "function",
  "function": {
    "name": "grep",
    "description": "Search tracked files for a given term and return file paths, line numbers, and matching content.",
    "parameters": {
      "type": "object",
      "properties": {
        "term":            {"type": "string"},
        "regex":           {"type": "boolean"},
        "case_insensitive":{"type": "boolean"}
      },
      "required": ["term"],
      "additionalProperties": false
    }
  }
}
```

---

## 14. `update` — Self-update

Check GitHub Releases for a newer Codey version. With explicit user confirmation, downloads the wheel, verifies its SHA-256 against the asset's `digest` field, and runs `pip install --upgrade`.

Takes no parameters.

```json
{
  "type": "function",
  "function": {
    "name": "update",
    "description": "Check for a newer version of Codey and, with explicit user confirmation, install it from GitHub Releases. Always prompts the user before running pip.",
    "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": false}
  }
}
```

**Behavior.**

- The model **must** ask via the `ask` tool before invoking `update` — it never installs silently.
- If no update is available, returns `"Codey is already up to date (vX.Y.Z)."` without prompting.
- The release wheel's SHA-256 is read from the asset `digest` field; verification is skipped only if the digest is absent.
- Equivalent to running `codey update` from the CLI.

For internals, safety properties, and known limitations of every tool, see [tool_improvements.md](tool_improvements.md).