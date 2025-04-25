# tools/__init__.py

from .shell import shell, schema as shell_schema
from .read_codebase import read_codebase, schema as read_codebase_schema
from .read_files import read_files, schema as read_files_schema
from .edit_file import edit_file, schema as edit_file_schema
from .create_file import create_file, schema as create_file_schema
from .calculate import calculate, schema as calculate_schema

# Map tool names to their functions
TOOL_MAP = {
    "shell": shell,
    "read_codebase": read_codebase,
    "read_files": read_files,
    "edit_file": edit_file,
    "create_file": create_file,
    "calculate": calculate,
}

# JSON schemas for model integration
tools = [
    shell_schema,
    read_codebase_schema,
    read_files_schema,
    edit_file_schema,
    create_file_schema,
    calculate_schema,
]
