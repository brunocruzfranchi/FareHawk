"""Time helpers for UTC timestamps.

The database schema stores naive ``DateTime`` values today. ``utc_now`` keeps
that storage contract while avoiding ``datetime.utcnow()``, which is deprecated
on newer Python versions.
"""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current UTC time as a naive datetime for ORM storage."""
    return datetime.now(UTC).replace(tzinfo=None)
