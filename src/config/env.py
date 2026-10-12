from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

MAIN_SERVER_URL = (os.getenv("MAIN_SERVER_URL") or "http://192.168.0.232:3915").rstrip("/")
PORT = int(os.getenv("PORT") or "3916")
TRAIN_DATASETS = (os.getenv("TRAIN_DATASETS") or "all").strip()

_raw_ttl = os.getenv("HISTORIC_CACHE_TTL_MS")
try:
    _ttl = int(_raw_ttl) if _raw_ttl is not None else 0
except ValueError:
    _ttl = 0
HISTORIC_CACHE_TTL_MS = _ttl if _ttl > 0 else 0

REFRESH_HISTORIC = (os.getenv("REFRESH_HISTORIC") or "").strip().lower() in ("1", "true", "yes")
