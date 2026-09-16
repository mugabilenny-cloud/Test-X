"""
Small, deterministic recommendation layer for the local prototype.

The recommender deliberately uses only first-party app signals already
available locally: the user's semester and recently opened resources. It
returns existing resource shapes so the normal Switch cards can render them.
A future production version can replace this function with a server-side
recommendation service without changing the UI contract.
"""
from local_client import fetch_active_courses, fetch_recently_viewed


def recommend_for_user(student_id: str, limit: int = 5) -> list[dict]:
    if not student_id or student_id == "demo-student":
        return []

    recent = fetch_recently_viewed(student_id=student_id, limit=20)
    seen = {r.get("resource_id") for r in recent if r.get("resource_id")}
    recommendations = []

    # History already contains the strongest local signal. For now we expose
    # a small "continue/review" set rather than inventing unrelated content.
    for item in recent:
        resource = {
            "id": item.get("resource_id"),
            "title": item.get("title", "Untitled"),
            "course_code": item.get("course_code", ""),
            "file_type": item.get("file_type", "link"),
            "url": item.get("url"),
            "youtube_video_id": item.get("youtube_video_id"),
            "reason": "Based on what you recently opened",
        }
        if resource["id"] and resource["id"] not in {r["id"] for r in recommendations}:
            recommendations.append(resource)
        if len(recommendations) >= limit:
            break

    # Keep the import here deliberately useful as the recommender grows:
    # active course context is available without changing its public contract.
    if not recommendations:
        fetch_active_courses(student_id=student_id)

    return recommendations[:limit]
