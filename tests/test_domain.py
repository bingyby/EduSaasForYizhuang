import unittest
from datetime import date
from decimal import Decimal
from tutor_core.domain import occurrence_dates, amount_for_minutes

class TestDomain(unittest.TestCase):
    def test_weekly_bounds(self):
        self.assertEqual(list(occurrence_dates(date(2026, 10, 21), date(2026, 11, 4), 2)), [date(2026, 10, 21), date(2026, 10, 28), date(2026, 11, 4)])
    def test_billing(self):
        self.assertEqual(amount_for_minutes("250", 90), Decimal("375.00"))
        self.assertEqual(amount_for_minutes("350", 60), Decimal("350.00"))
    def test_reject_invalid(self):
        with self.assertRaises(ValueError): amount_for_minutes(250, 0)
        with self.assertRaises(ValueError): list(occurrence_dates(date(2026, 1, 1), date(2025, 1, 1), 2))

if __name__ == "__main__": unittest.main()
