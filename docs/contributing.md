# Contributing to Codey

Bug reports, feature requests, documentation fixes, and pull requests are all welcome. This document covers the workflow, the local dev setup, and the standards PRs are expected to meet.

## Code of conduct

Be respectful. Assume good faith. Critique ideas, not people. We're all here to ship a better dev tool.

## How to report a bug

Open an issue using the [bug report template](https://github.com/Varad-13/codey/issues/new?template=bug_report.md). Include:

1. **Version** — `codey --version`.
2. **OS + Python version** — output of `python --version` on the affected machine.
3. **Provider + model** — the line `Provider: ... Model: ...` from the startup banner.
4. **Reproduction steps** — exact commands or messages.
5. **Expected vs. actual behavior.**
6. **Full output** — any traceback, even if it looks noisy.

If the bug is security-sensitive, **email the maintainers first** rather than opening a public issue.

## How to request a feature

Open a regular GitHub issue with:

- The use case, not just the solution ("I want X because Y" beats "add Z").
- Any prior art (other tools that do this well).
- Whether you're willing to implement it.

## Development workflow

### 1. Fork & clone

```bash
git clone https://github.com/<your-username>/codey.git
cd codey
```

### 2. Set up the dev environment

```bash
python -m venv .venv
source .venv/bin/activate          # or .venv\Scripts\activate on Windows

pip install -e .
playwright install chromium        # only if you'll be testing the web tool
```

The `-e` (editable) install triggers `setup.py`'s Chromium download via `InstallWithPlaywright` / `DevelopWithPlaywright`.

### 3. Configure secrets

Create a `.env` in the repo root with at least:

```dotenv
OPENAI_API_KEY=sk-or-v1-...
# Optional:
# PROVIDER=openrouter
# UNLOCKED_MODEL=...
# CODEY_NO_UPDATE_CHECK=1
```

`.env` is in `.gitignore` — never commit it.

### 4. Branch

Use a descriptive branch name:

```bash
git checkout -b fix/edit-file-range-error
git checkout -b feat/ast-based-calculator
git checkout -b docs/improve-tool-reference
```

### 5. Make your changes

Follow the conventions below. Small, focused commits are easier to review than a single mega-commit.

### 6. Verify locally

```bash
# Smoke test: launch the REPL and confirm the banner looks right
codey

# Verify the CLI subcommands still work
codey --version
codey -V
```

There is no automated test suite yet — see "Roadmap" below. Manual verification is the norm for now.

### 7. Commit

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <concise description in present tense>

<detailed explanation of changes>
<reasoning for the approach>
<breaking changes / migration notes, if any>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`.

Example:

```
fix: edit_file range mode rejects inverted line ranges

Previously, calling replace_range with start_line > end_line would
silently produce an empty file because Python slicing tolerated it.
Now the tool returns a clear error and the user gets actionable
feedback from the model.

Adds unit-test coverage in tests/test_edit_file.py for the
boundary case where start_line == end_line.
```

### 8. Push & open a PR

```bash
git push origin <branch-name>
```

Then open a pull request against `master` on the upstream repo. Include:

- A clear title using the commit-message format.
- A short summary of **what** and **why**.
- A list of **how you tested** it.
- Screenshots or terminal output for user-visible changes.
- A note on any breaking changes or migration steps.

---

## Code standards

### Style

- **PEP 8** for Python. 4-space indentation, snake_case, type hints where they help.
- **No formatter enforced yet.** `black` and `ruff` are good choices; if you use them, run them before committing.
- Line length: keep it under 100 chars where reasonable.

### Architecture

Read [architecture.md](architecture.md) first. The codebase is small (~10 modules) — get the lay of the land before changing it.

A few rules of thumb:

- **Tools are pure functions** that accept primitive args and return either a string or a dict with a `__image__` key. Never raise from inside a tool — return an error string.
- **Path safety:** any tool that takes a user-supplied path runs it through `utils.assert_within_project`.
- **Atomic writes:** file mutations go through `tempfile.NamedTemporaryFile` + `os.replace`. No `.bak` files.
- **Subprocess decoding:** wrap `subprocess.run` with `encoding_safety.run_capture`. Never rely on the default stdio encoding.
- **Errors as data:** return error strings, not exceptions, from tool functions. Let `chat_runner.call_tool` catch unexpected exceptions and stringify them.

### Adding a new tool

See [tool_improvements.md](tool_improvements.md) § "Extension points" for the full checklist. Short version:

1. Create `codey/tools/<name>.py` with a function and a `schema` dict.
2. Add the schema to `codey/tools/__init__.py` (`TOOL_MAP` + `tools` list).
3. Add the tool name to the default `ENABLED_TOOLS` string in `config.py`.
4. Document it in [tools.md](tools.md).
5. Update the system prompt (`codey/prompts/codey-unlocked.txt`) if the model needs to know when to reach for it.

### Adding a new persona

1. Add the prompt file to `codey/prompts/`.
2. Register the `(model, prompt)` pair in `PERSONAS` in `config.py`.
3. Set `DEFAULT_PERSONA` to the new key (or leave it default and let users opt in via env var).

---

## Documentation standards

- **Match the code.** If you change a tool's signature, update [tools.md](tools.md) in the same PR.
- **Show, don't just tell.** Every tool reference should have a short example.
- **Cross-link generously.** [configuration.md](configuration.md), [tools.md](tools.md), [architecture.md](architecture.md), [tool_improvements.md](tool_improvements.md), and [faq.md](faq.md) all reference each other; keep the links alive.
- **No marketing copy.** State facts; let the reader decide.

---

## Release process

1. Bump `__version__` in `codey/__init__.py`.
2. Bump `version=` in `setup.py` (must match).
3. Build the wheel: `python -m build` (requires the `build` package).
4. Create a GitHub release with a `vX.Y.Z` tag.
5. Attach the wheel to the release. The `update.py` machinery will find it.

---

## Roadmap

Active areas where contributions are especially welcome:

- **AST-based `calculate`** (replaces `eval`) — see [tool_improvements.md](tool_improvements.md) § Planned work.
- **Per-tool execution timeouts** — only `shell` and `terminal` have implicit timeouts today.
- **Structured tool results** — switching from freeform strings to dicts would make programmatic consumption cleaner.
- **Automated test suite** — there's no `tests/` directory yet. A good first PR.
- **More personas** — `default_prompt.txt`, `builder_prompt.txt`, `educator_prompt.txt`, and `static_app.txt` exist but aren't wired into `PERSONAS`. Wire them up and write proper docs.

---

## Communication

- **GitHub Issues** for bugs and feature requests.
- **GitHub Discussions** for open-ended questions, design discussions, and "how do I…" questions.
- **Pull Request comments** for code review.

Maintainer: [@Varad-13](https://github.com/Varad-13).

Thanks for helping make Codey better.