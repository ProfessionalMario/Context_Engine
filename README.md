# Context Stream

> AI-powered project mapping that provides full details and intents for your local llms.
> Reads your codebase, understands what every file *actually does*, and writes the truth back into your source — so both humans and machines stop guessing.

---

## Overview

**Context Stream** is a local, offline-first code intelligence layer that walks a Python project, parses every file with AST, and uses a local GGUF model (Gemma by default) to generate a one-sentence "intent" for every file, function, class, and method. The result is a single `project_summary.json` that becomes the **nervous system** that DebugFlow's surgeon and logger pull from when something breaks.

Built for two audiences:

- **Developers** who want their codebase to self-document and want a machine-readable map of intent + dependencies for every module.
- **DebugFlow / ML pipelines** that need a global "what is this project" context to make crash diagnosis and auto-repair surgical instead of guesswork.

Everything runs locally. No code ever leaves your machine.

---

## How it works — process model

Context Stream runs as a **completely separate process** from the project it analyzes. It never imports, executes, or links against any of your project's code. It only:

1. Walks your directory tree with `os.walk`.
2. Reads each `.py` file as plain text.
3. Parses it with Python's built-in `ast` module (static analysis only).
4. Passes code snippets to a local GGUF model for summarization.
5. Writes JSON output to `<project>/context/`.

This means you can safely run it against any project — broken, partially installed, or with conflicting dependencies — without any interference in either direction.

---

## Quick Demo

### What it looks like in flight

```bash
$ context-stream .

═══════════════════════════════════════════════════════
📂 TARGET:      /home/you/projects/my_app
🧠 AI LOGS:     ENABLED
═══════════════════════════════════════════════════════

🔍 Scanning files in: /home/you/projects/my_app
📂 Found 24 Python nodes.
🧠 Cache Loaded: 18 file hashes recognized.
🧬 Synthesizing context: core.py
🧠 LLM (file): Orchestrates the request lifecycle and dispatches to handlers.
✍️ Injected AI Intent: core.py
🧠 Analyzing Project: 100%|████████████| 24/24 [00:42<00:00,  1.75s/file]
💾 State Physically Synchronized: 24 keys.
🏁 Neural Mapping Complete (42.18s).

───────────────────────────────────────────────────────
🏁 SCAN COMPLETE
⏱️  Duration:     42.18s
📄 Total Files:   24
⚡ Cached:        18
🧠 AI Analyzed:   6
───────────────────────────────────────────────────────
```

After the run, you get a `context/project_summary.json` at the project root with the full neural map of your code — files, intents, dependencies, classes, methods, the works.

---

## Installation

```bash
pip install context_stream
```

**Dependencies (auto-installed):**

- `tqdm` — progress bar for the scan loop
- `llama-cpp-python` — runs the local GGUF model
- `debugflow` — sibling package; provides the logger and SpineLink telemetry

**Requires Python 3.10+.**

You also need a **GGUF model** on disk. The stream is tuned around `google_gemma-3-4b-it-Q5_K_M.gguf`, but any chat-tuned GGUF that `llama-cpp-python` can load will work.

After install, link your model **once**:

```bash
context-stream model-path
# 🎯 Enter absolute path to your GGUF model: /home/you/models/gemma-3-4b-it-Q5_K_M.gguf
# ✨ Configuration saved successfully.
```

The path is persisted to `~/.context_stream/config.json` and reused across every project.

---

## Usage

### Option 1 — CLI (recommended)

From the root of any Python project:

```bash
context-stream .
```

The stream will:

1. Walk every `.py` file (skipping `__pycache__`, `.git`, `venv`, `models`, `context`).
2. Hash each file and skip anything already cached.
3. Send only the *changed* files to the local LLM for re-summarization.
4. Inject a `"""File summary: ..."""` docstring at the top of any file that doesn't already have one.
5. Write the full project map to `./context/project_summary.json`.

### Option 2 — Python module (embed in your own tooling)

```python
from context_stream import ContextStream

stream = ContextStream(project_path=".", logs_on=True, context_logs_on=True)
project_map, stats = stream.run(auto_inject=True)

print(f"Mapped {stats['total_files']} files in {stats['time_taken']:.2f}s")
print(f"Cache hits: {stats['cache_hits']}, AI analyses: {stats['new_analyses']}")
```

`project_map` is the same dict written to disk — use it directly without round-tripping through JSON.

The stream instance is just a regular Python object. Creating it inside your own script does **not** affect your process's imports or environment in any way — it only touches the filesystem paths you give it.

### Stopping it

The scan is cooperative. `Ctrl+C` at any time; the cache is `fsync`'d after each file so the next run picks up exactly where you left off.

---

## Problem + Motivation

Every non-trivial codebase suffers from the same rot:

- Docstrings drift, lie, or never get written.
- File names imply one thing while the code does another.
- When something crashes deep inside an ML pipeline, the only "context" your debugger has is the traceback — no idea what the surrounding files were *supposed* to do.

Context Stream fixes this at the root by treating the project itself as the source of truth. Instead of trusting names or stale docstrings, it reads the **actual logic** of every function and asks a local LLM to summarize what it *executes*, not what it claims to do. That summary then becomes:

1. A real, injected docstring at the top of the file.
2. A node in the global `project_summary.json` map.
3. The "neighborhood context" that DebugFlow's surgeon uses when proposing a fix for a crashing file.

The whole pipeline is local, cached, and incremental — so re-running it across a 500-file repo is cheap.

---

## Key Features

- **Local-first.** Runs entirely offline through `llama-cpp-python`. No API keys, no telemetry, no code leaves the machine.
- **Process-isolated.** Only reads files; never imports or executes your project's code.
- **Skeptic prompting.** The LLM is instructed to ignore misleading names and summarize what the code *actually executes*.
- **Hash-based incremental cache.** SHA-256 per file; only changed files get re-analyzed.
- **AST-level extraction.** Functions, classes, methods, signatures, and a 50-line logic preview per symbol — not just names.
- **Auto-injection.** Files without a module docstring get a real one written in, derived from the model's intent.
- **Dependency graph.** Every file's imports are mapped into a global graph, exposing the project's nervous system.
- **DebugFlow integration.** Logs route through `debugflow.logger_system`; the resulting map is consumed by the DebugFlow surgeon for crash repair.
- **Toggleable AI chatter.** Mute the LLM's status logs without touching the rest of DebugFlow's logging.
- **Crash-safe persistence.** State is `fsync`'d to disk after each scan; partial runs survive interruption.

---

## API Usage / Examples

### Mapping a single project

```python
from context_stream import ContextStream

stream = ContextStream("/path/to/project")
project_map, stats = stream.run()
```

### Ignoring framework / boilerplate directories

```python
stream = Contextstream(
    project_path=".",
    ignore_list=["migrations", "tests", "conftest.py"]
)
project_map, stats = stream.run()
```

Entries in `ignore_list` are matched against both directory names and file names.

### Reading a previously generated map

```python
import json
from pathlib import Path

summary = json.loads(Path("context/project_summary.json").read_text())

print("Project:", summary["project_name"])
for entry in summary["map"]:
    print(f"  {entry['file']}: {entry['intent']}")
```

### Inspecting the dependency graph

```python
import json
from pathlib import Path

summary = json.loads(Path("context/project_summary.json").read_text())

for file, deps in summary["dependencies"].items():
    print(f"{file}")
    for d in deps:
        print(f"   └─ {d}")
```

### Running silently (no AI logs)

```python
stream = ContextStream(
    project_path=".",
    logs_on=True,           # keep DebugFlow's master pipe alive
    context_logs_on=False,  # silence the stream's own chatter
)
stream.run()
```

### Mapping without auto-injecting docstrings

If you want a read-only pass (no file mutations), disable injection:

```python
stream = ContextStream(".")
project_map, stats = stream.run(auto_inject=False)
```

### Switching the model at runtime

```python
from context_stream import set_model_path, get_model_path

set_model_path("/new/path/to/another-model.gguf")
print("Active model:", get_model_path())
```

---

## Configuration via environment variables

| Variable     | Purpose                                                                 | Default                                                |
|--------------|-------------------------------------------------------------------------|--------------------------------------------------------|
| `MODEL_PATH` | Override the GGUF model path (takes precedence over the saved config).  | Falls back to `~/.context_stream/config.json`, then to `./models/google_gemma-3-4b-it-Q5_K_M.gguf` |

Persistent config is stored in:

- `~/.context_stream/config.json` — global model path.
- `<project>/context/cache.json` — per-project hash cache.
- `<project>/context/project_summary.json` — per-project neural map.
- `<project>/.context/stream_flow.log` — runtime log piped through DebugFlow.

The stream's chatter toggle is persisted at:

- `<install>/context_stream/.context_log_state` — `ON` / `OFF`.

---

## Console scripts

| Command                         | What it does                                                        |
|---------------------------------|---------------------------------------------------------------------|
| `context-stream <path>`         | Run a full scan over the given project path (use `.` for cwd).      |
| `context-stream model-path`     | Interactive prompt to link / re-link your GGUF model.               |
| `context-logs`                  | Toggle the stream's AI chatter ON ↔ OFF (state persists).           |
| `context-logs-on`               | Force AI chatter ON.                                                |
| `context-logs-off`              | Force AI chatter OFF (silenced).                                    |

You can also override the chatter state inline for a single run:

```bash
context-stream . context-logs off
```

---

## Project map schema

The `context/project_summary.json` written after each scan has this shape:

```json
{
  "project_name": "my_app",
  "tree": {
    "root": "my_app",
    "structure": [
      { "folder": "", "files": ["main.py", "utils.py"] },
      { "folder": "models", "files": ["data.py"] }
    ]
  },
  "dependencies": {
    "main.py": ["os", "utils", "models.data"],
    "utils.py": ["re", "pathlib"]
  },
  "map": [
    {
      "file": "main.py",
      "intent": "Orchestrates the request lifecycle and dispatches to handlers.",
      "index": {
        "run(args: list) -> None": "Parses CLI args and delegates to the appropriate handler."
      },
      "classes": {
        "App": {
          "intent": "Holds application state and routes incoming requests.",
          "methods": {
            "start(self) -> None": "Initialises the event loop and binds the socket."
          }
        }
      },
      "dependencies": ["os", "utils"],
      "docstring": "-------- main --------\nOrchestrates the request lifecycle.\n-------- main --------"
    }
  ]
}
```

---

## Project Status

**Stable:**

- AST parsing of functions, classes, methods (signature + docstring + 50-line logic preview).
- Local LLM summarization via `llama-cpp-python` with the skeptic prompt.
- Hash-based incremental cache and crash-safe `fsync` persistence.
- Auto-injection of file-level docstrings.
- Dependency graph extraction.
- CLI (`context-stream`, `model-path`) and persistent log-state toggles.
- DebugFlow logger integration (`debugflow.logger_system`, child-logger naming).
- `ignore_list` support for filtering framework noise.

**In progress / experimental:**

- `surgeon.operate()` — pulls the latest crash from DebugFlow's SpineLink, locates the offending file in the project map, and asks the LLM to propose a patch. Functional end-to-end but treated as experimental until the patching step is hardened.
- Richer class-level intent (currently uses the class docstring as the prompt; logic-preview-based class intent is on the bench).

---

## License

MIT © 2026 ProfessionalMario. See [LICENSE](LICENSE) for the full text.
