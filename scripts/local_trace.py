# local_trace.py
import json
import time
from threading import Lock

TRACE_FILE = "local_traces.json"
_lock = Lock()

def append_trace(event: dict):
    event.setdefault("timestamp", time.time())
    with _lock:
        try:
            with open(TRACE_FILE, "a") as f:
                f.write(json.dumps(event, indent=2) + ",\n")
        except Exception:
            # best-effort logging
            pass
