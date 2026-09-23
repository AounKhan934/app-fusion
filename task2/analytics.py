from typing import List, Dict, Any, Optional
from datetime import datetime
import calendar
from database import DatabaseManager
from models import Expense

class AnalyticsEngine:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_monthly_metrics(self, year_month: str) -> Dict[str, Any]:
        """Calculates detailed metrics for a specific month (YYYY-MM)."""
        category_summary = self.db.get_category_summary(month=year_month)
        daily_trend = self.db.get_daily_trend(month=year_month)
        budget = self.db.get_budget(year_month)

        total_spent = sum(item["total_amount"] for item in category_summary)
        total_count = sum(item["count"] for item in category_summary)

        # Days in month
        try:
            year, month = map(int, year_month.split("-"))
            _, num_days = calendar.monthrange(year, month)
        except Exception:
            num_days = 30

        # If current month, calculate avg based on days passed so far
        now = datetime.now()
        if year_month == now.strftime("%Y-%m"):
            days_passed = max(1, now.day)
            daily_avg = total_spent / days_passed
        else:
            daily_avg = total_spent / max(1, num_days)

        # Highest spending day
        highest_day = {"date": "N/A", "daily_total": 0.0}
        if daily_trend:
            highest_day = max(daily_trend, key=lambda x: x["daily_total"])

        # Top category
        top_category = "N/A"
        top_cat_amount = 0.0
        if category_summary:
            top_cat_obj = max(category_summary, key=lambda x: x["total_amount"])
            top_category = top_cat_obj["category"]
            top_cat_amount = top_cat_obj["total_amount"]

        # Budget calculation
        budget_remaining = None
        budget_percent_used = None
        if budget is not None and budget > 0:
            budget_remaining = budget - total_spent
            budget_percent_used = (total_spent / budget) * 100

        return {
            "month": year_month,
            "total_spent": total_spent,
            "total_count": total_count,
            "daily_average": daily_avg,
            "top_category": top_category,
            "top_category_amount": top_cat_amount,
            "highest_day": highest_day["date"],
            "highest_day_amount": highest_day["daily_total"],
            "categories": category_summary,
            "daily_trend": daily_trend,
            "budget": budget,
            "budget_remaining": budget_remaining,
            "budget_percent_used": budget_percent_used
        }

    def generate_text_summary(self, year_month: Optional[str] = None) -> str:
        """Generates a nicely formatted text summary report."""
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        metrics = self.get_monthly_metrics(year_month)
        overall = self.db.get_overall_stats()

        lines = [
            "=" * 60,
            f"          EXPENSE TRACKER & SUMMARY REPORT",
            f"             Reporting Period: {year_month}",
            "=" * 60,
            f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "--- MONTHLY OVERVIEW ---",
            f"Total Monthly Spending : ${metrics['total_spent']:,.2f}",
            f"Total Transactions     : {metrics['total_count']}",
            f"Daily Average Expense  : ${metrics['daily_average']:,.2f}",
            f"Top Spending Category  : {metrics['top_category']} (${metrics['top_category_amount']:,.2f})",
            f"Peak Spending Date     : {metrics['highest_day']} (${metrics['highest_day_amount']:,.2f})",
        ]

        if metrics["budget"] is not None:
            status = "OVER BUDGET!" if metrics["budget_remaining"] < 0 else "Within Budget"
            lines.extend([
                "",
                "--- BUDGET TRACKING ---",
                f"Monthly Budget Limit   : ${metrics['budget']:,.2f}",
                f"Remaining Balance      : ${metrics['budget_remaining']:,.2f} ({status})",
                f"Budget Utilization     : {metrics['budget_percent_used']:.1f}%"
            ])

        lines.extend([
            "",
            "--- CATEGORY BREAKDOWN ---",
            f"{'Category':<20} {'Amount':>12} {'% of Total':>12} {'Count':>8}",
            "-" * 54
        ])

        if metrics["categories"]:
            for cat in metrics["categories"]:
                pct = (cat["total_amount"] / metrics["total_spent"] * 100) if metrics["total_spent"] > 0 else 0
                lines.append(f"{cat['category']:<20} ${cat['total_amount']:>11,.2f} {pct:>11.1f}% {cat['count']:>8}")
        else:
            lines.append("No expenses recorded for this period.")

        lines.extend([
            "",
            "--- ALL-TIME SUMMARY ---",
            f"Lifetime Total Spent   : ${overall['total_spending']:,.2f}",
            f"Total Lifetime Entries : {overall['total_count']}",
            f"All-time Average / Item: ${overall['average_expense']:,.2f}",
            f"Highest Single Expense : ${overall['highest_expense']:,.2f}",
            "=" * 60
        ])

        return "\n".join(lines)
