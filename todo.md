Project Intelligence: The Ghost Pipeline
Goal: Create a high-performance, local-first autonomous debugging framework that bridges the gap between static code architecture and live runtime failures.

1. The Vision (Final Goal)
To build a "Zero-Click" developer tool where a local LLM (Gemma-3) acts as a resident Code Surgeon. When a crash occurs, the system automatically cross-references the Project Map with the Live Traceback and applies a verified code patch, refreshing the developer's HUD (Heads-Up Display) in real-time.

2. System Component 1: DebugFlow (The Live Sentinel)
Purpose: Real-time runtime telemetry and crash capture.

Log-Only Neural Bridge: No slow JSON sidecar files. It communicates live state via a high-speed debugflow.log.

SpineLink: A specialized bridge that harvests "Red Node" evidence (locals, global state, and tensor shapes).

_safe_serialize: An engine that converts complex Python objects (like Torch Tensors or DataFrames) into human-readable metadata without crashing the logger.

Ghost Pipeline: A watcher service that "ignites" a refresh of the HUD/Project Map immediately after a patch is applied.

3. System Component 2: Context Engine (The Architect)
Purpose: Global project awareness and intent mapping.

Semantic Mapping: Crawls the project to build a project_summary.json containing the Intent (the "Why") of every file and function.

AI Synthesis (The Thinking Summarizer): * Uses Gemma-3 to "read" code that lacks docstrings.

Chunking Logic: Splits massive files into 2000-token chunks, summarizes them individually, and synthesizes a "Master Summary" to prevent context window overflow.

SHA-256 Caching: Only re-scans files that have changed, ensuring a near-instant (0.10s) response time for large projects.

Intelligence Boundaries: Purposely ignores technical noise (args/params) because it knows DebugFlow will provide that live during a crash.

4. System Component 3: The Surgeon (The Coordinator)
Purpose: The bridge between the Map and the Crime Scene.

Evidence Harvesting: Parses the debugflow.log using regex to find the exact file and line of the last failure.

Context Filtering: Injects only the relevant "Intent Map" into the LLM prompt to save tokens and maintain high precision.

Autonomous Patching: Generates a full-file rewrite for the broken module and executes the disk-write, followed by a Ghost Pipeline refresh.

5. Current Status (April 2026)
Scanner/Parser: Complete. Uses AST to map classes and functions.

AI Summarizer: Refactored to handle large-file chunking and synthesis.

SpineLink: Active. Direct-to-log mode is functional.

Model Loader: Lazy-loading logic implemented for Gemma-3 GGUF via llama-cpp-python.

Current Challenge: Finalizing the absolute import structure and testing the "Full Loop" (Crash → Scan → AI Fix → Ghost Refresh).

6. Desired Capabilities for Tomorrow
Refinement of the Surgeon Prompt: Ensuring the LLM produces stable, production-ready code without excessive "chat" or explanations.

Cross-File Traceback: Enhancing the Context Engine to follow the "trail of imports" if the bug is caused by a change in a different file than the one that crashed.

Autonomous Review: A logic gate that double-checks if the patched code compiles before overwriting the source.

Prompt for the next LLM: > "I am building a system called the Ghost Pipeline. It consists of DebugFlow (runtime logging) and a Context Engine (static project mapping). I have provided the architectural summary. Please help me refine the Surgeon logic to ensure the local Gemma-3 model uses the Project Map effectively to fix runtime crashes."