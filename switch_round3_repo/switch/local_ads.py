"""
Local advertising store for the Switch prototype.

Ads are created by the separate admin dashboard (pages/7_Admin.py) and stored
in data/ads.json. Uploaded creative files live under assets/ads/. This is
intentionally provider-neutral so the same ad contract can later be backed by
a hosted database/object store without changing the Home layout.
"""
import json
import os
import time
import uuid
from pathlib import Path
from typing import Optional

ADS_PATH = Path(__file__).parent / "data" / "ads.json"
AD_ASSET_DIR = Path(__file__).parent / "assets" / "ads"


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp_path.write_text(json.dumps(data, indent=2))
    os.replace(tmp_path, path)


def _is_active(ad: dict, now: Optional[float] = None) -> bool:
    now = now or time.time()
    if not ad.get("active", True):
        return False
    if ad.get("starts_at") and now < ad["starts_at"]:
        return False
    if ad.get("ends_at") and now >= ad["ends_at"]:
        return False
    return True


def list_ads(active_only: bool = True) -> list[dict]:
    ads = list(_read_json(ADS_PATH).values())
    ads.sort(key=lambda a: a.get("created_at", 0), reverse=True)
    return [a for a in ads if not active_only or _is_active(a)]


def get_ads_for_home(course_names: Optional[list[str]] = None, limit: int = 3) -> list[dict]:
    """Return active ads, preferring ads targeted to the user's courses."""
    course_names = set(course_names or [])
    ads = list_ads(active_only=True)
    return [a for a in ads if not a.get("course_names") or course_names.intersection(a.get("course_names", []))][:limit]


def record_ad_impression(ad_id: str) -> None:
    ads = _read_json(ADS_PATH)
    if ad_id in ads:
        ads[ad_id]["impressions"] = int(ads[ad_id].get("impressions", 0)) + 1
        _write_json_atomic(ADS_PATH, ads)


def record_ad_click(ad_id: str) -> None:
    ads = _read_json(ADS_PATH)
    if ad_id in ads:
        ads[ad_id]["clicks"] = int(ads[ad_id].get("clicks", 0)) + 1
        _write_json_atomic(ADS_PATH, ads)


def create_ad(
    title: str,
    advertiser: str,
    body: str,
    destination_url: str,
    course_names: Optional[list[str]] = None,
    asset_filename: Optional[str] = None,
    starts_at: Optional[float] = None,
    ends_at: Optional[float] = None,
) -> dict:
    ad_id = uuid.uuid4().hex
    record = {
        "id": ad_id,
        "title": title.strip(),
        "advertiser": advertiser.strip(),
        "body": body.strip(),
        "destination_url": destination_url.strip(),
        "course_names": course_names or [],
        "asset_filename": asset_filename,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "active": True,
        "created_at": time.time(),
    }
    ads = _read_json(ADS_PATH)
    ads[ad_id] = record
    _write_json_atomic(ADS_PATH, ads)
    return record


def set_ad_active(ad_id: str, active: bool) -> None:
    ads = _read_json(ADS_PATH)
    if ad_id in ads:
        ads[ad_id]["active"] = bool(active)
        _write_json_atomic(ADS_PATH, ads)


def save_asset(uploaded_file) -> Optional[str]:
    """Persist a Streamlit UploadedFile and return its repo-relative path."""
    if uploaded_file is None:
        return None
    AD_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(uploaded_file.name).suffix.lower()
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    destination = AD_ASSET_DIR / safe_name
    destination.write_bytes(uploaded_file.getbuffer())
    return f"assets/ads/{safe_name}"
