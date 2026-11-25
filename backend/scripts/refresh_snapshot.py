"""Rewrite data/live_snapshot.json from the live sources. Run daily by .github/workflows/refresh-data.yml.

    python scripts/refresh_snapshot.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from adapters import sources  # noqa: E402

snapshot = {}
for key, fetch in (
    ("countries", sources.openalex_countries),
    ("price_levels", sources.worldbank_price_levels),
    ("fx", sources.fx_rates),
    ("unis_default", lambda: sources.openalex_universities(per_page=20)),
):
    try:
        snapshot[key] = fetch()
        print(f"{key}: ok")
    except Exception as exc:  # keep the previous value for a source that is down today
        print(f"{key}: failed ({exc})")

path = ROOT / "data" / "live_snapshot.json"
try:
    old = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    old = {}
merged = {**old, **{k: v for k, v in snapshot.items() if v}}
path.write_text(json.dumps(merged, separators=(",", ":")), encoding="utf-8")
print(f"wrote {path} ({path.stat().st_size // 1024} KB)")
