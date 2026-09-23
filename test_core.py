import os
import unittest
from datetime import datetime
from models import Expense, validate_expense_input
from database import DatabaseManager
from analytics import AnalyticsEngine
from exporter import Exporter

class TestExpenseTrackerCore(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_expenses.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.db = DatabaseManager(self.test_db, auto_seed=False)
        self.analytics = AnalyticsEngine(self.db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists("test_export.csv"):
            os.remove("test_export.csv")
        if os.path.exists("test_report.pdf"):
            os.remove("test_report.pdf")
        if os.path.exists("test_report.txt"):
            os.remove("test_report.txt")

    def test_validation(self):
        valid, msg = validate_expense_input("Coffee", "4.50", "Food", "2026-09-14")
        self.assertTrue(valid)

        invalid_amt, msg = validate_expense_input("Coffee", "-10", "Food", "2026-09-14")
        self.assertFalse(invalid_amt)

        invalid_date, msg = validate_expense_input("Coffee", "10", "Food", "14-09-2026")
        self.assertFalse(invalid_date)

    def test_crud_operations(self):
        # Create
        exp = Expense(
            title="Dinner",
            amount=45.50,
            category="Food",
            date="2026-09-14",
            payment_method="Credit Card",
            notes="Dinner at Italian Place"
        )
        exp_id = self.db.add_expense(exp)
        self.assertIsNotNone(exp_id)
        self.assertGreater(exp_id, 0)

        # Read
        fetched = self.db.get_expense(exp_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Dinner")
        self.assertEqual(fetched.amount, 45.50)
        self.assertEqual(fetched.category, "Food")

        # Update
        fetched.title = "Dinner & Wine"
        fetched.amount = 60.00
        success = self.db.update_expense(fetched)
        self.assertTrue(success)

        updated = self.db.get_expense(exp_id)
        self.assertEqual(updated.title, "Dinner & Wine")
        self.assertEqual(updated.amount, 60.00)

        # Delete
        del_success = self.db.delete_expense(exp_id)
        self.assertTrue(del_success)
        self.assertIsNone(self.db.get_expense(exp_id))

    def test_filtering(self):
        self.db.add_expense(Expense(title="Bus", amount=5.00, category="Travel", date="2026-09-10"))
        self.db.add_expense(Expense(title="Flight", amount=250.00, category="Travel", date="2026-09-12"))
        self.db.add_expense(Expense(title="Lunch", amount=15.00, category="Food", date="2026-09-13"))

        # Category filter
        travel_items = self.db.filter_expenses(category="Travel")
        self.assertEqual(len(travel_items), 2)

        # Amount range filter
        mid_items = self.db.filter_expenses(min_amount=10.0, max_amount=100.0)
        self.assertEqual(len(mid_items), 1)
        self.assertEqual(mid_items[0].title, "Lunch")

        # Keyword search
        search_items = self.db.filter_expenses(search_keyword="Flight")
        self.assertEqual(len(search_items), 1)

    def test_analytics_and_export(self):
        self.db.seed_sample_data()
        metrics = self.analytics.get_monthly_metrics(datetime.now().strftime("%Y-%m"))
        self.assertGreater(metrics["total_spent"], 0)

        # Export CSV
        all_exp = self.db.get_all_expenses()
        csv_ok = Exporter.export_to_csv(all_exp, "test_export.csv")
        self.assertTrue(csv_ok)
        self.assertTrue(os.path.exists("test_export.csv"))

        # Export PDF
        pdf_ok = Exporter.export_summary_to_pdf(self.db, "test_report.pdf")
        self.assertTrue(pdf_ok)
        self.assertTrue(os.path.exists("test_report.pdf"))

        # Export Text
        txt_ok = Exporter.export_summary_to_text(self.db, "test_report.txt")
        self.assertTrue(txt_ok)
        self.assertTrue(os.path.exists("test_report.txt"))

if __name__ == "__main__":
    unittest.main()
