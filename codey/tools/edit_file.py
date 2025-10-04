import os
from codey.tools.shell import shell

def edit_file(filename: str, content: str) -> str:
    """
    Completely replace a file's content.
    
    Returns git diff showing the changes.
    """
    if not os.path.isfile(filename):
        return f"Error: File '{filename}' not found."
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        diff_output = shell(f"git diff {filename}")
        return f"File '{filename}' updated.\n\n{diff_output}"
        
    except Exception as e:
        return f"Error: {e}"


schema = {
    "type": "function",
    "function": {
        "name": "edit_file",
        "description": "Replace entire file content. First read the file with read_file, then write back the complete modified content.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Path to the file."
                },
                "content": {
                    "type": "string",
                    "description": "Complete new file content."
                }
            },
            "required": ["filename", "content"]
        }
    }
}