"""
File summary: This code provides functions to create and write JSON or text files within a 'context' directory, ensuring the directory exists.
"""

from pathlib import Path
import json

CONTEXT_DIR = "context"

def ensure_context_dir(project_path: Path) -> Path:
    """
    Ensure the context/ folder exists inside project_path.
    Returns the Path object.
    """
    context_path = project_path / CONTEXT_DIR
    context_path.mkdir(exist_ok=True)
    return context_path

# -----------------------------
# JSON EXPORT
# -----------------------------
def export_json(data: dict, filename: str, project_path: Path):
    """
    Export data as JSON inside project_path/context/
    """
    context_path = ensure_context_dir(project_path)
    file_path = context_path / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# -----------------------------
# TEXT EXPORT
# -----------------------------
def export_text(text: str, filename: str, project_path: Path):
    """
    Export plain text inside project_path/context/
    """
    context_path = ensure_context_dir(project_path)
    file_path = context_path / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)