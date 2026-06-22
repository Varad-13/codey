# Tools Documentation

Codey provides a set of tools designed to perform specific tasks within the chat interface. Below is a detailed overview of each tool available.

## 1. Shell Tool
- **Description**: Executes shell commands in the current working directory, using PowerShell on Windows or `/bin/sh` on Unix-like systems.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "shell",
 "description": "Run a shell/PowerShell command, non-interactive.",
 "parameters": {
 "type": "object",
 "properties": {
 "command": {"type": "string"}
 },
 "required": ["command"],
 "additionalProperties": False
 }
 }
 ```

## 2. Calculate Tool
- **Description**: Evaluates mathematical expressions safely, supporting functions like sin, cos, and basic arithmetic operations.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "calculate",
 "description": "Evaluate a mathematical expression safely.",
 "parameters": {
 "type": "object",
 "properties": {
 "expression": {"type": "string"}
 },
 "required": ["expression"],
 "additionalProperties": False
 }
 }
 ```

## 3. Read Codebase Tool
- **Description**: Lists all tracked files in the current git repository. Initializes the repository if it's empty.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "read_codebase",
 "description": "List files in the git repository (initializes if empty).",
 "parameters": {
 "type": "object",
 "properties": {},
 "required": [],
 "additionalProperties": False
 }
 }
 ```

## 4. Read Files Tool
- **Description**: Reads and returns content from one or more specified files, numbering lines for easier analysis.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "read_files",
 "description": "Read one or more files by comma-separated list, returning numbered lines for each file.",
 "parameters": {
 "type": "object",
 "properties": {
 "file_list": {"type": "string"}
 },
 "required": ["file_list"],
 "additionalProperties": False
 }
 }
 ```

## 5. Edit File Tool
- **Description**: Surgically edit an existing file with three modes. Pick ONE mode per call. For full-file rewrites, use `create_file` with `overwrite=True` instead.
- **Modes**:
  - **`find_replace`** -- exact-string find and replace. Use when the snippet is unique and counting lines is awkward. Pass `search_text`, `replacement`, and optionally `replace_all=True`. Errors on 0 matches (with a hint to check whitespace) or 2+ matches (with the matching line numbers).
  - **`replace_range`** -- replace lines `[start_line, end_line]` (1-indexed, inclusive) with `replacement`. Use when the change spans a known inclusive line range. Errors on out-of-range or inverted ranges.
  - **`insert`** -- insert `content` after line `line` (0 = top of file, total = end of file). Use when adding new lines without disturbing existing ones.
- **Behavior**:
  - Atomic write via `tempfile.mkstemp` + `os.replace` (no partial files).
  - No backup files are created. Git history is the undo log -- use `git` tool to review or revert.
  - Returns a short summary plus the unified diff from `git diff`.
  - Path safety enforced via `assert_within_project`.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "edit_file",
 "description": "Surgical file editor. Three modes: find_replace, replace_range, insert. Use create_file for full-file rewrites. Each call picks ONE mode and passes that mode's keyword args. Use find_replace when the snippet is unique and line counts are awkward (exact-string match; replace_all=True to replace every occurrence). Use replace_range when the change spans a known inclusive line range [start_line, end_line]. Use insert to add new lines after a given line (0 = top of file, total = append at end). Returns a short summary plus the unified diff from `git diff`.",
 "parameters": {
 "type": "object",
 "properties": {
   "filename": {"type": "string", "description": "Path to the file (relative to cwd or absolute)."},
   "mode": {"type": "string", "enum": ["find_replace", "replace_range", "insert"], "description": "Which edit mode to use. Pick exactly one."},
   "search_text": {"type": "string", "description": "[find_replace] Exact substring to find. Must be non-empty. If 2+ matches and replace_all=False, the call errors out with the line numbers."},
   "replacement": {"type": "string", "description": "[find_replace, replace_range] Text to insert in place of the match or the replaced line range. May contain newlines."},
   "replace_all": {"type": "boolean", "default": false, "description": "[find_replace] If true, replace every occurrence of search_text. If false (default), require exactly one match."},
   "start_line": {"type": "integer", "description": "[replace_range] First line of the inclusive range to replace. 1-indexed."},
   "end_line": {"type": "integer", "description": "[replace_range] Last line of the inclusive range to replace. 1-indexed."},
   "line": {"type": "integer", "description": "[insert] Insert content AFTER this line. 0 = top of file, total_lines = append at end."},
   "content": {"type": "string", "description": "[insert] Text to insert. Include a trailing newline if you want it on its own line."}
 },
 "required": ["filename", "mode"],
 "additionalProperties": false
 }
 }
 ```

## 6. Create File Tool
- **Description**: Creates a new text file with specified content.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "create_file",
 "description": "Create a new text file (and any parent dirs) with given content.",
 "parameters": {
 "type": "object",
 "properties": {
 "filename": {"type": "string"},
 "content": {"type": "string"}
 },
 "required": ["filename", "content"],
 "additionalProperties": False
 }
 }
 ```

## 7. Edit File Partial Tool
- **Description**: Partially edits a file—can insert, delete, or replace lines based on specified range.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "edit_file_partial",
 "description": "Partially edit a file by inserting, deleting, or replacing lines.",
 "parameters": {
 "type": "object",
 "properties": {
 "filename": {"type": "string"},
 "mode": {"type": "string", "enum": ["insert", "delete", "replace"]},
 "start_line": {"type": "integer"},
 "end_line": {"type": "integer"},
 "content": {"type": "string"}
 },
 "required": ["filename", "mode", "start_line"],
 "additionalProperties": False
 }
 }
 ```

## 8. Edit Files by String Tool
- **Description**: Searches and replaces a string across multiple files. By default, it performs a dry run; changes can be applied if specified.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "edit_files_by_string",
 "description": "Search and replace a string across multiple files (case-sensitive).",
 "parameters": {
 "type": "object",
 "properties": {
 "file_list": {"type": "string"},
 "search_string": {"type": "string"},
 "replace_string": {"type": "string"},
 "apply": {"type": "boolean"}
 },
 "required": ["file_list", "search_string", "replace_string"],
 "additionalProperties": False
 }
 }
 ```

## 9. Git Tool
- **Description**: Handles various Git commands. Can perform operations like add, commit, diff, status, etc.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "git",
 "description": "A tool to handle Git functionality. Supports commands such as add, commit, and more.",
 "parameters": {
 "type": "object",
 "properties": {
 "command": {"type": "string"},
 "message": {"type": "string"},
 "branch": {"type": "string"},
 "files": {"type": "string"},
 "args": {"type": "string"}
 },
 "required": ["command"],
 "additionalProperties": False
 }
 }
 ```

## 10. Grep Tool
- **Description**: Searches recursively in the repository for files containing a specified search term, returning matching lines with file paths and line numbers.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "grep",
 "description": "Search tracked files for a given term and return file paths, line numbers, and matching content.",
 "parameters": {
 "type": "object",
 "properties": {
 "term": {"type": "string"}
 },
 "required": ["term"],
 "additionalProperties": False
 }
 }
 ```

## 11. Update Tool
- **Description**: Checks GitHub Releases for a newer Codey version; with explicit user confirmation, downloads the wheel, verifies its SHA256, and runs `pip install --upgrade --force-reinstall`.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "update",
 "description": "Check for a newer version of Codey and, with explicit user confirmation, install it from GitHub Releases. Always prompts the user before running pip.",
 "parameters": {
 "type": "object",
 "properties": {},
 "required": [],
 "additionalProperties": false
 }
 }
 ```
- **Behavior**:
  - The model *must* ask the user via the `ask` tool before invoking `update` — it never installs silently.
  - If no update is available, returns `"Codey is already up to date (vX.Y.Z)."` without prompting.
  - The release wheel's SHA256 is read from the asset `digest` field; verification is skipped only if the digest is absent.

## Conclusion
Each of these tools ensures smooth and intuitive interactions within the Codey chat interface, providing a comprehensive functionality set for developers.