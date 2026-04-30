import ast

def extract_dependencies(file_path):
    """Scans a file for imports to build the project graph."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports = []
    
    for node in ast.walk(tree):
        # Handles 'import numpy'
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        # Handles 'from utils import math_ops'
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)
            
    return list(set(imports)) # Unique dependencies only



def extract_imports(tree: ast.AST) -> list:
    """Extracts all top-level imports to map file relationships."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return list(set(imports))