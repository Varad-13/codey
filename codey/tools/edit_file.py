import os
from codey.tools.shell import shell

def edit_file(filename: str, operation: str, target: str = None, replacement: str = None) -> str:
    """
    Perform CRUD-like operations on a text file.
    
    operation: one of ["read", "replace", "insert_after", "delete"]
    target: text/line to match (for replace, insert_after, delete)
    replacement: new text (for replace or insert_after)
    
    Returns status + git diff if applicable.
    """
    if not os.path.isfile(filename):
        return f"Error: File '{filename}' not found."

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        updated = False

        if operation == "read":
            return "".join(lines)

        elif operation == "replace":
            new_lines = []
            for line in lines:
                if target in line:
                    new_lines.append(line.replace(target, replacement))
                    updated = True
                else:
                    new_lines.append(line)
            lines = new_lines

        elif operation == "insert_after":
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if target in line:
                    new_lines.append(replacement + "\n")
                    updated = True
            lines = new_lines

        elif operation == "delete":
            new_lines = []
            for line in lines:
                if target not in line:
                    new_lines.append(line)
                else:
                    updated = True
            lines = new_lines

        else:
            return f"Error: Unknown operation '{operation}'"

        if updated:
            with open(filename, "w", encoding="utf-8") as f:
                f.writelines(lines)
            diff_output = shell("git diff")
            return f"{operation.capitalize()} operation applied.\n\n{diff_output}"
        else:
            return f"No changes made. Target '{target}' not found."

    except Exception as e:
        return f"Error editing {filename}: {e}"


schema = {
    "name": "edit_file",
    "description": "Perform CRUD-like edits on a text file.",
    "input": {
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "Path to the file."},
            "operation": {
                "type": "string",
                "enum": ["read", "replace", "insert_after", "delete"],
                "description": "Type of operation to perform."
            },
            "target": {
                "type": "string",
                "description": "Target string/line to match for replace/insert/delete."
            },
            "replacement": {
                "type": "string",
                "description": "New text for replace or insert operations."
            }
        },
        "required": ["filename", "operation"]
    }
}
