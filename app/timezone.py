from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    APP_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")
except ZoneInfoNotFoundError:
    APP_TIMEZONE = timezone(timedelta(hours=7), "Asia/Ho_Chi_Minh")


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_now() -> datetime:
    return datetime.now(APP_TIMEZONE).replace(tzinfo=None)


def utc_to_local(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(APP_TIMEZONE).replace(tzinfo=None)


def local_date_start_as_utc(value: date | None) -> datetime | None:
    if value is None:
        return None
    local_value = datetime.combine(value, time.min).replace(tzinfo=APP_TIMEZONE)
    return local_value.astimezone(timezone.utc).replace(tzinfo=None)


def local_date_end_as_utc(value: date | None) -> datetime | None:
    if value is None:
        return None
    local_value = datetime.combine(value, time.max).replace(tzinfo=APP_TIMEZONE)
    return local_value.astimezone(timezone.utc).replace(tzinfo=None)


def format_local_datetime(value: datetime | None, fmt: str = "%d/%m/%Y %H:%M") -> str:
    local_value = utc_to_local(value)
    return local_value.strftime(fmt) if local_value else ""


def format_local_date(value: datetime | None) -> str:
    return format_local_datetime(value, "%d/%m/%Y") or "-"
