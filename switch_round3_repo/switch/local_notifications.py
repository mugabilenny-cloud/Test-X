"""
Push-notification groundwork for the future Switch smartphone app.

This module stores provider-neutral subscription records and notification
jobs locally. It does NOT claim to send native push notifications. A future
mobile/web push adapter can consume pending jobs and deliver them through
FCM/APNs/Web Push while keeping this data contract stable.
"""
import json
import os
import time
import uuid
from pathlib import Path
from typing import Optional

SUBSCRIPTIONS_PATH = Path(__file__).parent / "data" / "push_subscriptions.json"
JOBS_PATH = Path(__file__).parent / "data" / "notification_jobs.json"


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


def register_subscription(
    user_id: str,
    platform: str,
    token: Optional[str] = None,
    endpoint: Optional[str] = None,
    p256dh: Optional[str] = None,
    auth: Optional[str] = None,
) -> dict:
    """Register an FCM/APNs-style token or Web Push subscription."""
    subscription_id = uuid.uuid4().hex
    record = {
        "id": subscription_id,
        "user_id": user_id,
        "platform": platform,  # ios | android | web
        "token": token,
        "endpoint": endpoint,
        "keys": {"p256dh": p256dh, "auth": auth},
        "active": True,
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    data = _read_json(SUBSCRIPTIONS_PATH)
    data[subscription_id] = record
    _write_json_atomic(SUBSCRIPTIONS_PATH, data)
    return record


def subscriptions_for_user(user_id: str) -> list[dict]:
    return [
        s for s in _read_json(SUBSCRIPTIONS_PATH).values()
        if s.get("user_id") == user_id and s.get("active", True)
    ]


def queue_notification(
    title: str,
    body: str,
    audience: str = "all",
    user_ids: Optional[list[str]] = None,
    data: Optional[dict] = None,
) -> dict:
    job_id = uuid.uuid4().hex
    job = {
        "id": job_id,
        "title": title.strip(),
        "body": body.strip(),
        "audience": audience,  # all | users
        "user_ids": user_ids or [],
        "data": data or {},
        "status": "pending",
        "created_at": time.time(),
    }
    jobs = _read_json(JOBS_PATH)
    jobs[job_id] = job
    _write_json_atomic(JOBS_PATH, jobs)
    return job


def pending_notifications() -> list[dict]:
    jobs = list(_read_json(JOBS_PATH).values())
    return [j for j in jobs if j.get("status") == "pending"]


def mark_notification_status(job_id: str, status: str) -> None:
    jobs = _read_json(JOBS_PATH)
    if job_id in jobs:
        jobs[job_id]["status"] = status
        jobs[job_id]["updated_at"] = time.time()
        _write_json_atomic(JOBS_PATH, jobs)
