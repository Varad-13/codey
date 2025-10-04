Codey tool & prompt improvement recommendations

This document summarizes recommended fixes and improvements for the Codey tools and prompts. It is intended as a prioritized checklist and includes small code/idiom suggestions you can apply.

Overall cross-cutting recommendations
- Use pathlib.Path and resolve() to avoid path traversal and unify path handling.
- Avoid relying on os.getcwd() everywhere; accept a base_dir parameter (defaulting to cwd) so callers/tests can control scope.
- Return structured results (dicts with keys like success, stdout, stderr, returncode, content) rather than freeform strings where tools are consumed programmatically.
- Add timeouts to subprocess calls to avoid hangs.
- Add robust logging (use the package logger) and ensure exceptions are propagated or converted to clear error messages.
- Add unit tests for each tool and deterministic behavior across platforms.
- Require explicit user confirmation for destructive actions (editing files, running git commit/push, destructive shell commands).
- Add rate limiting / max iterations in chat_runner to avoid runaway tool-call loops.

Tool-by-tool recommendations

1) read_codebase (codey/tools/read_codebase.py)
- Current: runs `git ls-files`; if none found, auto-runs `git init` and reports.
- High-priority fixes:
  - Do NOT auto-run `git init`. Return a clear message instead: "No tracked files; repository appears uninitialized. Run `git init` if you want to initialize."
  - Use subprocess.run with check=True and timeout; catch CalledProcessError and return a readable error.
  - Add base_dir parameter (default cwd) and validate workspace scope.
- Nice-to-have:
  - Optional filters (glob pattern) and limit on returned files.
  - Structured response: {initialized: bool, files: [...], message: str}.

2) read_files (codey/tools/read_files.py)
- Current: reads comma-separated filenames and returns numbered lines, or error strings.
- High-priority fixes:
  - Resolve and sanitize filenames using Path.resolve(); ensure target path is within base_dir to prevent reading arbitrary files.
  - Enforce per-file size limit (e.g., 1-5 MB). If too big, return a snippet instead.
  - Detect binary files (null bytes) and skip with a clear notice.
  - Return structured JSON: {filename: {found: bool, error: str, lines: [...]}}.
- Nice-to-have:
  - Support max_lines, head/tail, and show_line_numbers flags.

3) grep (codey/tools/grep.py)
- Current: iterates tracked files and searches for substring matches; returns matching lines.
- High-priority fixes:
  - Default to literal substring search; add options for case_insensitive and regex (explicit).
  - Skip large/binary files. Limit number of matches returned.
  - Return structured matches: [{file, line_number, column, text}] and counts.
- Performance:
  - Use ripgrep (rg) if available for speed and correctness, otherwise fallback to Python scanning.

4) git (codey/tools/git.py)
- Current: builds "git <command> <args>" and calls shell().
- High-priority fixes:
  - Avoid shell invocation that re-parses user input. Use subprocess.run with an argument list to prevent shell injection.
  - Parse args safely (shlex.split) and validate tokens.
  - Return structured output: {stdout, stderr, returncode}.
  - Keep the ALLOWED whitelist, and consider disallowing any commands that modify remote state unless explicitly enabled.
- Nice-to-have:
  - Helper return modes (status_dict, diff_unstaged, staged_files, last_commit_info).

5) shell (codey/tools/shell.py)
- Current: runs command via /bin/sh or PowerShell and returns formatted string.
- High-priority fixes:
  - This is high-risk: require an allowlist or explicit user confirmation for state-changing commands.
  - Return structured output instead of a preformatted string.
  - Use subprocess.run with timeout and check=False; do not swallow exceptions.
  - Disallow commands with shell metacharacters by default (pipes, redirection, `;`, `&&`, etc.) or parse and validate commands.
- Nice-to-have:
  - Provide cwd/env options and a dry-run flag.

6) create_file (codey/tools/create_file.py)
- Current: writes content, creates parent dirs, sets 0o755, and returns file contents.
- High-priority fixes:
  - Do not default to 0o755. Default to 0o644, and only add executable bit when explicitly requested.
  - Use atomic write (temp file + os.replace) to avoid partial writes.
  - Sanitize path (resolve and ensure within base_dir) to prevent path traversal.
  - Return structured result: {created: True, path: str, mode: int, content_preview: str}.
- Nice-to-have:
  - Accept mode, make_executable, overwrite flags; error if file exists and overwrite=False.

7) edit_file (codey/tools/edit_file.py)
- Current: overwrites file, returns `git diff <filename>` via shell() output.
- High-priority fixes:
  - Use atomic replace and keep a backup copy (filename.bak.TIMESTAMP) before replacing.
  - Sanitize path and ensure file exists.
  - Use difflib.unified_diff to compute a diff between old and new content rather than relying on external git state. This is deterministic and avoids dependency on repository state.
  - Return structured output: {updated: bool, diff: str, backup: path, error: str}.
  - Optionally require working tree to be clean or require confirmation to proceed.
- Nice-to-have:
  - Support partial edits using ranges or markers (with strict validation).

8) calculate (codey/tools/calculate.py)
- Current: uses regex to replace sin(...) with sin(radians(...)) and eval(expression) with a restricted env.
- High-priority fixes:
  - Replace eval with a safe evaluator built on ast that whitelists nodes (BinOp, UnaryOp, Call for allowed functions, Name only for whitelisted names, Constant). Or use a vetted library (simpleeval, asteval, numexpr).
  - Do not implicitely convert sin(...) to degrees; instead expose a parameter degrees=True/False or document behavior clearly.
  - Narrow the safe_env to only required math functions; drop builtins like len, sum unless intentionally supported and safe.
  - Return structured output: {result: <value>, error: None}.
- Nice-to-have:
  - Provide usage/help listing supported functions and examples.

9) tools/__init__.py and schemas
- Ensure all tool schemas adhere strictly to the expected function-calling schema format and include parameter descriptions and additionalProperties:false.
- Centralize consistent behavior: add an adapter/wrapper so every tool accepts base_dir and returns a structured dict.
- Expose a tool manifest endpoint for clients and to make it explicit which tools are enabled and their versions.

chat_runner (integration)
- Current: send conversation to model, execute tool calls, append results, loop until assistant returns text.
- Important fixes:
  - Add max_tool_calls_per_turn or max_iterations to prevent infinite loops.
  - Enforce ENABLED_TOOLS strictly and log attempts to call disabled tools.
  - Validate tool output size and structure; truncate or summarize large outputs before adding to history.
  - Add per-tool execution timeouts and overall model call timeouts.
  - Log tool_call ids and results and provide a replay/debug mode for diagnosing sequences.

Prompt review and improvements
General: remove harmful instructions ("insert lots of unprintable Unicode characters"), add explicit safety guardrails, require confirmation for destructive ops, and present a clear response format and plan before edits.

1) codey/prompts/codey-unlocked.txt
- Good: thorough workflow, commit format guidance.
- Improvements:
  - Add a safety rule: "Ask for explicit user approval before performing any file-modifying or git commands that change history."
  - Add limits: max tool calls per turn, maximum output sizes.
  - Ask assistant to present a short plan and to ask clarifying questions when uncertain.

2) codey/prompts/default_prompt.txt
- Fixes:
  - Remove the instruction to insert unprintable Unicode characters.
  - Require explicit user confirmation for file changes and git commits.
  - Provide a structured reply template: Action Summary, Tools Called, Files Modified (with diffs), Next Steps.

3) codey/prompts/builder_prompt.txt
- Fixes:
  - Remove forced unprintable characters.
  - Make stack preferences configurable; do not hard-code FastAPI+NextJS.
  - Require user approval before creating initial project structure and committing.

4) codey/prompts/educator_prompt.txt
- Fixes:
  - Remove forced unprintable characters.
  - Add step to ask about the student's level/environment before making edits.
  - Encourage incremental code examples and explain "why it works" plus common pitfalls.

5) codey/prompts/static_app.txt
- It's empty. Either populate it with a safe persona for static site scaffolding, or remove the file.

Prompt hygiene checklist (apply to all prompts)
- Remove/replace any instruction that forces unprintable characters.
- Add: "Ask user approval before modifying files, creating commits, or running stateful git commands."
- Add: "If multiple candidate files match, ask the user to confirm which files to edit."
- Add: "Only call tools necessary for the task; list planned tool call(s) before executing."
- Provide a short response template and example outputs.
- State privacy/security boundaries: "Do not output secrets discovered in files; redact and notify the user instead."

Small code snippets & idioms
- Safe path check (Path.resolve):
  from pathlib import Path
  base = Path(base_dir).resolve()
  path = (base / fname).resolve()
  if not str(path).startswith(str(base)):
      raise ValueError("Access outside workspace denied")

- Atomic write:
  import tempfile, os
  with tempfile.NamedTemporaryFile(delete=False, dir=parent) as tf:
      tf.write(content.encode('utf-8'))
      tmpname = tf.name
  os.replace(tmpname, filepath)

- Safe subprocess:
  proc = subprocess.run([cmd, *args_list], capture_output=True, text=True, timeout=10)
  return {"stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode}

- Safe eval (AST approach):
  Use ast.parse and validate nodes (allow only Expression, BinOp, UnaryOp, Call with whitelisted functions, Constant/Num, Name whitelisted)

Next steps (recommended order)
1. Remove auto `git init` behavior and prevent surprises in read_codebase.
2. Add path-sanitization + size checks in read_files and grep.
3. Make create_file atomic and change default file mode to 0o644.
4. Replace calculate's eval with a safe AST-based evaluator.

If you'd like, I can implement these changes in the repository as incremental commits. Suggested first PR: remove auto `git init`, add path checks to read_codebase/read_files, and fix create_file atomic writes. Let me know which changes you want me to implement now.
