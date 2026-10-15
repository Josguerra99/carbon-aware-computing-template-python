from __future__ import annotations

import os


def backend_preference() -> str:
    raw = (os.environ.get("TF_BACKEND") or os.environ.get("TFJS_BACKEND") or "").strip().lower()
    if raw in ("gpu", "cuda"):
        return "gpu"
    if raw == "cpu":
        return "cpu"
    return "auto"


def ensure_tf_backend() -> str:
    """Log TensorFlow device choice (mirrors Node ensureTfBackend)."""
    import tensorflow as tf

    pref = backend_preference()
    gpus = tf.config.list_physical_devices("GPU")
    if pref == "cpu":
        try:
            tf.config.set_visible_devices([], "GPU")
        except RuntimeError:
            pass
        name = "cpu"
    elif gpus:
        name = "gpu"
    else:
        name = "cpu"
    print(f"TensorFlow backend: {name} (devices={tf.config.list_logical_devices()})")
    return name
