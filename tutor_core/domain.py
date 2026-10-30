"""Pure functions for recurrence and historical billing; Frappe integration pending."""
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP


def occurrence_dates(start: date, end: date, weekday: int):
    if not 0 <= weekday <= 6 or end < start:
        raise ValueError("invalid recurrence")
    day = start + timedelta(days=(weekday - start.weekday()) % 7)
    while day <= end:
        yield day
        day += timedelta(days=7)


def amount_for_minutes(rate, minutes):
    rate = Decimal(str(rate))
    if rate < 0 or minutes <= 0:
        raise ValueError("rate must be nonnegative and duration positive")
    return (rate * Decimal(minutes) / Decimal(60)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
