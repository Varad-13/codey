# Introduction

**Codey** is an in-terminal AI coding assistant. It exposes an OpenAI-compatible chat model with a tool layer that can read, edit, search, and execute code on your local machine — all from a single REPL in your terminal.

It's designed for developers who want AI assistance **inside** their existing workflow, not a separate web app. You point it at a project directory, talk to it in natural language, and it calls tools (file reads, edits, shell commands, web fetches, git operations, subagents) to get work done.

## Who it's for

- **Application developers** who want a coding copilot that can actually run commands and edit files, not just chat.
- **DevOps / infra work** where you want to script, search, and refactor across a repo without leaving the terminal.
- **Research and prototyping** — the `web` tool browses docs and live pages, the `delegate` tool spawns isolated subagents for parallelizable subtasks.

## How it differs from a plain chatbot

| Plain chatbot | Codey |
|---|---|
| You copy-paste code into the prompt | The model **reads your files** via `read_files` / `read_codebase` |
| You apply suggestions manually | The model **edits files** via `edit_file` / `create_file` |
| You run suggested commands yourself | The model **runs commands** via `shell` / `terminal` |
| You switch tabs to look things up | The model **browses the web** via `web` (Playwright Chromium) |
| Single-threaded reasoning | The model **delegates** parallel sub-tasks via `delegate` |
| Stateless | **Multi-session history** per project, with token & cost tracking |
| Generic prompts | Switchable **personas** with different models and system prompts |

## Key capabilities

- **Streaming chat REPL** with ANSI color, multi-line input (`Ctrl+N`), and a session picker on launch.
- **15 tools** covering filesystem, shell, git, search, math, web, vision, subagent delegation, and self-update. See [tools.md](tools.md).
- **Provider auto-detect** — works with OpenAI (`sk-proj-…`) or OpenRouter (`sk-or-…`) out of the box; switchable via `PROVIDER`.
- **Multi-session persistence** — every project directory gets its own session log under `~/.codey/history/<project>-<hash>/`.
- **Subagent delegation** — `delegate(task, tools=[...], files=[...])` runs a fresh agent loop in isolation, ideal for research or atomic code edits.
- **Vision & attachments** — paste a file path to inline a file, or type `@image` to attach the current clipboard image.
- **Interactive terminal sessions** — `terminal` keeps a long-lived process alive across multiple `send`/`peek` calls, perfect for `npm init` or `apt-get` wizards.
- **Context hygiene** — `trim_history` truncates oversized tool results, drops orphan tool calls, and `chat_runner._compress_context` summarizes older turns when the conversation grows past ~500K characters.
- **Self-update** — `codey update` polls GitHub Releases, verifies SHA-256 of the wheel asset, and reinstalls via pip. The startup update check is cached for 6 hours.

## Design principles

1. **Tool-first, not chat-first.** When the user asks for something Codey can do, the model calls a tool — it doesn't describe how to do it.
2. **Inspect before acting.** Reading code, listing files, and checking git state always come before edits.
3. **Small, focused commits.** The default prompt includes a commit-message format and asks the model to make incremental changes.
4. **Ask before destructive ops.** `ask` is a first-class tool. The model is instructed to confirm framework choices, file overwrites, and ambiguous refactors before acting.
5. **Delegate liberally.** Anything that takes more than a couple of tool calls should be handed to `delegate`, which scopes tools and files for the subagent.
6. **Determinism where it matters.** File edits are atomic (`tempfile.mkstemp` + `os.replace`), version comparison prefers `packaging.version.Version`, and tool calls honor `ENABLED_TOOLS` strictly.

## Where to go next

- New here? → [installation.md](installation.md), then [usage.md](usage.md).
- Want to tweak behavior? → [configuration.md](configuration.md).
- Curious how it works? → [architecture.md](architecture.md).
- Looking for a specific tool? → [tools.md](tools.md).
- Want to extend Codey? → [tool_improvements.md](tool_improvements.md) (internals + extension points), then [contributing.md](contributing.md).
- Hit a snag? → [faq.md](faq.md) and [logging.md](logging.md).