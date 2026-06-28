# Logging

Codey uses Python's standard `logging` module for diagnostic output. The logger is named `codey` and is configured in `codey/chat_runner.py`.

## Current behavior

By default, the `codey` logger is wired to a `logging.NullHandler`. **No log file is written, and no log output appears on stderr or stdout.** This is intentional — the chat REPL is the user-facing surface, and log noise would interfere with the prompt.

The `chat_runner` module exposes an `ENABLE_LOGGING` flag (currently `False`) that, if you flip it on, attaches a `FileHandler` writing to `codey.log` in the current working directory:

```python
# codey/chat_runner.py
ENABLE_LOGGING = False

if ENABLE_LOGGING:
    fh = logging.FileHandler(os.path.join(os.getcwd(), 'codey.log'))
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(fh)
else:
    logger.addHandler(logging.NullHandler())
```

If you want file logging, edit `codey/chat_runner.py` to set `ENABLE_LOGGING = True` and reinstall (or run from a source tree with `pip install -e .`).

## Enabling logging from your own code

If you're embedding Codey or debugging from a script, the cleanest path is to attach your own handler to the `codey` logger — don't modify the source:

```python
import logging
from codey import chat_runner

logger = logging.getLogger("codey")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
logger.propagate = False   # silence the root logger
```

`logger.propagate = False` is important — `chat_runner` sets it so the root logger doesn't double-print.

## What gets logged

When `ENABLE_LOGGING = True`, the following events are written to `codey.log`:

| Level | Event |
|---|---|
| `DEBUG` | Every tool call: `TOOL_CALL name=<name>` |
| `DEBUG` | Every tool result: `TOOL_RESULT name=<name>` |
| `INFO` | Context compression: `Context compressed: summarized N messages` |
| `WARNING` | Context compression failure (the model call to summarize failed) |
| `ERROR` | Unknown tool call: `Error: Unknown tool '<name>'` |
| `ERROR` | Tool exception: `Error executing tool '<name>': <error>` |

## What gets shown to the user (separately)

The user-facing REPL uses plain ANSI-colored `print()` for everything visible:

- **Green** — model streaming text (`Codey: ...`).
- **Magenta** — tool calls and tool results (when `SHOW_TOOL_CALLS=true` / `SHOW_TOOL_RESULTS=true`).
- **Cyan** — `ask` questions.
- **Yellow** — subagent invocations (`delegate`).
- **Yellow + bold** — startup update notice (single line on stderr).

These are not log records; they're direct terminal writes controlled by the `SHOW_TOOL_CALLS`, `SHOW_TOOL_RESULTS`, and `CONFIRM_SHELL` environment variables. See [configuration.md](configuration.md).

## Update-check diagnostics

The update subsystem in `codey/update.py` writes nothing to stdout — all output goes to **stderr** so it doesn't tangle with the chat REPL. To see what it's doing, set:

```bash
# Linux / macOS
codey 2>codey-update.log

# PowerShell
codey 2>&1 | Tee-Object codey-update.log
```

The stderr stream is mostly silent unless `check_for_update()` finds a newer release (one-line notice) or `codey update` is invoked (release notes + pip output).

## Token and cost tracking

Token usage and (when reported by the API) per-turn cost are accumulated **in memory** during a session and persisted to the session's `.meta.json` file on every turn:

```json
{
  "prompt_tokens": 4521,
  "completion_tokens": 2107,
  "total_tokens": 6628,
  "cost": 0.021487
}
```

These counters are surfaced:

- In the **session picker** at launch (per-session column).
- In the **exit summary** (printed once when you type `exit` or `Ctrl+D`).
- In every saved session's `.meta.json`.

OpenRouter includes `cost` (USD) on the streamed `usage` object; OpenAI does not, so the `cost` field stays `0.0` for direct OpenAI usage unless you wrap the API yourself.

## Sample log file

If you flip `ENABLE_LOGGING = True` and exercise the system, your `codey.log` will look roughly like:

```
2024-05-12 14:32:11,234 - DEBUG - TOOL_CALL name=read_codebase
2024-05-12 14:32:11,502 - DEBUG - TOOL_RESULT name=read_codebase
2024-05-12 14:32:14,801 - DEBUG - TOOL_CALL name=read_files
2024-05-12 14:32:14,955 - DEBUG - TOOL_RESULT name=read_files
2024-05-12 14:32:22,118 - INFO - Context compressed: summarized 14 messages
2024-05-12 14:32:25,440 - DEBUG - TOOL_CALL name=edit_file
2024-05-12 14:32:25,612 - DEBUG - TOOL_RESULT name=edit_file
```

## Why the defaults are quiet

The chat REPL is the product. Log lines interleaving with model output would be confusing, and writing a log file on every machine that runs Codey feels intrusive. If you hit a bug, enabling file logging temporarily (or attaching your own handler) is a one-line change.