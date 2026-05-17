"""
File summary: This Python code loads and initializes a Llama model using the llama-cpp-python library, prioritizing using an environment variable for the model path or falling back to a default location, and includes logging for loading and warmup processes.
"""

import os
import time
import logging
from pathlib import Path
from llama_cpp import Llama

logger = logging.getLogger(__name__)

# -----------------------------
# CONFIG
# -----------------------------
DEFAULT_MODEL_NAME = "google_gemma-3-4b-it-Q5_K_M.gguf"  # update after download
MODELS_DIR = "models"

_llm = None


# -----------------------------
# RESOLVE MODEL PATH
# -----------------------------
def resolve_model_path() -> Path:
    # 1️⃣ ENV override (cloud / prod)
    env_path = os.getenv("MODEL_PATH")
    if env_path:
        return Path(env_path)

    # 2️⃣ Local fallback
    base_dir = Path(__file__).parent
    return base_dir / MODELS_DIR / DEFAULT_MODEL_NAME


# -----------------------------
# LOAD MODEL (LAZY)
# -----------------------------
def get_model():
    global _llm

    if _llm:
        return _llm

    model_path = resolve_model_path()

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}\n"
            f"👉 Place GGUF inside /models or set MODEL_PATH env"
        )

    logger.info(f"[MODEL] Loading: {model_path}")

    start = time.time()
    _llm = Llama(
        model_path=str(model_path),
        n_ctx=4096,
        n_threads=os.cpu_count() or 8,
        n_gpu_layers=1,
        n_batch=512,        # 🔥 BIG speed gain
        use_mmap=True,
        use_mlock=False,
        verbose=False
)

    load_time = time.time() - start
    logger.info(f"[MODEL] Loaded in {load_time:.2f}s")

    # 🔥 Warmup (important)
    warmup_model(_llm)

    return _llm


# -----------------------------
# WARMUP
# -----------------------------
def warmup_model(llm):
    logger.info("[MODEL] Warming up...")

    start = time.time()

    llm(
        "Hello",
        max_tokens=5,
    )

    warmup_time = time.time() - start
    logger.info(f"[MODEL] Warmup complete in {warmup_time:.2f}s")