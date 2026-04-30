"""
File summary: This module provides core functionality and configuration settings for a contextual reasoning engine.
"""

from .core import ContextEngine
from .config import get_model_path, set_model_path

__all__ = ["ContextEngine", "get_model_path", "set_model_path"]

import os
from pathlib import Path
from debugflow import logger_system as log

def initialize_engine():
    # 1. Detect the 'Host' Project Root
    # This finds the directory where the user is actually running the code
    host_root = Path(os.getcwd())
    
    # 2. Define the target log path (e.g., inside a .context folder)
    log_dir = host_root / ".context"
    log_dir.mkdir(exist_ok=True) # Create it if it doesn't exist
    
    log_file = log_dir / "engine_flow.log"
    
    # 3. Hand the path to debugflow
    # This ensures everything—engine logs and debugflow traces—hit the same file
    log.config(log_file=str(log_file))
    
    log.info(f"🚀 Engine docked. Logs redirecting to: {log_file}")