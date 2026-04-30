"""
File summary: The code extracts and formats documentation from a Python file, creating a structured representation of the module's docstring, function summaries, and class definitions.
"""

from pathlib import Path
from typing import List, Dict, Optional
import re
import re
import ast
from pathlib import Path
from typing import Dict, List, Optional


import re

def extract_function_summaries(module_doc: str, parsed_functions: list) -> list[dict]:
    """
    Extract summary per function from the file docstring index.
    Fallback to the AST-extracted docstring if the index is missing.
    """
    summaries = []
    for func in parsed_functions:
        name = func["name"]
        pattern = rf"{re.escape(name)}:\s*Summary:\s*(.+)"
        match = re.search(pattern, module_doc)
        
        # Priority: 1. Top File Index, 2. Function's own docstring, 3. Signature
        summary_text = match.group(1).strip() if match else (func.get("docstring") or func.get("signature"))
        
        summaries.append({
            "name": name,
            "summary": summary_text,
            "docstring": func.get("docstring", "")
        })
    return summaries

def extract_function(node: ast.FunctionDef, source_lines: list[str]) -> dict:
    """
    Extracts signature, real docstring, and a code preview for logic analysis.
    Wrapped in try-except with logging for stability.
    """
    try:
        # 1. Extract Signature
        args_list = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args_list.append(arg_str)
        
        returns = "None"
        if node.returns:
            returns = ast.unparse(node.returns)
        signature = f"{node.name}({', '.join(args_list)}) -> {returns}"

        # 2. Extract Real Docstring
        raw_doc = ast.get_docstring(node)
        if not raw_doc and node.body and isinstance(node.body[0], ast.Expr):
            val = getattr(node.body[0], "value", None)
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                raw_doc = val.value

        # 3. Extract Logic Preview (The "Truth" check)
        # We take a 50-line chunk to keep context light but informative
        start_idx = node.lineno - 1
        end_idx = node.end_lineno
        body_lines = source_lines[start_idx:end_idx]
        logic_preview = "\n".join(body_lines[:50]) 

        return {
            "name": node.name,
            "signature": signature,
            "docstring": raw_doc.strip() if raw_doc else "",
            "logic_preview": logic_preview
        }

    except Exception as e:
        # Use the local engine logger if available, else fallback to base log
        log.error(f"Failed to parse function {node.name}: {e}")
        return {
            "name": node.name,
            "signature": f"{node.name}(...) -> Unknown",
            "docstring": "",
            "logic_preview": "Error extracting logic."
        }

def get_file_summary(module_doc: str) -> str:
    """
    Extracts the file-level summary from the top docstring.
    Returns empty string if not found.
    """
    if not module_doc:
        return ""
    match = re.search(r"File summary:\s*(.*?)\s*Function index:", module_doc, re.DOTALL)
    return match.group(1).strip() if match else ""

# -----------------------------
# FILE PARSER
# -----------------------------

import re
from debugflow import logger_system as log

def get_last_crash_file(log_text: str) -> str:
    """
    Parses the debugflow.log text to extract the last file path that crashed.
    """
    if not log_text or "No logs found" in log_text:
        return None

    # Pattern to find: File "X:\Path\to\file.py", line 123
    # We use re.findall to get the very last one (deepest in the traceback)
    matches = re.findall(r'File "(.*?)", line \d+', log_text)
    
    if matches:
        target = matches[-1]
        log.info(f"🎯 Target identified for surgery: {target}")
        return target
    
    log.warning("⚠️ Could not find a file path in the traceback.")
    return None


def parse_docstring(module_doc: str) -> dict:
    """
    Parses a module-level docstring into:
      - file_summary: top-level summary of the file
      - functions: list of dicts with function name and one-line summary
    Ignores separators and handles minor formatting variations.
    """
    result = {
        "file_summary": "",
        "functions": []
    }

    if not module_doc:
        return result

    lines = module_doc.splitlines()
    current_func = None
    func_map = {}
    mode = None  # "file_summary" | "function_index"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect sections robustly
        if re.search(r"file\s*summary\s*:", line, re.I):
            mode = "file_summary"
            continue

        if re.search(r"function\s*index\s*:", line, re.I):
            mode = "function_index"
            continue

        # Extract file summary: first non-empty, non-separator line
        if mode == "file_summary" and not result["file_summary"]:
            if not re.match(r"^[-=~\s]+$", line):
                result["file_summary"] = line
            continue

        # Extract function summaries
        if mode == "function_index":
            # New function line ends with colon
            if line.endswith(":") and not line.lower().startswith("summary:"):
                current_func = line.rstrip(":").strip()
                func_map[current_func] = {"name": current_func, "summary": ""}
            elif line.lower().startswith("summary:") and current_func:
                func_map[current_func]["summary"] = line[len("summary:"):].strip()

    result["functions"] = list(func_map.values())
    return result

def parse_file(file_path: Path):
    """
    Parses a Python file and returns:
    1. parsed (dict of funcs/classes)
    2. module_doc (str)
    3. imports (list) <--- THE MISSING THIRD VALUE
    """
    if not file_path.exists():
        return {}, None, []

    try:
        source = file_path.read_text(encoding="utf-8")
        source_lines = source.splitlines()
        tree = ast.parse(source)

        # 1. Extract Imports (The Linker logic)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.append(n.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        imports = list(set(imports)) # De-duplicate

        # 2. Module Docstring
        module_doc_raw = ast.get_docstring(tree)
        # (Your existing fallback logic for module_doc here...)
        module_doc = format_docstring(file_path.stem, module_doc_raw)

        # 3. Functions & Classes
        parsed = {"functions": [], "classes": []}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                parsed["functions"].append(extract_function(node, source_lines))
            elif isinstance(node, ast.ClassDef):
                class_data = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node) or "",
                    "methods": []
                }
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # Reuse extract_function for methods to get signatures and logic!
                        method_info = extract_function(item, source_lines)
                        class_data["methods"].append(method_info)
                
                parsed["classes"].append(class_data)
        # RETURN ALL THREE
        return parsed, module_doc, imports

    except Exception as e:
        print(f"[WARN] Failed to parse {file_path}: {e}")
        return {}, None, []
    

def clean_docstring(doc: Optional[str]) -> str:
    """
    Cleans a docstring by removing empty lines and separators.
    Wraps the docstring with -------- and the module/function name for readability.
    """
    if not doc:
        return ""

    lines = doc.splitlines()
    cleaned = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove lines that are just separators
        if set(line) in [{"-"}, {"="}, {"~"}] and len(line) > 5:
            continue
        cleaned.append(line.replace("\u2022", "-"))

    return "\n".join(cleaned)


def format_docstring(name: str, doc: Optional[str]) -> str:
    """
    Wrap the docstring with lines and the name.
    """
    cleaned = clean_docstring(doc)
    if not cleaned:
        return ""
    return f"-------- {name} --------\n{cleaned}\n-------- {name} --------"