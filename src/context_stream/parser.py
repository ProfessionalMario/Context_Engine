"""
File summary: The code extracts and formats documentation from a Python file, creating a structured representation of the module's docstring, function summaries, and class definitions.
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Optional
from debugflow.logger_system import log


def extract_function_summaries(module_doc: str, parsed_functions: list) -> list:
    """
    Extract summary per function from the file docstring index.
    Fallback to the AST-extracted docstring if the index is missing.
    """
    summaries = []
    for func in parsed_functions:
        name = func["name"]
        pattern = rf"{re.escape(name)}:\s*Summary:\s*(.+)"
        match = re.search(pattern, module_doc)

        summary_text = match.group(1).strip() if match else (func.get("docstring") or func.get("signature"))

        summaries.append({
            "name": name,
            "summary": summary_text,
            "docstring": func.get("docstring", "")
        })
    return summaries


def extract_function(node: ast.FunctionDef, source_lines: list) -> dict:
    """
    Extracts signature, real docstring, and a code preview for logic analysis.
    Wrapped in try-except with logging for stability.
    """
    try:
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

        raw_doc = ast.get_docstring(node)
        if not raw_doc and node.body and isinstance(node.body[0], ast.Expr):
            val = getattr(node.body[0], "value", None)
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                raw_doc = val.value

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


def get_last_crash_file(log_text: str) -> str:
    """
    Parses the debugflow.log text to extract the last file path that crashed.
    """
    if not log_text or "No logs found" in log_text:
        return None

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
    Handles both inline ("File summary: text here") and next-line formats.
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
    mode = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect "File summary: <inline text>" on same line
        inline_match = re.match(r"file\s*summary\s*:\s*(.+)", stripped, re.I)
        if inline_match:
            result["file_summary"] = inline_match.group(1).strip()
            mode = "file_summary"
            continue

        if re.search(r"function\s*index\s*:", stripped, re.I):
            mode = "function_index"
            continue

        # Next-line file summary (no inline text after the colon)
        if mode == "file_summary" and not result["file_summary"]:
            if not re.match(r"^[-=~\s]+$", stripped):
                result["file_summary"] = stripped
            continue

        if mode == "function_index":
            if stripped.endswith(":") and not stripped.lower().startswith("summary:"):
                current_func = stripped.rstrip(":").strip()
                func_map[current_func] = {"name": current_func, "summary": ""}
            elif stripped.lower().startswith("summary:") and current_func:
                func_map[current_func]["summary"] = stripped[len("summary:"):].strip()

    result["functions"] = list(func_map.values())
    return result


def parse_file(file_path: Path):
    """
    Parses a Python file and returns:
    1. parsed (dict of funcs/classes)
    2. module_doc (str)
    3. imports (list)
    """
    if not file_path.exists():
        return {}, None, []

    try:
        source = file_path.read_text(encoding="utf-8")
        source_lines = source.splitlines()
        tree = ast.parse(source)

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.append(n.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        imports = list(set(imports))

        module_doc_raw = ast.get_docstring(tree)
        module_doc = format_docstring(file_path.stem, module_doc_raw)

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
                        method_info = extract_function(item, source_lines)
                        class_data["methods"].append(method_info)

                parsed["classes"].append(class_data)

        return parsed, module_doc, imports

    except Exception as e:
        print(f"[WARN] Failed to parse {file_path}: {e}")
        return {}, None, []


def clean_docstring(doc: Optional[str]) -> str:
    """
    Cleans a docstring by removing empty lines and separators.
    """
    if not doc:
        return ""

    lines = doc.splitlines()
    cleaned = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove lines that consist only of separator characters (length >= 2)
        if set(line) in [{"—"}, {"-"}, {"="}, {"~"}] and len(line) >= 2:
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
