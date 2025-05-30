import os


def read_files(file_list: str) -> str:
    """
    Read one or more files given a comma-separated list of filenames.
    Return each file's content numbered by line for easier analysis.
    """
    base_dir = os.getcwd()
    outputs = []
    for fname in [f.strip() for f in file_list.split(",")]:
        filepath = os.path.join(base_dir, fname)
        if not os.path.isfile(filepath):
            outputs.append(f"**Error:** '{fname}' not found.")
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
            numbered_lines = [f"{i+1}: {line.rstrip()}" for i, line in enumerate(lines)]
            outputs.append(f"----- {fname} -----\n" + "\n".join(numbered_lines))
        except Exception as e:
            outputs.append(f"**Error reading {fname}:** {e}")
    return "\n\n".join(outputs)

schema = {
    "type": "function",
    "name": "read_files",
    "description": "Read files by comma-separated list, returning numbered lines for each file.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_list": {"type": "string", "description": "Comma-separated list of file paths to read."}
        },
        "required": ["file_list"],
        "additionalProperties": False
    }
}