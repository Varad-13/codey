import os

def read_files(file_list: str) -> str:
    """
    Read one or more files given a comma-separated list of filenames.
    Returns each file’s content or an error message if not found.
    """
    base_dir = os.getcwd()
    outputs = []
    for fname in [f.strip() for f in file_list.split(",")] :
        filepath = os.path.join(base_dir, fname)
        if not os.path.isfile(filepath):
            outputs.append(f"**Error:** '{fname}' not found.")
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read()
            outputs.append(f"----- {fname} -----\n{content}")
        except Exception as e:
            outputs.append(f"**Error reading {fname}:** {e}")
    return "\n\n".join(outputs)

schema = {
    "type": "function",
    "name": "read_files",
    "description": "Read one or more files given a comma-separated list.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_list": {"type": "string"}
        },
        "required": ["file_list"],
        "additionalProperties": False
    }
}
