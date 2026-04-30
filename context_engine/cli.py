"""
File summary: This file defines a command-line tool for project scanning and context analysis.
It manages its own AI-specific log persistence and handles model path configuration.
"""

import sys
import os
import time
from pathlib import Path
from .core import ContextEngine
from .config import set_model_path, get_model_path

# Path to persist the toggle state (AI chatter ON/OFF)
STATE_FILE = Path(__file__).parent / ".context_log_state"

def get_log_state():
    """Reads the persisted state for AI chatter (defaults to ON)."""
    if not STATE_FILE.exists():
        return True
    return STATE_FILE.read_text().strip() == "ON"

def set_log_state(state: bool):
    """Writes the AI chatter state to the local persistence file."""
    STATE_FILE.write_text("ON" if state else "OFF")

def logs_on():
    set_log_state(True)
    print("\n🧠 Context AI Logging: ON")

def logs_off():
    set_log_state(False)
    print("\n🧠 Context AI Logging: OFF (SILENCED)")

def toggle_logs():
    """Toggles the AI log state based on current local value."""
    current = get_log_state()
    if current:
        logs_off()
    else:
        logs_on()

def show_help():
    print("\n" + "═"*50)
    print(" 💡 CONTEXT ENGINE - COMMAND CENTER")
    print("═"*50)
    print("  context <path>            # Scan project (e.g., context .)")
    print("  context model-path        # Link your GGUF model")
    print("\n 🛠️  AI LOG CONTROL (Persists):")
    print("  context-logs              # Toggle AI logs ON/OFF")
    print("  context-logs-on           # Force AI logs ON")
    print("  context-logs-off          # Force AI logs OFF")
    print("═"*50 + "\n")

def main():
    invoked_as = os.path.basename(sys.argv[0]).lower()
    args = sys.argv[1:]
    arg_string = " ".join(args).lower()

    # 1. Handle Bare Command
    if not args and invoked_as == "context":
        show_help()
        return

    # 2. Handle Model Configuration
    if args and args[0].lower() == "model-path":
        print("\n" + "─"*50)
        path = input("🎯 Enter absolute path to your GGUF model: ").strip().replace('"', '').replace("'", "")
        if set_model_path(path):
            print("✨ Configuration saved successfully.")
        else:
            print("❌ Setup failed.")
        print("─"*50 + "\n")
        return

    # 3. Determine Context AI Log State
    # We ignore global debugflow state here; let the debugflow package handle itself.
    persisted_context_state = get_log_state()
    
    # Check for runtime overrides (e.g., 'context . context-logs off')
    context_logs_enabled = persisted_context_state
    if "context-logs off" in arg_string: context_logs_enabled = False
    if "context-logs on" in arg_string: context_logs_enabled = True

    # 4. Target Path Resolution
    target_path = args[0] if args and not args[0].startswith("-") and "off" not in args[0] else "."
    
    # 5. Model Guard
    if not get_model_path():
        print("\n⚠️  ERROR: No model linked! Run: 'context model-path'\n")
        return

    # --- THE VERBOSE STATUS HEADER ---
    print("\n" + "═"*50)
    print(f"📂 TARGET:      {Path(target_path).resolve()}")
    print(f"🧠 AI LOGS:     {'ENABLED' if context_logs_enabled else 'OFF (SILENCED)'}")
    print("═"*50 + "\n")

    try:
        # We still pass True for logs_on (master pipe) because we want Context
        # to try and log. If DebugFlow is globally OFF, its internal 
        # NullHandler will catch it anyway.
        engine = ContextEngine(
            project_path=target_path,
            logs_on=True, 
            context_logs_on=context_logs_enabled
        )
        
        project_map, stats = engine.run()

        # 6. Summary Report
        if stats:
            print("\n" + "─"*50)
            print("🏁 SCAN COMPLETE")
            print(f"⏱️  Duration:     {stats['time_taken']:.2f}s")
            print(f"📄 Total Files:   {stats['total_files']}")
            print(f"⚡ Cached:        {stats['cache_hits']}")
            print(f"🧠 AI Analyzed:   {stats['new_analyses']}")
            
            if stats['cache_hits'] == stats['total_files'] and stats['total_files'] > 0:
                print("✨ Status:         Project matches cache. No changes.")
            print("─"*50 + "\n")

    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted. Exiting...")
    except Exception as e:
        print(f"\n❌ Failure: {e}")

if __name__ == "__main__":
    main()