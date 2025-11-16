from datetime import datetime, timedelta

import pytest

from src.services.booking_rules import validate_time_block


def _hour(start: int, duration: int = 1):
    base = datetime(2025, 1, 1, start, 0, 0)
    return base, base + timedelta(hours=duration)


def test_validate_time_block_accepts_within_limits():
    start, end = _hour(9, 2)
    validate_time_block(start, end)  # should not raise


def test_validate_time_block_rejects_partial_hours():
    start = datetime(2025, 1, 1, 10, 30)
    end = start + timedelta(hours=1)
    with pytest.raises(ValueError):
        validate_time_block(start, end)


def test_validate_time_block_rejects_longer_than_max():
    start, end = _hour(8, 12)
    with pytest.raises(ValueError):
        validate_time_block(start, end)

