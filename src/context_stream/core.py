"""
File summary: This code implements a context stream for analyzing and summarizing source code projects, 
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


class ContextStream:
    def __init__(self, project_path: str, logs_on: bool = True, context_logs_on: bool = True, ignore_list: list = None):
        self.project_path = Path(project_path).resolve()
        self.model_path = get_model_path()
        self.state = ProjectState(self.project_path)

        self.ignore_list = ignore_list or []

        from debugflow.logger_system import log as base_log
        self.logger = base_log.getChild("context_stream")
        self.logger.name = "context_stream"
        self.silent = not logs_on or not context_logs_on

    def _log(self, message: str, level: str = "info"):
        """Internal logger using the context_stream identity."""
        if not self.silent:
            if level == "info":
                self.logger.info(message)
            elif level == "error":
                self.logger.error(message)

    def run(self, auto_inject: bool = True):
        """The actual stream logic. Now filters framework noise."""
        if not self.model_path:
            self._log("❌ Model path not set. Use 'model-path' command first.", "error")
            return None, None

        self._log(f"🚀 Context Stream Active: {self.project_path.name}")

        stats = {"total_files": 0, "cache_hits": 0, "new_analyses": 0, "time_taken": 0.0}
        project_graph = {}

        files = scan_project_files(self.project_path, user_ignores=self.ignore_list)
        tree, _ = build_tree(self.project_path, user_ignores=self.ignore_list)

        cache = self.state.load_cache()
        summarized_data = []
        stats["total_files"] = len(files)
        total_start = time.time()

        for file in tqdm(files, desc="🧠 Analyzing Project", unit="file", disable=self.silent):
            try:
                rel_path = self.state.to_relative(file).replace("\\", "/")
                current_hash = get_file_hash(file)

                if rel_path in cache and cache[rel_path].get("hash") == current_hash:
                    cached_entry = cache[rel_path]["summary"]
                    summarized_data.append(cached_entry)
                    project_graph[rel_path] = cached_entry.get("dependencies", [])
                    stats["cache_hits"] += 1
                    continue

                stats["new_analyses"] += 1
                parsed, module_doc, imports = parse_file(file)
                project_graph[rel_path] = imports

                file_info = {
                    "file": rel_path,
                    "content": file.read_text(encoding="utf-8"),
                    "docstring": module_doc or "",
                    "functions": parsed.get("functions", []),
                    "classes": parsed.get("classes", [])
                }

                summary = summarize_file(file_info, cache)
                injected_doc = module_doc

                if auto_inject and not module_doc:
                    intent_text = summary.get("intent", "No intent captured.")
                    injected_doc = f'"""\nFile summary: {intent_text}\n"""\n\n'
                    original_content = file.read_text(encoding="utf-8")

                    if not original_content.startswith('"""'):
                        file.write_text(injected_doc + original_content, encoding="utf-8")
                        self._log(f"✍️ Injected AI Intent: {file.name}")
                        current_hash = get_file_hash(file)

                file_entry = {
                    "file": rel_path,
                    "intent": summary.get("intent", "No intent captured."),
                    "index": summary.get("index", {}),
                    "classes": summary.get("classes", {}),
                    "dependencies": imports,
                    "docstring": injected_doc
                }

                summarized_data.append(file_entry)
                cache[rel_path] = {"hash": current_hash, "summary": file_entry}

            except Exception as e:
                self._log(f"❌ Failed {file.name}: {e}", "error")

        project_map = {
            "project_name": self.project_path.name,
            "tree": tree,
            "dependencies": project_graph,
            "map": summarized_data
        }

        self.state.save_state(cache, project_map)
        export_json(project_map, "project_summary.json", self.project_path)

        stats["time_taken"] = time.time() - total_start
        self._log(f"🏁 Neural Mapping Complete ({stats['time_taken']:.2f}s).")

        return project_map, stats
