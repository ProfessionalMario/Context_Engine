"""
File summary: This module provides core functionality and configuration settings for a contextual reasoning engine.
"""

from .core import ContextStream
from .config import get_model_path, set_model_path

__all__ = ["ContextStream", "get_model_path", "set_model_path"]

import os
from pathlib import Path

try:
    from debugflow import logger_system as log
except ImportError:
    log = None

def initialize_stream():
    # 1. Detect the 'Host' Project Root
    # This finds the directory where the user is actually running the code
    host_root = Path(os.getcwd())
    
    # 2. Define the target log path (e.g., inside a .context folder)
    log_dir = host_root / ".context"
    log_dir.mkdir(exist_ok=True) # Create it if it doesn't exist
    
    log_file = log_dir / "stream_flow.log"
    
    # 3. Hand the path to debugflow
    # This ensures everything—stream logs and debugflow traces—hit the same file
    log.config(log_file=str(log_file))
    
    log.info(f"🚀 Stream docked. Logs redirecting to: {log_file}")