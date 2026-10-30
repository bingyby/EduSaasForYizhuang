"""Independent edge-case tests for the prototype's pure business calculations."""
import unittest
from datetime import date
from decimal import Decimal

from tutor_core.domain import amount_for_minutes, occurrence_dates


class RecurrenceBoundaryTests(unittest.TestCase):
    def test_nonmatching_single_day_produces_no_occurrence(self):
        self.assertEqual(list(occurrence_dates(date(2026, 10, 22), date(2026, 10, 22), 2)), [])

    def test_weekly_range_crosses_year_boundary(self):
        self.assertEqual(
            list(occurrence_dates(date(2025, 12, 31), date(2026, 1, 7), 2)),
            [date(2025, 12, 31), date(2026, 1, 7)],
        )

    def test_invalid_weekday_and_end_date_are_rejected(self):
        for weekday in (-1, 7):
            with self.subTest(weekday=weekday), self.assertRaises(ValueError):
                list(occurrence_dates(date(2026, 1, 1), date(2026, 1, 31), weekday))
        with self.assertRaises(ValueError):
            list(occurrence_dates(date(2026, 1, 2), date(2026, 1, 1), 0))


class BillingBoundaryTests(unittest.TestCase):
    def test_partial_hour_and_money_rounding(self):
        self.assertEqual(amount_for_minutes('1', 1), Decimal('0.02'))
        self.assertEqual(amount_for_minutes('250', 30), Decimal('125.00'))
        self.assertEqual(amount_for_minutes('350', 120), Decimal('700.00'))

    def test_zero_rate_is_allowed_but_negative_rate_and_duration_are_not(self):
        self.assertEqual(amount_for_minutes('0', 60), Decimal('0.00'))
        for rate, minutes in [('-1', 60), ('250', 0), ('250', -1)]:
            with self.subTest(rate=rate, minutes=minutes), self.assertRaises(ValueError):
                amount_for_minutes(rate, minutes)


if __name__ == '__main__':
    unittest.main()
