"""Stale-while-revalidate cache with a committed snapshot, so no page ever waits on an outside API.

get(key, fetch, ttl):
  fresh value in memory  -> return it
  stale value in memory  -> return it now, refresh in a background thread
  nothing in memory      -> return the snapshot value now (data/live_snapshot.json), refresh in the background;
                            only if there is no snapshot either does it fetch inline
The snapshot is rewritten by scripts/refresh_snapshot.py (a daily GitHub Action), so a cold start still has data.
"""
import json
import threading
import time
from pathlib import Path

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "live_snapshot.json"
_mem, _inflight, _lock = {}, set(), threading.Lock()
try:
    _snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
except Exception:
    _snapshot = {}


def _refresh(key, fetch):
    try:
        value = fetch()
        if value:
            with _lock:
                _mem[key] = (time.time(), value)
    except Exception as exc:
        print(f"adapters.cache: refresh of {key} failed: {exc}")
    finally:
        with _lock:
            _inflight.discard(key)


def _refresh_async(key, fetch):
    with _lock:
        if key in _inflight:
            return
        _inflight.add(key)
    threading.Thread(target=_refresh, args=(key, fetch), daemon=True).start()


def get(key, fetch, ttl, snapshot_key=None):
    with _lock:
        hit = _mem.get(key)
    if hit:
        if time.time() - hit[0] >= ttl:
            _refresh_async(key, fetch)
        return hit[1]
    snap = _snapshot.get(snapshot_key or key)
    if snap:
        _refresh_async(key, fetch)
        return snap
    try:
        value = fetch()
    except Exception as exc:
        print(f"adapters.cache: first fetch of {key} failed: {exc}")
        return None
    if value:
        with _lock:
            _mem[key] = (time.time(), value)
    return value


def warm(jobs):
    """Fill the cache at startup without blocking it. jobs = [(key, fetch, ttl), ...]"""
    for key, fetch, _ in jobs:
        _refresh_async(key, fetch)
