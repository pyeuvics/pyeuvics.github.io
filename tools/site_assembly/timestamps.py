"""One representable UTC timestamp policy for direct and CI builds."""
from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import re


class TimestampError(ValueError):
    """A deterministic build timestamp is missing or outside its allowed range."""


@dataclass(frozen=True)
class BuildTimestamp:
    epoch: str
    iso: str


def parse_timestamp(value: str | None) -> BuildTimestamp:
    if value is None:
        raise TimestampError('SOURCE_DATE_EPOCH is required for deterministic assembly')
    if not re.fullmatch(r'[0-9]+', value):
        raise TimestampError('SOURCE_DATE_EPOCH must be a representable non-negative integer timestamp')
    try:
        seconds = int(value)
        instant = dt.datetime.fromtimestamp(seconds, tz=dt.timezone.utc)
    except (ValueError, OverflowError, OSError) as exc:
        raise TimestampError('SOURCE_DATE_EPOCH must be a representable non-negative integer timestamp') from exc
    return BuildTimestamp(str(seconds), instant.isoformat().replace('+00:00', 'Z'))
