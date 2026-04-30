"""
File summary: This script analyzes crash evidence, retrieves a project map, formulates a surgical prompt, consults a language model to generate a code fix, and applies the fix to the identified target file.
"""

import os
import json
from debugflow.logger_system import log
from debugflow import spinelink
from .model_loader import get_model
from .parser import get_last_crash_file  # Our local helper

def operate():
    linker = spinelink()
    
    # 1. Harvest Evidence
    log.info("💉 Surgeon: Harvesting live evidence...")
    evidence = linker.harvest_last_failure_from_logs()
    
    if not evidence or "No logs found" in evidence:
        log.error("❌ Surgeon: No crash evidence found.")
        return

    # 2. Identify Target File locally
    target_file = get_last_crash_file(evidence)
    if not target_file:
        log.error("❌ Surgeon: Could not identify target file from traceback.")
        return

    # 3. Load & Filter Project Map
    map_path = os.path.join(os.path.normpath(), "context", "project_summary.json")
    project_context = ""
    
    if os.path.exists(map_path):
        try:
            with open(map_path, "r") as f:
                full_map = json.load(f)
            
            # 1. Build the Global Context (The Neighborhood)
            summaries = [f"{item['file']}: {item['intent']}" for item in full_map.get('map', [])]
            project_context = "\n".join(summaries)

            # 2. Extract Target Intent (The Specific House)
            # We use os.path.normpath to handle the \ vs / mismatch in your JSON
            normalized_target = os.path.normpath(target_file)
            target_intent = "General Logic" # Fallback

            for item in full_map.get('map', []):
                if os.path.normpath(item['file']) in normalized_target:
                    target_intent = item['intent']
                    break
                    
        except Exception as e:
            log.warning(f"⚠️  Map Parse Error: {e}. Operating with raw text.")
            project_context = "Project map corrupted."
            target_intent = "Unknown - Repair based on traceback only."

    # 4. Formulate the Surgical Prompt
    prompt = f"""
   ### ROLE: LEAD ML ARCHITECT & SURGEON
### GOAL: REPAIR RUNTIME FAILURE IN {target_file}

### PROJECT ARCHITECTURE (GLOBAL INTENT):
{project_context}

### TARGET FILE ROLE:
{target_intent}

### EVIDENCE (SPINELINK TELEMETRY):
{evidence}

### REPAIR INSTRUCTIONS:
1. Locate the specific failure point identified in the Crime Scene.
2. Resolve shape mismatches (Tensors), type errors, or logic breaks.
3. Ensure the fix aligns with the [TARGET FILE ROLE].
4. Return ONLY the code. Do not apologize. Do not explain.

### CORRECTED SOURCE CODE:
    """

    # 5. Consult Gemma
    llm = get_model()
    log.info(f"🧠 Surgeon: Analyzing {os.path.basename(target_file)}...")
    
    response = llm(prompt, max_tokens=2048) # Higher tokens for full file rewrite
    raw_fix = response['choices'][0]['text']

    # 6. Extract Code
    fix_code = ""
    if "```" in raw_fix:
        # Grabs everything between the first and last triple backticks
        fix_code = raw_fix.split("```")[1]
        if fix_code.startswith("python"):
            fix_code = fix_code[6:]
        fix_code = fix_code.strip()
    else:
        fix_code = raw_fix.strip()

    # 7. Final Operation
    if fix_code and len(fix_code) > 10: # Basic sanity check
        log.warning(f"🛠️  Surgeon: Applying patch to {target_file}")
        linker.apply_patch(target_file, fix_code)
    else:
        log.error("❌ Surgeon: LLM returned empty or invalid fix.")

if __name__ == "__main__":
    operate()