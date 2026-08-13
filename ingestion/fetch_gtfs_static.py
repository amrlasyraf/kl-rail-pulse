"""Bronze: download raw GTFS static ZIPs from data.gov.my, unmodified, as-is."""
import sys
from datetime import datetime, timezone

import requests

from config import GTFS_STATIC_BRONZE_DIR, GTFS_STATIC_URL, RAIL_CATEGORY


def fetch(category: str) -> tuple[str, object]:
    """Download one category's GTFS static ZIP. Returns (batch_id, path)."""
    resp = requests.get(GTFS_STATIC_URL, params={"category": category}, timeout=60)
    resp.raise_for_status()

    batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = GTFS_STATIC_BRONZE_DIR / category
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{batch_id}.zip"
    out_path.write_bytes(resp.content)

    latest_path = out_dir / "latest.zip"
    latest_path.write_bytes(resp.content)

    print(f"[bronze] {category}: {len(resp.content):,} bytes -> {out_path}")
    return batch_id, out_path


if __name__ == "__main__":
    categories = sys.argv[1:] or [RAIL_CATEGORY]
    for cat in categories:
        fetch(cat)
