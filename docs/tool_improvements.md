# Tool Internals, Safety Properties & Known Limitations

This document describes how the tools work *under the hood* — the safety guarantees they make, the assumptions they rely on, and the things you should know if you're going to extend Codey or rely on it in production.

For the user-facing reference (schemas, parameters, examples), see [tools.md](tools.md). For configuration, see [configuration.md](configuration.md).

---

## Cross-cutting design properties

These properties apply across most or all tools.

### Atomic file writes

`edit_file` and `create_file` both write through `tempfile.NamedTemporaryFile` + `os.replace`, so a crash mid-write cannot leave a partial file on disk. **No `.bak` files are created.** The undo log is git history. If you need a safety net, make a git commit before letting Codey make non-trivial edits.

### Path safety

Every tool that accepts a user-supplied path runs it through `codey.utils.assert_within_project(filepath, base_dir)`, which raises `ValueError` if `realpath(filepath)` escapes `base_dir`. This is a hard guarantee, not a soft warning — the tool call fails with the error message surfaced back to the model.

The only tools that intentionally relax this are `read_files` (relative paths resolve from cwd) and `view_image` (accepts arbitrary absolute paths because users frequently reference screenshots in `~/Downloads`).

### Subprocess output decoding

`shell` and `terminal` route their captures through `codey.encoding_safety.safe_decode` / `run_capture`, which try UTF-8 with `errors="replace"` and fall back to `latin-1` if replacement characters remain. This means **child processes can emit arbitrary UTF-8 (including the C1 0x80–0x9F range) without ever raising `UnicodeDecodeError`**, even on Windows consoles locked to code page 437/1252.

Nothing else in the codebase or in the Python environment is mutated to make this work — `sys.stdout` encoding, environment variables, and stdio configuration are all left alone.

### Tool-call round limit

`chat_runner.process_history` enforces `MAX_TOOL_ROUNDS` (default 25). After the cap, the loop appends a `[Stopped after N tool-call rounds]` message and forces a final response. This is the only thing preventing a runaway tool-call loop from burning through your token budget.

### Disabled tools fail loudly

If the model calls a tool that's not in `ENABLED_TOOLS`, the tool result is the error string `"Error: tool '<name>' is not enabled in this session."` This is preferable to silent omission: it keeps tool-call IDs and orphan-pair cleanup working correctly.

### Image results flow as multimodal content

`view_image`, `web(action="screenshot")`, and `delegate` subagents can all return results with a `__image__` key. `chat_runner` converts those into multimodal tool-result content (`text` block + `image_url` block) so vision-capable models can see them in the next turn.

---

## Per-tool notes

### `read_codebase`

- **What it actually does:** runs `git ls-files` and prints the result. Returns a clear notice (no side effects) if the directory isn't a git repo.
- **Old behavior:** auto-ran `git init` if the repo was empty. **Removed** — that was surprising and potentially destructive. Users should run `git init` themselves.
- **Limits:** files larger than 1 MB are skipped; binary detection is done via null-byte scan.

### `read_files`

- Reads comma-separated filenames and returns numbered lines.
- Path safety: relative paths resolve from `os.getcwd()`; absolute paths are taken as-is.
- Limits: ~1 MB per file; binary files (null bytes in first 8 KB) are skipped with a notice.
- **Returns plain text, not structured JSON.** Tools consumed programmatically should wrap calls.

### `grep`

- Searches tracked files via Python's file scanner. Skips files larger than 1 MB and binary files.
- Capped at 200 results.
- Returns file paths, line numbers, and matching content.
- Future: optionally use `ripgrep` (`rg`) for speed when it's available on the system.

### `git`

- Whitelists a subset of git subcommands: `add`, `commit`, `diff`, `status`, `log`, `checkout`, `branch`, `rm`, `merge`, `stash`, `reset`, `revert`.
- Args are forwarded directly without shell escaping. **Don't** let the model pass arbitrary `;`-separated chains via the `args` parameter — the wrapper currently doesn't parse/shlex them.
- Currently no allowlist filter for "state-changing" commands (`push`, `force-push`, etc.) beyond the subcommand whitelist itself.

### `shell`

- One-shot, non-interactive.
- Uses `powershell -Command` on Windows, `/bin/sh -c` on Unix.
- 30-second default timeout. The model can pass a custom `timeout` via... actually no, the current schema only exposes `command`. Timeouts are hardcoded for now.
- **High-risk surface.** Anyone using `ENABLED_TOOLS=shell` is giving the model arbitrary command execution. Pair with `CONFIRM_SHELL=true` for interactive supervision.

### `terminal`

- Stateful: each `session_id` holds a `subprocess.Popen` plus a buffered output queue.
- A dedicated reader thread accumulates chunks; `drain(settle, timeout)` returns when output stalls for `settle` seconds or `timeout` is reached.
- On Windows, uses `powershell -Command`. On Unix, uses `/bin/sh -c`. (The "shell" tool uses the same shims.)
- Multiple concurrent sessions are supported; pick distinct `session_id` values.
- Processes that exit during a `send` / `peek` are cleaned up automatically and a `[Process exited with code N]` note is appended to the result.

### `create_file`

- Atomic write (`tempfile.mkstemp` + `os.replace`). Creates parent directories.
- Default mode `0o644`. Pass `make_executable=True` (when supported by the schema) for `0o755`.
- Path safety via `assert_within_project`.
- For partial edits, use `edit_file` instead — don't rewrite whole files via `create_file` for small changes.

### `edit_file`

- Three modes, pick exactly one per call: `find_replace`, `replace_range`, `insert`.
- Atomic write — never partial files.
- `find_replace` errors on 0 matches (with a hint to check whitespace) or 2+ matches (with line numbers). Pass `replace_all=True` to bypass the uniqueness check.
- `replace_range` errors on out-of-range or inverted ranges.
- `insert` clamps `line` past EOF to "append at end."
- Path safety via `assert_within_project`.
- **No backup files.** Git is the undo log.

### `calculate`

- Sandboxed math eval. Supports standard arithmetic, parentheses, and a whitelist of `math` functions.
- **Trig functions are interpreted in radians** (the implementation rewrites `sin(x)` → `sin(radians(x))`).
- **Current limitation:** uses Python `eval()` under a restricted namespace. This is *safer* than unrestricted eval (no builtins, no attribute access) but not bulletproof — see "Known limitations" below.
- Returns the computed value as a string.

### `ask`

- Pure stdio. Prints a colored prompt and reads a single line.
- If `options` is provided, the user can pick by number; the tool returns the option text.
- EOF / Ctrl+C returns `"(no response)"` rather than raising — this is intentional so the model can recover gracefully from an interrupted question.

### `view_image`

- Accepts absolute paths or paths relative to `os.getcwd()`.
- Calls `realpath` so symlinks are resolved before existence checks.
- Supported formats: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`.
- Returns the image as a base64 data URL inside a vision content block.
- Errors return string messages (not exceptions) so the model can self-correct.

### `web`

- Playwright Chromium, single-threaded executor so the asyncio loop never touches the main thread.
- Auto-installs Chromium on first use if missing (~120 MB).
- `CODEY_WEB_HEADLESS` toggles headed vs headless.
- All Playwright actions return strings (or image content blocks for `screenshot`).
- **Headed mode shows a browser window.** Set `CODEY_WEB_HEADLESS=true` on servers.

### `update`

- **Always** prompts via the CLI confirmation prompt before running pip.
- Verifies SHA-256 from the asset's `digest` field; verification is skipped only if the digest is missing.
- The startup update check is cached for 6 hours per user (`~/.cache/codey/update_check.json`).
- `CODEY_NO_UPDATE_CHECK=1` disables the startup check entirely; it does **not** affect `codey update`.

### `delegate`

- Recursive chat loop with its own system prompt and 25-round cap.
- **Cannot call back into the orchestrator** — there's no parent-tool access from inside the subagent. Communication is one-way: subagent returns a summary, orchestrator uses it.
- Tool scope defaults to a curated subset (`web`, `shell`, `read_files`, `grep`, `create_file`, `edit_file`, `git`, `calculate`).
- Files passed via `files=[]` are inlined into the subagent's task prompt as fenced snippets — no cross-process file sharing.
- Suggested patches via `suggested_patch` are forwarded as a hint, not enforced.

---

## Known limitations

These are the sharp edges you should be aware of when relying on Codey.

### `calculate` uses `eval`

The current implementation pre-processes the expression to wrap trig functions, then calls `eval(expression, {"__builtins__": {}}, safe_env)`. The safe namespace includes a curated set of `math` functions, but it's still `eval`. A sufficiently creative expression can potentially trigger behavior outside the intended math scope (e.g. via dunder attributes on the whitelisted callables). The planned replacement is an AST-based evaluator that whitelists node types (`BinOp`, `UnaryOp`, `Call` to whitelisted functions, `Constant`, whitelisted `Name`) — see "Planned work" below.

### `shell` is unrestricted

Any command the model decides to run will run, modulo `CONFIRM_SHELL`. There is no command allowlist, no working-directory sandbox beyond the OS-level user permissions, and no argument validation. If you need stronger isolation, set `ENABLED_TOOLS` to exclude `shell` and `terminal`, or run Codey inside a container.

### `git` doesn't shell-escape `args`

The `args` parameter is passed straight through. The model shouldn't pass `;`-separated chains because there's no shlex parsing — but if it does, the call will fail at the git level rather than being rejected up front.

### Context compression is lossy

`_compress_context` summarizes older turns with the same model. The summary is appended as a single user-role message. This is intentionally simple — it's a sliding window with a soft cap, not a true memory system. Long-running sessions will lose fine-grained detail from the early turns.

### Web tool runs headed by default

`CODEY_WEB_HEADLESS=false` opens a visible browser window. This is intentional for transparency — you can watch what the model is browsing. For headless servers, set the env var.

### Self-update trusts the GitHub API response

The release JSON is fetched over HTTPS with a 5-second timeout. The wheel's SHA-256 is verified against the asset `digest` field, but if GitHub omits the digest for some reason, verification is skipped (with no warning to the user). This is documented in [tools.md](tools.md) § `update`.

### `edit_file.find_replace` is whitespace-strict

The match is a literal string comparison. Trailing spaces, indentation differences, or line-ending mismatches will cause 0-match errors. The error message includes a hint to check whitespace.

---

## Extension points

If you're adding a new tool, follow these conventions:

1. **File layout:** `codey/tools/<name>.py` with a callable function and a `schema` dict.
2. **Schema:** use the OpenAI function-calling format with `additionalProperties: false`. Always include parameter descriptions.
3. **Atomicity:** write files through `tempfile.mkstemp` + `os.replace`. No `.bak` files.
4. **Path safety:** call `assert_within_project(path, base_dir)` for any user-supplied path.
5. **Subprocess decoding:** wrap `subprocess.run` with `encoding_safety.run_capture`. Never rely on the default stdio encoding.
6. **Timeouts:** set explicit timeouts on every blocking call.
7. **Errors as strings:** return error messages as strings so the model can self-correct.
8. **Image results:** if the tool produces visual output, return a dict with a `__image__` key (a base64 data URL) and a `text` description.
9. **Registration:** import the function and schema in `codey/tools/__init__.py`, then add them to both `TOOL_MAP` and `tools` (the list of schemas).
10. **Enabled by default:** add the tool name to the default `ENABLED_TOOLS` string in `config.py`.

Subagents (`delegate`) automatically pick up any new tool — there's no separate registry for them. The orchestrator just chooses which tools to grant via the `tools=[...]` parameter.

---

## Planned work

Roughly in priority order, the known TODOs that haven't landed yet:

1. **Replace `calculate`'s `eval` with an AST-based evaluator** that whitelists node types — eliminates the remaining sandbox surface.
2. **Stricter `shell` allowlist or per-command confirmation** — currently the whole tool is on/off.
3. **Shlex-parsing for `git`'s `args`** — prevent the model from injecting shell metacharacters.
4. **Optional `ripgrep` fallback in `grep`** — significant speedup on large repos.
5. **Structured tool results** — currently tools return freeform strings; switching to dicts would make programmatic consumption cleaner.
6. **Per-tool execution timeouts** — only `shell` and `terminal` have implicit timeouts today.

Each of these is small and well-scoped. PRs welcome — see [contributing.md](contributing.md).