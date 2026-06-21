from .ask import ask, schema as ask_schema
from .calculate import calculate, schema as calculate_schema
from .create_file import create_file, schema as create_file_schema
from .delegate import delegate, schema as delegate_schema
from .edit_file import edit_file, schema as edit_file_schema
from .git import Git, schema as git_tool_schema
from .grep import grep, schema as grep_schema
from .read_codebase import read_codebase, schema as read_codebase_schema
from .read_files import read_files, schema as read_files_schema
from .shell import shell, schema as shell_schema
from .terminal import terminal, schema as terminal_schema
from .web import web, schema as web_schema

TOOL_MAP = {
    "ask":           ask,
    "shell":         shell,
    "terminal":      terminal,
    "delegate":      delegate,
    "web":           web,
    "calculate":     calculate,
    "read_codebase": read_codebase,
    "read_files":    read_files,
    "edit_file":     edit_file,
    "create_file":   create_file,
    "git":           Git(),
    "grep":          grep,
}

tools = [
    ask_schema,
    shell_schema,
    terminal_schema,
    delegate_schema,
    web_schema,
    calculate_schema,
    read_codebase_schema,
    read_files_schema,
    edit_file_schema,
    create_file_schema,
    git_tool_schema,
    grep_schema,
]