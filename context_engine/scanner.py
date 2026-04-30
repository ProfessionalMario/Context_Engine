"""
File summary: This code manages project-local data storage and generates a structured tree representation of Python files within a project, utilizing caching and hashing for efficient change detection.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any
from debugflow.logger_system import log  # Restored Neural Link

# Administrative constraints
IGNORE_DIRS = {"__pycache__", ".git", "venv", ".env", ".pytest_cache", "models", "context"}
IGNORE_FILES = {".env", ".gitignore"}

class ProjectState:
    """
    Manages project-local storage. 
    Responsibility: Isolation of project data and relative path mapping.
    """
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.context_dir = self.root / "context"
        
        try:
            self.context_dir.mkdir(exist_ok=True)
            log.info(f"📁 Neural State Path: {self.context_dir}")
        except Exception as e:
            log.error(f"❌ Failed to create context directory: {e}")
            
        self.cache_path = self.context_dir / "cache.json"
        self.map_path = self.context_dir / "project_summary.json"

    def to_relative(self, full_path: Path) -> str:
        """Converts absolute paths to relative."""
        try:
            return str(full_path.relative_to(self.root))
        except ValueError:
            return str(full_path)

    def load_cache(self) -> dict:
        """Loads the local cache with validation logs."""
        if not self.cache_path.exists():
            log.warning(f"⚠️  No cache found at {self.cache_path}. Fresh scan initiated.")
            return {}
        try:
            with open(self.cache_path, "r") as f:
                data = json.load(f)
                log.info(f"🧠 Cache Loaded: {len(data)} file hashes recognized.")
                return data
        except (json.JSONDecodeError, Exception) as e:
            log.error(f"❌ Cache failure: {e}. Resetting to empty state.")
            return {}

    def save_state(self, cache_data: dict, map_data: dict):
        """Force-persists the current hash-table and the generated project map."""
        try:
            # We use 'w' to overwrite the empty ghost file
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
                f.flush() # Force the OS to write the buffer
                os.fsync(f.fileno()) # Ensure it hits the physical disk
            
            with open(self.map_path, "w", encoding="utf-8") as f:
                json.dump(map_data, f, indent=2)
                
            log.info(f"💾 State Physically Synchronized: {len(cache_data)} keys.")
        except Exception as e:
            log.error(f"❌ Physical Write Failure: {e}")

def scan_project_files(root_path: str):
    """Walks the tree and returns a list of viable Python files."""
    log.info(f"🔍 Scanning files in: {root_path}")
    root_path = Path(root_path).resolve()
    project_files = []

    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(".py") and file not in IGNORE_FILES:
                project_files.append(Path(root) / file)
    
    log.info(f"📂 Found {len(project_files)} Python nodes.")
    return project_files

def get_file_hash(file_path: Path) -> str:
    """Generates a hash for change detection."""
    try:
        if not file_path.exists():
            return ""
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except Exception as e:
        log.error(f"⚠️  Hash failed for {file_path.name}: {e}")
        return ""

def build_tree(root_path: str):
    """Generates the structural visualization for the JSON map."""
    root_path = Path(root_path).resolve()
    tree = {"root": root_path.name, "structure": []}

    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        rel_root = Path(root).relative_to(root_path)
        tree["structure"].append({
            "folder": "" if str(rel_root) == "." else str(rel_root),
            "files": [f for f in files if f.endswith(".py")]
        })
    return tree, None # Kept original return signature