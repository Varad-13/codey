from .shell import shell, schema as shell_schema
from .read_codebase import read_codebase, schema as read_codebase_schema
from .read_files import read_files, schema as read_files_schema
from .edit_file import edit_file, schema as edit_file_schema
from .calculate import calculate, schema as calculate_schema
from .create_file import create_file, schema as create_file_schema
from .edit_file_partial import edit_file_partial, schema as edit_file_partial_schema
from .edit_files_by_string import edit_files_by_string, schema as edit_files_by_string_schema
from .git import Git, schema as git_tool_schema
from .grep import grep, schema as grep_schema

# Map tool names to their functions
TOOL_MAP = {
    "shell": shell,
    "calculate": calculate,
    "read_codebase": read_codebase,
    "read_files": read_files,
    "edit_file": edit_file,
    "create_file": create_file,
    "edit_file_partial": edit_file_partial,
    "edit_files_by_string": edit_files_by_string,
    "git": Git(),  # Instantiate GitTool
    "grep": grep,
}

# JSON schemas for model integration
tools = [
    shell_schema,
    calculate_schema,
    read_codebase_schema,
    read_files_schema,
    edit_file_schema,
    create_file_schema,
    edit_file_partial_schema,
    edit_files_by_string_schema,
    git_tool_schema,
    grep_schema,
]