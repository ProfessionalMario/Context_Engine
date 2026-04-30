"""
File summary: This code implements a context engine for analyzing and summarizing source code projects, 
injecting AI intent where applicable, and generating a project map for a debugging tool.
"""

import time
from pathlib import Path
from tqdm import tqdm
from debugflow.logger_system import log
from debugflow.spinelink import SpineLink

# Local package imports
from .scanner import scan_project_files, build_tree, get_file_hash, ProjectState
from .parser import parse_file
from .summarize import summarize_file
from .exporter import export_json, export_text
from .config import get_model_path

class ContextEngine:
    def __init__(self, project_path: str, logs_on: bool = True, context_logs_on: bool = True):
        self.project_path = Path(project_path).resolve()
        self.model_path = get_model_path()
        self.state = ProjectState(self.project_path)
        
        # 1. Create a specific child logger for this engine
        # This changes [debugflow] to [debugflow.context_engine]
        from debugflow.logger_system import log as base_log
        self.logger = base_log.getChild("context_engine")
        
        # This forces the logger name to JUST 'context_engine' in the output strings
        self.logger.name = "context_engine" 
        
        self.silent = not logs_on or not context_logs_on

    def _log(self, message: str, level: str = "info"):
        """Internal logger using the context_engine identity."""
        if not self.silent:
            # Use the instance logger instead of the global 'log'
            if level == "info": 
                self.logger.info(message)
            elif level == "error": 
                self.logger.error(message)

    
    def run(self, auto_inject: bool = True):
        """The actual engine logic. Returns a tuple of (project_map, stats)."""
        if not self.model_path:
            self._log("❌ Model path not set. Use 'model-path' command first.", "error")
            return None, None

        self._log(f"🚀 Context Engine Active: {self.project_path.name}")
        
        # Initialize Stats & Graph
        stats = {"total_files": 0, "cache_hits": 0, "new_analyses": 0, "time_taken": 0.0}
        project_graph = {} # Global dependency store
        
        files = scan_project_files(self.project_path)
        tree, _ = build_tree(self.project_path)
        cache = self.state.load_cache()
        
        summarized_data = []
        stats["total_files"] = len(files)
        total_start = time.time()

        # 2. Processing Loop
        for file in tqdm(files, desc="🧠 Analyzing Project", unit="file", disable=self.silent):
            try:
                rel_path = self.state.to_relative(file).replace("\\", "/") 
                current_hash = get_file_hash(file)

                # Cache Check
                if rel_path in cache and cache[rel_path].get("hash") == current_hash:
                    cached_entry = cache[rel_path]["summary"]
                    summarized_data.append(cached_entry)
                    # Restore graph links from cache
                    project_graph[rel_path] = cached_entry.get("dependencies", [])
                    stats["cache_hits"] += 1
                    continue 

                # Analysis (Cache Miss)
                stats["new_analyses"] += 1
                
                # parser.py now returns 'imports' as a 3rd item
                parsed, module_doc, imports = parse_file(file)
                project_graph[rel_path] = imports # Map the island to the graph

                file_info = {
                    "file": rel_path,
                    "content": file.read_text(encoding="utf-8"),
                    "docstring": module_doc or "",
                    "functions": parsed.get("functions", []),
                    "classes": parsed.get("classes", [])
                }

                # Step 1: Synthesis Manager delegates to Analyst (deep scan)
                summary = summarize_file(file_info, cache)
                injected_doc = module_doc 

                # Step 2: Injection Logic (Always use the 'Truth' from intent)
                if auto_inject and not module_doc:
                    intent_text = summary.get("intent", "No intent captured.")
                    injected_doc = f'"""\nFile summary: {intent_text}\n"""\n\n'
                    original_content = file.read_text(encoding="utf-8")
                    
                    if not original_content.startswith('"""'):
                        file.write_text(injected_doc + original_content, encoding="utf-8")
                        self._log(f"✍️ Injected AI Intent: {file.name}")
                        current_hash = get_file_hash(file) # Update hash after mutation

                # Step 3: Assembly
                file_entry = {
                    "file": rel_path,
                    "intent": summary.get("intent", "No intent captured."),
                    "index": summary.get("index", {}),       # Deep function truths
                    "classes": summary.get("classes", {}),   # Deep method truths
                    "dependencies": imports,                 # Nervous system links
                    "docstring": injected_doc
                }
                
                summarized_data.append(file_entry)
                cache[rel_path] = {"hash": current_hash, "summary": file_entry}

            except Exception as e:
                self._log(f"❌ Failed {file.name}: {e}", "error")

        # 3. Finalization: Global Project Map
        project_map = {
            "project_name": self.project_path.name, 
            "tree": tree, 
            "dependencies": project_graph, # The total nervous system
            "map": summarized_data
        }

        # Persistent storage
        self.state.save_state(cache, project_map)
        export_json(project_map, "project_summary.json", self.project_path)

        stats["time_taken"] = time.time() - total_start
        self._log(f"🏁 Neural Mapping Complete ({stats['time_taken']:.2f}s).")

        return project_map, stats