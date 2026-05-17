import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from debugflow.logger_system import log 

# Administrative constraints (KEPT ORIGINAL NAMES)
IGNORE_DIRS = {"__pycache__", ".git", "venv", ".env", ".pytest_cache", "models", "context"}
IGNORE_FILES = {".env", ".gitignore"}

class ProjectState:
    """Manages project-local storage."""
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
        try:
            return str(full_path.relative_to(self.root))
        except ValueError:
            return str(full_path)

    def load_cache(self) -> dict:
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
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            with open(self.map_path, "w", encoding="utf-8") as f:
                json.dump(map_data, f, indent=2)
                
            log.info(f"💾 State Physically Synchronized: {len(cache_data)} keys.")
        except Exception as e:
            log.error(f"❌ Physical Write Failure: {e}")

def scan_project_files(root_path: str, user_ignores: Optional[List[str]] = None):
    """Walks the tree and returns a list of viable Python files."""
    log.info(f"🔍 Scanning files in: {root_path}")
    root_path = Path(root_path).resolve()
    project_files = []

    # Merge original IGNORE_DIRS with user_ignores
    effective_ignore_dirs = IGNORE_DIRS.copy()
    if user_ignores:
        effective_ignore_dirs.update(user_ignores)

    for root, dirs, files in os.walk(root_path):
        # Pruning the directory tree
        dirs[:] = [d for d in dirs if d not in effective_ignore_dirs]
        for file in files:
            # Check against original IGNORE_FILES and framework specific files
            if file.endswith(".py") and file not in IGNORE_FILES:
                if user_ignores and file in user_ignores:
                    continue
                project_files.append(Path(root) / file)
    
    log.info(f"📂 Found {len(project_files)} Python nodes.")
    return project_files

def build_tree(root_path: str, user_ignores: Optional[List[str]] = None):
    """Generates the structural visualization for the JSON map."""
    root_path = Path(root_path).resolve()
    tree = {"root": root_path.name, "structure": []}

    effective_ignore_dirs = IGNORE_DIRS.copy()
    if user_ignores:
        effective_ignore_dirs.update(user_ignores)

    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in effective_ignore_dirs]
        rel_root = Path(root).relative_to(root_path)
        
        tree["structure"].append({
            "folder": "" if str(rel_root) == "." else str(rel_root),
            "files": [f for f in files if f.endswith(".py") and (not user_ignores or f not in user_ignores)]
        })
    return tree, None

def get_file_hash(file_path: Path) -> str:
    try:
        if not file_path.exists():
            return ""
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except Exception as e:
        log.error(f"⚠️  Hash failed for {file_path.name}: {e}")
        return ""