"""
File summary: The file summarizes the intent in one concise sentence.
"""

import json
import hashlib
import os
import re
from typing import Dict, Any, List
from debugflow.logger_system import log
from .model_loader import get_model
from llama_cpp import Llama
from .config import get_model_path
from pathlib import Path

# -----------------------------
# LLM CLEANING & LOGIC
# -----------------------------
# Create a global placeholder
_LLM_INSTANCE = None
def get_model():
    global _LLM_INSTANCE
    if _LLM_INSTANCE is None:
        path = get_model_path()
        if not path:
            raise ValueError("Model path not configured.")
        log.info(f"💾 Loading Model into RAM: {Path(path).name}")
        _LLM_INSTANCE = Llama(model_path=path, verbose=False, n_ctx=2048)
    return _LLM_INSTANCE


def clean_llm_text(text: str) -> str:
    """Removes markdown backticks, 'python' tags, and forced newlines."""
    # Remove triple backtick blocks
    text = re.sub(r"```(python)?", "", text)
    text = text.replace("```", "")
    # Remove leading/trailing whitespace and junk symbols
    return text.strip().split('\n')[0] 
def ai_generate_summary(code_segment: str, context_type: str = "file") -> str:
    """Uses Gemma to explain intent, prioritized by actual logic flow."""
    llm = get_model()
    
    # The Skeptic Prompt: 
    # Tells the AI to look at execution, not just definitions.
    role = "Senior Code Auditor"
    instruction = (
        f"Summarize what this {context_type} ACTUALLY executes in ONE concise sentence. "
        "Ignore misleading names; focus on the operations."
    )
    
    prompt = (
        f"[SYSTEM] You are a {role}. Provide a plain-text summary.\n"
        f"[TASK] {instruction} No markdown.\n"
        f"[CODE]\n{code_segment}\n[SUMMARY]"
    )
    
    try:
        # Lowered temperature (if your get_model allows) would be ideal here 
        # to keep the AI from getting "creative."
        response = llm(prompt, max_tokens=80, stop=["\n", "```"])
        raw_text = response['choices'][0]['text']
        cleaned = clean_llm_text(raw_text)
        
        # If the AI returns an empty string or just the function name, 
        # we have a fallback.
        if not cleaned or len(cleaned) < 5:
            cleaned = f"Executes logic for {context_type}."

        log.info(f"🧠 Gemma ({context_type}): {cleaned}")
        return cleaned
    except Exception as e:
        log.error(f"🧠 LLM Summarization Error: {e}")
        return "Summary unavailable due to analysis error."
# -----------------------------
# MASTER SUMMARIZATION
# -----------------------------
def analyze_intent(code_chunk: str, context_type: str) -> str:
    """
    Specialist: Analyzes a specific block of code and returns a 1-sentence truth.
    """
    if not code_chunk or len(code_chunk.strip()) < 10:
        return f"Minimal {context_type} logic."

    try:
        # Passes the chunk to our existing ai_generate_summary skeptic prompt
        intent = ai_generate_summary(code_chunk, context_type=context_type)
        return intent
    except Exception as e:
        log.error(f"⚠️ IntentAnalyst failed on {context_type}: {e}")
        return f"Analysis failed for {context_type}."
    

def summarize_file(file_info: Dict[str, Any], cache: Any) -> Dict[str, Any]:
    """
    Orchestrator: Delegates chunk analysis and assembles the File Map.
    Ensures Classes and Methods are deeply analyzed, not just listed.
    """
    file_name = file_info.get("file", "unknown_file")
    functions = file_info.get("functions", [])
    classes = file_info.get("classes", [])
    content = file_info.get("content", "")
    
    log.info(f"🧬 Synthesizing context: {file_name}")

    # --- Step 1: File Level Intent (The 'Skeptic' check) ---
    doc_raw = file_info.get("docstring", "")
    if "File summary:" in doc_raw:
        match = re.search(r"File summary:\s*(.*)", doc_raw)
        file_intent = match.group(1).strip() if match else analyze_intent(content, "file")
    else:
        file_intent = analyze_intent(content, "file")

    # --- Step 2: Standalone Function Indexing ---
    func_index = {}
    for f in functions:
        # Use the logic preview to catch the 'truth'
        f_sig = f.get("signature") or f.get("name", "unknown_func")
        logic = f.get("logic_preview", "")
        func_index[f_sig] = analyze_intent(logic, "function")

    # --- Step 3: Class & Method Deep-Dive ---
    class_map = {}
    for c in classes:
        c_name = c.get("name", "UnknownClass")
        method_summaries = {}
        
        # Deeply analyze every method in the class
        for m in c.get("methods", []):
            # The parser should now be passing method dicts, not just names
            if isinstance(m, dict):
                m_sig = m.get("signature") or m.get("name", "unknown_method")
                m_logic = m.get("logic_preview", "")
                method_summaries[m_sig] = analyze_intent(m_logic, "method")
            else:
                # Fallback if parser only sent a string name
                method_summaries[m] = "Method identified but logic not indexed."
        
        # Analyze the class's purpose (from its own docstring or signature)
        class_map[c_name] = {
            "intent": analyze_intent(c.get("docstring", ""), "class"),
            "methods": method_summaries
        }

    return {
        "intent": file_intent,
        "index": func_index,
        "classes": class_map
    }