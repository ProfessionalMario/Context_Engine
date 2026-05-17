"""
File summary: Summary unavailable due to analysis error.
"""

# """
# Comprehensive test suite for context_engine.
# Mocks: llama_cpp, debugflow, tqdm (unavailable in this environment).
# Simulates the LLM response so the full pipeline can be exercised.
# """

# import sys
# import types
# import json
# import ast
# import hashlib
# import tempfile
# import os
# from pathlib import Path
# from unittest.mock import MagicMock, patch

# # ──────────────────────────────────────────────
# # 1.  MOCK ALL EXTERNAL DEPENDENCIES
# # ──────────────────────────────────────────────

# # --- tqdm ---
# tqdm_mod = types.ModuleType("tqdm")
# def _fake_tqdm(iterable=None, **kwargs):
#     return iterable or []
# tqdm_mod.tqdm = _fake_tqdm
# sys.modules["tqdm"] = tqdm_mod

# # --- llama_cpp ---
# llama_cpp_mod = types.ModuleType("llama_cpp")
# class FakeLlama:
#     def __init__(self, **kwargs): pass
#     def __call__(self, prompt, max_tokens=80, stop=None):
#         return {"choices": [{"text": "Executes logic for the given module."}]}
# llama_cpp_mod.Llama = FakeLlama
# sys.modules["llama_cpp"] = llama_cpp_mod

# # --- debugflow ---
# debugflow_mod = types.ModuleType("debugflow")
# logger_system_mod = types.ModuleType("debugflow.logger_system")

# class _FakeLogger:
#     name = "debugflow"
#     def info(self, *a, **kw): pass
#     def warning(self, *a, **kw): pass
#     def error(self, *a, **kw): pass
#     def getChild(self, name):
#         child = _FakeLogger()
#         child.name = name
#         return child
#     def config(self, **kw): pass

# _fake_log = _FakeLogger()
# logger_system_mod.log = _fake_log
# debugflow_mod.logger_system = logger_system_mod

# spinelink_mod = types.ModuleType("debugflow.spinelink")
# class FakeSpineLink:
#     def harvest_last_failure_from_logs(self): return "Traceback (most recent call last):\n  File \"/tmp/fake.py\", line 10\nValueError: test"
#     def apply_patch(self, path, code): pass
# spinelink_mod.SpineLink = FakeSpineLink
# debugflow_mod.spinelink = spinelink_mod

# sys.modules["debugflow"] = debugflow_mod
# sys.modules["debugflow.logger_system"] = logger_system_mod
# sys.modules["debugflow.spinelink"] = spinelink_mod

# # ──────────────────────────────────────────────
# # 2.  NOW IMPORT THE PACKAGE MODULES
# # ──────────────────────────────────────────────

# sys.path.insert(0, str(Path(__file__).parent.parent))

# # Import each module individually so failures are isolated
# import importlib

# def try_import(module_name):
#     try:
#         mod = importlib.import_module(module_name)
#         return mod, None
#     except Exception as e:
#         return None, e

# # ──────────────────────────────────────────────
# # 3.  TEST HELPERS
# # ──────────────────────────────────────────────

# PASS = "✅ PASS"
# FAIL = "❌ FAIL"
# results = []

# def check(name, condition, detail=""):
#     status = PASS if condition else FAIL
#     results.append((status, name, detail))
#     print(f"  {status}  {name}" + (f"  [{detail}]" if detail else ""))

# def section(title):
#     print(f"\n{'═'*55}")
#     print(f"  {title}")
#     print(f"{'═'*55}")

# # ──────────────────────────────────────────────
# # 4.  MODULE IMPORT TESTS
# # ──────────────────────────────────────────────

# section("MODULE IMPORT TESTS")

# mods = {}
# for mod_name in ["context_engine.config", "context_engine.scanner",
#                  "context_engine.parser", "context_engine.exporter",
#                  "context_engine.linker", "context_engine.model_loader",
#                  "context_engine.summarize", "context_engine.core",
#                  "context_engine.cli", "context_engine"]:
#     mod, err = try_import(mod_name)
#     mods[mod_name] = mod
#     check(f"import {mod_name}", mod is not None, str(err) if err else "")

# # ──────────────────────────────────────────────
# # 5.  CONFIG MODULE TESTS
# # ──────────────────────────────────────────────

# section("CONFIG MODULE (config.py)")

# cfg = mods.get("context_engine.config")
# if cfg:
#     check("get_model_path returns None when no config", cfg.get_model_path() is None)
#     check("set_model_path rejects non-existent path", cfg.set_model_path("/nonexistent/fake.gguf") == False)

#     with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as f:
#         fake_gguf = f.name
#     try:
#         result = cfg.set_model_path(fake_gguf)
#         check("set_model_path accepts real .gguf file", result == True)
#         retrieved = cfg.get_model_path()
#         check("get_model_path returns saved path", retrieved == fake_gguf)
#         cfg.clear_config()
#         check("clear_config removes config", cfg.get_model_path() is None)
#     finally:
#         os.unlink(fake_gguf)
# else:
#     check("config module unavailable - skipping", False)

# # ──────────────────────────────────────────────
# # 6.  SCANNER MODULE TESTS
# # ──────────────────────────────────────────────

# section("SCANNER MODULE (scanner.py)")

# scanner = mods.get("context_engine.scanner")
# if scanner:
#     with tempfile.TemporaryDirectory() as tmpdir:
#         tmpdir = Path(tmpdir)
#         (tmpdir / "alpha.py").write_text("x = 1")
#         (tmpdir / "beta.py").write_text("y = 2")
#         (tmpdir / "__pycache__").mkdir()
#         (tmpdir / "__pycache__" / "cached.py").write_text("# cache")
#         (tmpdir / "venv").mkdir()
#         (tmpdir / "venv" / "lib.py").write_text("# venv")

#         files = scanner.scan_project_files(str(tmpdir))
#         names = [f.name for f in files]

#         check("scan finds .py files", len(files) >= 2)
#         check("scan finds alpha.py", "alpha.py" in names)
#         check("scan finds beta.py", "beta.py" in names)
#         check("scan ignores __pycache__", "cached.py" not in names)
#         check("scan ignores venv", "lib.py" not in names)

#         # user_ignores
#         files2 = scanner.scan_project_files(str(tmpdir), user_ignores=["beta.py"])
#         names2 = [f.name for f in files2]
#         check("user_ignores excludes specified file", "beta.py" not in names2)

#         # build_tree
#         tree, _ = scanner.build_tree(str(tmpdir))
#         check("build_tree returns dict with root key", "root" in tree)
#         check("build_tree has structure key", "structure" in tree)
#         check("build_tree root name matches dir", tree["root"] == tmpdir.name)

#         # get_file_hash
#         test_file = tmpdir / "alpha.py"
#         h1 = scanner.get_file_hash(test_file)
#         check("get_file_hash returns non-empty string", isinstance(h1, str) and len(h1) == 64)

#         test_file.write_text("x = 999")
#         h2 = scanner.get_file_hash(test_file)
#         check("get_file_hash changes on file change", h1 != h2)

#         check("get_file_hash returns empty for missing file",
#               scanner.get_file_hash(Path("/nonexistent/file.py")) == "")

#         # ProjectState
#         ps = scanner.ProjectState(str(tmpdir))
#         check("ProjectState creates context dir", (tmpdir / "context").exists())
#         empty_cache = ps.load_cache()
#         check("ProjectState load_cache returns dict on miss", isinstance(empty_cache, dict))

#         sample_cache = {"alpha.py": {"hash": "abc123", "summary": {"intent": "does stuff"}}}
#         sample_map = {"project_name": "test", "tree": tree, "dependencies": {}, "map": []}
#         ps.save_state(sample_cache, sample_map)
#         check("ProjectState save_state creates cache.json", ps.cache_path.exists())
#         check("ProjectState save_state creates map file", ps.map_path.exists())

#         loaded = ps.load_cache()
#         check("ProjectState load_cache returns saved data", loaded.get("alpha.py", {}).get("hash") == "abc123")

#         rel = ps.to_relative(tmpdir / "alpha.py")
#         check("to_relative strips root path", "alpha.py" in rel)
# else:
#     check("scanner module unavailable - skipping", False)

# # ──────────────────────────────────────────────
# # 7.  PARSER MODULE TESTS
# # ──────────────────────────────────────────────

# section("PARSER MODULE (parser.py)")

# parser_mod = mods.get("context_engine.parser")
# if parser_mod:
#     with tempfile.TemporaryDirectory() as tmpdir:
#         tmpdir = Path(tmpdir)

#         # Normal file with class + function
#         sample_code = '''"""This is a module docstring."""

# import os
# from pathlib import Path

# def greet(name: str) -> str:
#     """Says hello."""
#     return f"Hello {name}"

# class MyClass:
#     """A sample class."""
#     def method_one(self, x: int) -> int:
#         """Doubles x."""
#         return x * 2
# '''
#         pyfile = tmpdir / "sample.py"
#         pyfile.write_text(sample_code)

#         parsed, module_doc, imports = parser_mod.parse_file(pyfile)
#         check("parse_file returns 3 values", parsed is not None and module_doc is not None and imports is not None)
#         check("parse_file extracts functions", len(parsed.get("functions", [])) >= 1)
#         check("parse_file extracts classes", len(parsed.get("classes", [])) >= 1)
#         check("parse_file function name correct", parsed["functions"][0]["name"] == "greet")
#         check("parse_file function signature present", "greet" in parsed["functions"][0].get("signature", ""))
#         check("parse_file class name correct", parsed["classes"][0]["name"] == "MyClass")
#         check("parse_file class methods present", len(parsed["classes"][0].get("methods", [])) >= 1)
#         check("parse_file extracts imports", "os" in imports or "pathlib" in imports)
#         check("parse_file deduplicates imports", len(imports) == len(set(imports)))

#         # Missing file
#         missing = tmpdir / "nonexistent.py"
#         p2, d2, i2 = parser_mod.parse_file(missing)
#         check("parse_file handles missing file gracefully", p2 == {} and i2 == [])

#         # Syntax-broken file
#         broken = tmpdir / "broken.py"
#         broken.write_text("def bad(:\n    pass")
#         p3, d3, i3 = parser_mod.parse_file(broken)
#         check("parse_file handles syntax error gracefully", p3 == {})

#         # parse_docstring
#         sample_doc = """File summary: Does something useful.
# Function index:
# greet:
#   Summary: Greets the user.
# """
#         result = parser_mod.parse_docstring(sample_doc)
#         check("parse_docstring extracts file_summary", "Does something useful" in result.get("file_summary", ""))
#         check("parse_docstring extracts functions list", len(result.get("functions", [])) >= 1)

#         # clean_docstring
#         raw = "  Hello World  \n\n----\n\n  This is it.  "
#         cleaned = parser_mod.clean_docstring(raw)
#         check("clean_docstring removes separators", "----" not in cleaned)
#         check("clean_docstring removes empty lines", cleaned.strip() != "")

#         # get_last_crash_file
#         traceback_text = 'Traceback (most recent call last):\n  File "/home/user/project/main.py", line 42\nRuntimeError: crash'
#         crash_file = parser_mod.get_last_crash_file(traceback_text)
#         check("get_last_crash_file extracts file path", crash_file == "/home/user/project/main.py")

#         check("get_last_crash_file returns None on empty text",
#               parser_mod.get_last_crash_file("") is None)
#         check("get_last_crash_file returns None on no-log text",
#               parser_mod.get_last_crash_file("No logs found") is None)

#         # extract_function directly
#         source = "def add(a: int, b: int) -> int:\n    \"\"\"Adds two numbers.\"\"\"\n    return a + b"
#         tree_node = ast.parse(source)
#         func_node = tree_node.body[0]
#         source_lines = source.splitlines()
#         func_data = parser_mod.extract_function(func_node, source_lines)
#         check("extract_function returns dict with name", func_data.get("name") == "add")
#         check("extract_function extracts signature", "add" in func_data.get("signature", ""))
#         check("extract_function extracts return type", "int" in func_data.get("signature", ""))
#         check("extract_function extracts docstring", "Adds" in func_data.get("docstring", ""))
#         check("extract_function extracts logic_preview", func_data.get("logic_preview") != "")
# else:
#     check("parser module unavailable - skipping", False)

# # ──────────────────────────────────────────────
# # 8.  EXPORTER MODULE TESTS
# # ──────────────────────────────────────────────

# section("EXPORTER MODULE (exporter.py)")

# exporter = mods.get("context_engine.exporter")
# if exporter:
#     with tempfile.TemporaryDirectory() as tmpdir:
#         tmpdir = Path(tmpdir)
#         data = {"project_name": "test_project", "files": ["a.py", "b.py"]}

#         exporter.export_json(data, "test_output.json", tmpdir)
#         out_file = tmpdir / "context" / "test_output.json"
#         check("export_json creates file", out_file.exists())

#         with open(out_file) as f:
#             loaded = json.load(f)
#         check("export_json content is correct", loaded["project_name"] == "test_project")

#         exporter.export_text("Hello, World!", "test_output.txt", tmpdir)
#         txt_file = tmpdir / "context" / "test_output.txt"
#         check("export_text creates file", txt_file.exists())
#         check("export_text content is correct", txt_file.read_text() == "Hello, World!")

#         context_path = exporter.ensure_context_dir(tmpdir)
#         check("ensure_context_dir returns Path", isinstance(context_path, Path))
#         check("ensure_context_dir path exists", context_path.exists())
# else:
#     check("exporter module unavailable - skipping", False)

# # ──────────────────────────────────────────────
# # 9.  LINKER MODULE TESTS
# # ──────────────────────────────────────────────

# section("LINKER MODULE (linker.py)")

# linker = mods.get("context_engine.linker")
# if linker:
#     with tempfile.TemporaryDirectory() as tmpdir:
#         tmpdir = Path(tmpdir)
#         code = "import os\nimport sys\nfrom pathlib import Path\nx = 1"
#         f = tmpdir / "test.py"
#         f.write_text(code)

#         deps = linker.extract_dependencies(f)
#         check("extract_dependencies returns list", isinstance(deps, list))
#         check("extract_dependencies finds 'os'", "os" in deps)
#         check("extract_dependencies finds 'sys'", "sys" in deps)
#         check("extract_dependencies deduplicates", len(deps) == len(set(deps)))

#         tree = ast.parse(code)
#         imports = linker.extract_imports(tree)
#         check("extract_imports works on AST", isinstance(imports, list))
#         check("extract_imports finds 'os'", "os" in imports)
# else:
#     check("linker module unavailable - skipping", False)

# # ──────────────────────────────────────────────
# # 10. MODEL_LOADER MODULE TESTS (with llama_cpp mocked)
# # ──────────────────────────────────────────────

# section("MODEL LOADER MODULE (model_loader.py)")

# model_loader = mods.get("context_engine.model_loader")
# if model_loader:
#     # Model doesn't exist — resolve_model_path should still return a Path
#     check("resolve_model_path returns a Path object",
#           isinstance(model_loader.resolve_model_path(), Path))

#     # get_model should raise FileNotFoundError when no model on disk
#     # (and env var not set)
#     model_loader._llm = None  # reset singleton
#     os.environ.pop("MODEL_PATH", None)
#     try:
#         model_loader.get_model()
#         check("get_model raises without model file", False, "Should have raised")
#     except FileNotFoundError as e:
#         check("get_model raises FileNotFoundError when model missing", True)
#     except Exception as e:
#         check("get_model raises on missing model", True, type(e).__name__)

#     # With a fake model path via env var (file doesn't exist → FileNotFoundError)
#     os.environ["MODEL_PATH"] = "/tmp/nonexistent_model.gguf"
#     model_loader._llm = None
#     try:
#         model_loader.get_model()
#         check("get_model respects MODEL_PATH env var", False, "Should raise")
#     except FileNotFoundError:
#         check("get_model respects MODEL_PATH env var (raises for missing)", True)
#     finally:
#         del os.environ["MODEL_PATH"]
#         model_loader._llm = None
# else:
#     check("model_loader module unavailable - skipping", False)

# # ──────────────────────────────────────────────
# # 11. SUMMARIZE MODULE TESTS (LLM fully mocked)
# # ──────────────────────────────────────────────

# section("SUMMARIZE MODULE (summarize.py)")

# summarize_mod = mods.get("context_engine.summarize")
# if summarize_mod:
#     # Inject a mock LLM instance
#     summarize_mod._LLM_INSTANCE = FakeLlama()

#     # Test clean_llm_text
#     check("clean_llm_text strips backticks",
#           "```" not in summarize_mod.clean_llm_text("```python\nsome code\n```"))
#     check("clean_llm_text returns first line",
#           summarize_mod.clean_llm_text("Line one\nLine two") == "Line one")
#     check("clean_llm_text handles empty string",
#           summarize_mod.clean_llm_text("") == "")

#     # Test ai_generate_summary (uses mock LLM)
#     result = summarize_mod.ai_generate_summary("def foo(): return 42", "function")
#     check("ai_generate_summary returns string", isinstance(result, str))
#     check("ai_generate_summary returns non-empty string", len(result) > 0)

#     # Test analyze_intent
#     intent = summarize_mod.analyze_intent("def bar(): pass", "function")
#     check("analyze_intent returns string", isinstance(intent, str))

#     intent_empty = summarize_mod.analyze_intent("", "function")
#     check("analyze_intent handles empty code gracefully", isinstance(intent_empty, str))

#     # Test summarize_file
#     file_info = {
#         "file": "test_module.py",
#         "content": "def compute(x):\n    return x * 2",
#         "docstring": "",
#         "functions": [
#             {"name": "compute", "signature": "compute(x) -> None",
#              "docstring": "", "logic_preview": "def compute(x):\n    return x * 2"}
#         ],
#         "classes": [
#             {
#                 "name": "Processor",
#                 "docstring": "Processes data.",
#                 "methods": [
#                     {"name": "run", "signature": "run(self) -> None",
#                      "docstring": "Runs the processor.", "logic_preview": "def run(self):\n    pass"}
#                 ]
#             }
#         ]
#     }
#     summary = summarize_mod.summarize_file(file_info, {})
#     check("summarize_file returns dict", isinstance(summary, dict))
#     check("summarize_file has 'intent' key", "intent" in summary)
#     check("summarize_file has 'index' key", "index" in summary)
#     check("summarize_file has 'classes' key", "classes" in summary)
#     check("summarize_file indexes functions", len(summary["index"]) >= 1)
#     check("summarize_file maps class", "Processor" in summary["classes"])
#     check("summarize_file class has 'intent'", "intent" in summary["classes"].get("Processor", {}))
#     check("summarize_file class has 'methods'", "methods" in summary["classes"].get("Processor", {}))

#     # Test that existing File summary in docstring is respected
#     file_info_with_doc = dict(file_info)
#     file_info_with_doc["docstring"] = "File summary: Already documented."
#     summary2 = summarize_mod.summarize_file(file_info_with_doc, {})
#     check("summarize_file uses existing File summary", "Already documented" in summary2["intent"])
# else:
#     check("summarize module unavailable - skipping", False)

# # ──────────────────────────────────────────────
# # 12. CORE ENGINE TESTS (full pipeline, LLM mocked)
# # ──────────────────────────────────────────────

# section("CORE ENGINE (core.py) — Full Pipeline")

# core_mod = mods.get("context_engine.core")
# if core_mod:
#     with tempfile.TemporaryDirectory() as tmpdir:
#         tmpdir = Path(tmpdir)

#         # Seed with a fake model path config
#         cfg = mods["context_engine.config"]
#         with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as f:
#             fake_gguf = f.name

#         cfg.set_model_path(fake_gguf)

#         # Inject mock LLM into summarize
#         if summarize_mod:
#             summarize_mod._LLM_INSTANCE = FakeLlama()

#         # Create sample Python files in project dir
#         (tmpdir / "main.py").write_text('"""Main module."""\nimport os\n\ndef run():\n    pass\n')
#         (tmpdir / "utils.py").write_text('import sys\n\ndef helper(x: int) -> int:\n    return x + 1\n')
#         (tmpdir / "models.py").write_text(
#             'class DataModel:\n    """Data holder."""\n    def load(self):\n        return {}\n'
#         )

#         engine = core_mod.ContextEngine(
#             project_path=str(tmpdir),
#             logs_on=False,
#             context_logs_on=False
#         )
#         check("ContextEngine instantiates", engine is not None)
#         check("ContextEngine sets project_path", engine.project_path == tmpdir)
#         check("ContextEngine stores ignore_list", isinstance(engine.ignore_list, list))

#         project_map, stats = engine.run(auto_inject=False)

#         check("engine.run returns project_map dict", isinstance(project_map, dict))
#         check("engine.run returns stats dict", isinstance(stats, dict))
#         check("project_map has 'project_name'", "project_name" in project_map)
#         check("project_map project_name correct", project_map["project_name"] == tmpdir.name)
#         check("project_map has 'tree'", "tree" in project_map)
#         check("project_map has 'dependencies'", "dependencies" in project_map)
#         check("project_map has 'map'", "map" in project_map)
#         check("stats has total_files", stats.get("total_files", 0) >= 3)
#         check("stats has cache_hits", "cache_hits" in stats)
#         check("stats has new_analyses", "new_analyses" in stats)
#         check("stats has time_taken", "time_taken" in stats)

#         # Verify JSON was written to disk
#         json_path = tmpdir / "context" / "project_summary.json"
#         check("project_summary.json written to disk", json_path.exists())

#         with open(json_path) as f:
#             on_disk = json.load(f)
#         check("on-disk JSON matches in-memory map (project_name)", on_disk["project_name"] == project_map["project_name"])

#         # Verify map entries have expected keys
#         map_entries = project_map.get("map", [])
#         check("map has at least 3 file entries", len(map_entries) >= 3)
#         if map_entries:
#             entry = map_entries[0]
#             check("map entry has 'file' key", "file" in entry)
#             check("map entry has 'intent' key", "intent" in entry)
#             check("map entry has 'dependencies' key", "dependencies" in entry)

#         # 2nd run — should hit cache entirely
#         project_map2, stats2 = engine.run(auto_inject=False)
#         check("second run hits cache", stats2["cache_hits"] == stats2["total_files"])
#         check("second run new_analyses is 0", stats2["new_analyses"] == 0)

#         # ignore_list test
#         (tmpdir / "noise.py").write_text("# framework noise\n")
#         engine_ignored = core_mod.ContextEngine(
#             project_path=str(tmpdir),
#             logs_on=False,
#             context_logs_on=False,
#             ignore_list=["noise.py"]
#         )
#         map3, stats3 = engine_ignored.run(auto_inject=False)
#         filenames_in_map = [e["file"].replace("\\", "/") for e in map3.get("map", [])]
#         check("ignore_list excludes noise.py from map",
#               not any("noise.py" in fn for fn in filenames_in_map))

#         # auto_inject test
#         no_doc_file = tmpdir / "nodoc.py"
#         no_doc_file.write_text("def work():\n    return 42\n")
#         engine_inject = core_mod.ContextEngine(
#             project_path=str(tmpdir),
#             logs_on=False,
#             context_logs_on=False,
#             ignore_list=["noise.py"]
#         )
#         engine_inject.run(auto_inject=True)
#         content_after = no_doc_file.read_text()
#         check("auto_inject=True adds docstring to undocumented file",
#               '"""' in content_after)

#         os.unlink(fake_gguf)
#         cfg.clear_config()
# else:
#     check("core module unavailable - skipping", False)

# # ──────────────────────────────────────────────
# # 13. CLI MODULE TESTS
# # ──────────────────────────────────────────────

# section("CLI MODULE (cli.py)")

# cli_mod = mods.get("context_engine.cli")
# if cli_mod:
#     check("get_log_state returns bool", isinstance(cli_mod.get_log_state(), bool))

#     # Toggle state
#     orig_state = cli_mod.get_log_state()
#     cli_mod.set_log_state(not orig_state)
#     check("set_log_state/get_log_state roundtrip", cli_mod.get_log_state() == (not orig_state))
#     cli_mod.set_log_state(orig_state)  # restore

#     # show_help shouldn't crash
#     try:
#         import io
#         old_stdout = sys.stdout
#         sys.stdout = io.StringIO()
#         cli_mod.show_help()
#         output = sys.stdout.getvalue()
#         sys.stdout = old_stdout
#         check("show_help prints content", "context" in output.lower())
#     except Exception as e:
#         sys.stdout = old_stdout
#         check("show_help executes without error", False, str(e))

#     check("logs_on function exists", callable(cli_mod.logs_on))
#     check("logs_off function exists", callable(cli_mod.logs_off))
#     check("toggle_logs function exists", callable(cli_mod.toggle_logs))
#     check("main function exists", callable(cli_mod.main))
# else:
#     check("cli module unavailable - skipping", False)

# # ──────────────────────────────────────────────
# # 14. PUBLIC __init__ API TESTS
# # ──────────────────────────────────────────────

# section("PUBLIC API (__init__.py)")

# pkg = mods.get("context_engine")
# if pkg:
#     check("ContextEngine exported", hasattr(pkg, "ContextEngine"))
#     check("get_model_path exported", hasattr(pkg, "get_model_path"))
#     check("set_model_path exported", hasattr(pkg, "set_model_path"))
#     check("__all__ defined", hasattr(pkg, "__all__"))
#     check("ContextEngine in __all__", "ContextEngine" in pkg.__all__)
# else:
#     check("context_engine package unavailable - skipping", False)

# # ──────────────────────────────────────────────
# # 15. STRUCTURAL / FIX VERIFICATION AUDIT
# # ──────────────────────────────────────────────

# section("STRUCTURAL AUDIT (verifying all fixes applied)")

# core_source = Path("context_engine/core.py").read_text()
# check("FIX: ContextEngine defined exactly once in core.py",
#       core_source.count("class ContextEngine:") == 1)

# parser_source = Path("context_engine/parser.py").read_text()
# check("FIX: 'import re' appears exactly once in parser.py",
#       parser_source.count("import re") == 1)

# summarize_source = Path("context_engine/summarize.py").read_text()
# check("FIX: summarize.py no longer has a redundant 'from .model_loader import get_model'",
#       "from .model_loader import get_model" not in summarize_source or
#       "def get_model():" not in summarize_source)

# surgeon_source = Path("context_engine/surgeon.py").read_text()
# check("FIX: surgeon.py calls os.path.normpath(os.getcwd()) — no bare normpath()",
#       "os.path.normpath()" not in surgeon_source)

# check("FIX: parser.py uses 'from debugflow.logger_system import log' (correct object)",
#       "from debugflow.logger_system import log" in parser_source)

# check("FIX: surgeon.py instantiates SpineLink() correctly (the class, not the module)",
#       "SpineLink()" in surgeon_source)

# # ──────────────────────────────────────────────
# # 16. FINAL REPORT
# # ──────────────────────────────────────────────

# section("FINAL REPORT")

# total = len(results)
# passed = sum(1 for r in results if r[0] == PASS)
# failed = sum(1 for r in results if r[0] == FAIL)

# print(f"\n  Total checks : {total}")
# print(f"  {PASS}         : {passed}")
# print(f"  {FAIL}         : {failed}")
# print()

# if failed:
#     print("  Failed checks:")
#     for status, name, detail in results:
#         if status == FAIL:
#             print(f"    • {name}" + (f" — {detail}" if detail else ""))

# print(f"\n{'═'*55}\n")
