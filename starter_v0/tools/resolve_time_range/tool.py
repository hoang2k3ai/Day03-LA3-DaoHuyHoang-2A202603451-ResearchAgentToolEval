from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from tools._shared import fold_text

VN_TZ = timezone(timedelta(hours=7))  # Vietnam has no DST; a fixed offset avoids tzdata on Windows.


def _now() -> datetime:
    return datetime.now(VN_TZ)


def _monday(day: date) -> date:
    return day - timedelta(days=day.weekday())


def resolve_time_range(phrase: str = "") -> dict[str, Any]:
    """Turn a Vietnamese time phrase into an explicit date range (Vietnam time)."""
    key = " ".join(fold_text(phrase or "").split())
    today = _now().date()
    yesterday = today - timedelta(days=1)
    ranges = {
        "hom nay": (today, today, "hôm nay"),
        "hom qua": (yesterday, yesterday, "hôm qua"),
        "tuan nay": (_monday(today), today, "tuần này"),
        "tuan truoc": (_monday(today) - timedelta(days=7), _monday(today) - timedelta(days=1), "tuần trước"),
        "thang nay": (today.replace(day=1), today, "tháng này"),
        "nam nay": (today.replace(month=1, day=1), today, "năm nay"),
    }
    if key not in ranges:
        return {
            "tool": "resolve_time_range",
            "error": "UnsupportedPhrase",
            "message": "supported: hôm nay, hôm qua, tuần này, tuần trước, tháng này, năm nay",
        }
    start, end, label = ranges[key]
    return {
        "tool": "resolve_time_range",
        "label": label,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "timezone": "Asia/Ho_Chi_Minh",
    }
