"""
File summary: This code defines functions to manage the global configuration for a GGUF model path, including validation, saving, retrieval, and clearing.
"""

import json
import os
from pathlib import Path
from debugflow.logger_system import log

# Define the global config directory in the user's home folder
CONFIG_DIR = Path.home() / ".context_engine"
CONFIG_FILE = CONFIG_DIR / "config.json"

def ensure_config_dir():
    """Creates the hidden config directory if it doesn't exist."""
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def set_model_path(path: str) -> bool:
    """
    Validates and saves the GGUF model path to global config.
    Returns True if successful, False otherwise.
    """
    model_path = Path(path).resolve()
    
    # 1. Verification
    if not model_path.exists():
        log.error(f"❌ Verification Failed: File does not exist at {model_path}")
        return False
    
    if model_path.suffix.lower() != ".gguf":
        log.warning(f"⚠️  Warning: The file {model_path.name} does not have a .gguf extension.")
        # We still allow it in case of weird naming, but we warn the user.

    # 2. Persistence
    ensure_config_dir()
    config_data = {"model_path": str(model_path)}
    
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=2)
        log.info(f"✅ Configuration Saved: Model linked at {model_path}")
        return True
    except Exception as e:
        log.error(f"❌ Failed to write config: {e}")
        return False

def get_model_path() -> str:
    """
    Retrieves the saved GGUF path. 
    Returns None if no config exists.
    """
    if not CONFIG_FILE.exists():
        return None
    
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            path = data.get("model_path")
            if path and os.path.exists(path):
                return path
            return None
    except Exception:
        return None

def clear_config():
    """Removes the global configuration."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        log.info("🗑️  Global configuration cleared.")