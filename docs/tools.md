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
- **Description**: Replaces the full content of an existing file.
- **Schema**:
 ```json
 {
 "type": "function",
 "name": "edit_file",
 "description": "Replace the full content of an existing file.",
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

## Conclusion
Each of these tools ensures smooth and intuitive interactions within the Codey chat interface, providing a comprehensive functionality set for developers.