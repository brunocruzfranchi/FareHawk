import warnings
from datetime import datetime

from core.time import utc_now


def test_utc_now_returns_naive_utc_datetime_without_deprecation_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        value = utc_now()

    assert isinstance(value, datetime)
    assert value.tzinfo is None
    assert not [warning for warning in caught if warning.category is DeprecationWarning]
