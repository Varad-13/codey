import base64
import mimetypes
import os

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def view_image(path: str) -> dict:
    """
    Load an image file from disk so you can see it.
    Accepts absolute paths or paths relative to the current project directory.
    Returns the image as a vision content block.
    """
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    path = os.path.realpath(path)

    if not os.path.isfile(path):
        return f"Error: file not found: {path}"

    ext = os.path.splitext(path)[1].lower()
    if ext not in _IMAGE_EXTS:
        return f"Error: '{ext}' is not a supported image type. Use read_files for text files."

    try:
        with open(path, "rb") as f:
            data = f.read()
        mime = mimetypes.guess_type(path)[0] or "image/png"
        b64 = base64.b64encode(data).decode()
        return {
            "__image__": f"data:{mime};base64,{b64}",
            "text": f"Image: {path} ({len(data):,} bytes)",
        }
    except Exception as e:
        return f"Error reading image: {e}"


schema = {
    "type": "function",
    "function": {
        "name": "view_image",
        "description": (
            "Load an image file from disk so you can see it directly. "
            "Use for screenshots, diagrams, UI mockups, error screenshots, "
            "or any image you need to inspect. "
            "Accepts absolute paths or project-relative paths."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or project-relative path to the image file (.png, .jpg, .jpeg, .gif, .webp, .bmp)."
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        }
    }
}
