import csv
import os
from typing import List, Optional
from datetime import datetime
from models import Expense
from database import DatabaseManager
from analytics import AnalyticsEngine

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

class ExpenseReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 41, 59) # Slate 800
        self.cell(0, 10, "Expense Tracker & Summary Report", border=0, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(100, 116, 139) # Slate 500
        self.cell(0, 6, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", border=0, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

class Exporter:
    @staticmethod
    def export_to_csv(expenses: List[Expense], file_path: str) -> bool:
        """Exports a list of expenses to a CSV file."""
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["ID", "Title", "Amount", "Category", "Date", "Payment Method", "Notes", "Created At"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for exp in expenses:
                    writer.writerow({
                        "ID": exp.id,
                        "Title": exp.title,
                        "Amount": f"{exp.amount:.2f}",
                        "Category": exp.category,
                        "Date": exp.date,
                        "Payment Method": exp.payment_method,
                        "Notes": exp.notes or "",
                        "Created At": exp.created_at or ""
                    })
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False

    @staticmethod
    def export_summary_to_text(db: DatabaseManager, file_path: str, month: Optional[str] = None) -> bool:
        """Exports formatted summary report to a text file."""
        try:
            analytics = AnalyticsEngine(db)
            report_text = analytics.generate_text_summary(month)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report_text)
            return True
        except Exception as e:
            print(f"Error exporting summary text: {e}")
            return False

    @staticmethod
    def export_summary_to_pdf(db: DatabaseManager, file_path: str, month: Optional[str] = None) -> bool:
        """Generates a professional PDF report using fpdf2."""
        if not HAS_FPDF:
            # Fallback to text file
            txt_path = file_path if file_path.endswith(".txt") else file_path + ".txt"
            return Exporter.export_summary_to_text(db, txt_path, month)

        try:
            analytics = AnalyticsEngine(db)
            metrics = analytics.get_monthly_metrics(month or datetime.now().strftime("%Y-%m"))
            overall = db.get_overall_stats()

            pdf = ExpenseReportPDF(orientation="P", unit="mm", format="A4")
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Section: Period Banner
            pdf.set_fill_color(241, 245, 249)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 10, f" Reporting Period: {metrics['month']}", fill=True, border=0, align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

            # Metrics Table / Grid
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(51, 65, 85)
            
            # Row 1
            pdf.set_fill_color(248, 250, 252)
            pdf.cell(95, 8, f" Total Monthly Spent: ${metrics['total_spent']:,.2f}", border=1, fill=True)
            pdf.cell(95, 8, f" Total Transactions: {metrics['total_count']}", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

            # Row 2
            pdf.cell(95, 8, f" Daily Average: ${metrics['daily_average']:,.2f}", border=1)
            pdf.cell(95, 8, f" Top Category: {metrics['top_category']} (${metrics['top_category_amount']:,.2f})", border=1, new_x="LMARGIN", new_y="NEXT")

            if metrics["budget"] is not None:
                # Budget row
                status = "Within Budget" if metrics["budget_remaining"] >= 0 else "OVER BUDGET"
                pdf.cell(95, 8, f" Monthly Budget: ${metrics['budget']:,.2f}", border=1, fill=True)
                pdf.cell(95, 8, f" Status: {status} (${metrics['budget_remaining']:,.2f} left)", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

            pdf.ln(6)

            # Category Breakdown Section Header
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 8, "Category Breakdown", border=0, new_x="LMARGIN", new_y="NEXT")

            # Table Header
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(226, 232, 240)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(60, 7, " Category", border=1, fill=True)
            pdf.cell(45, 7, " Amount ($)", border=1, fill=True, align="R")
            pdf.cell(45, 7, " % Share", border=1, fill=True, align="R")
            pdf.cell(40, 7, " Count", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

            # Table Rows
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(51, 65, 85)
            
            if metrics["categories"]:
                for cat in metrics["categories"]:
                    pct = (cat["total_amount"] / metrics["total_spent"] * 100) if metrics["total_spent"] > 0 else 0
                    pdf.cell(60, 6, f" {cat['category']}", border=1)
                    pdf.cell(45, 6, f"${cat['total_amount']:,.2f}", border=1, align="R")
                    pdf.cell(45, 6, f"{pct:.1f}%", border=1, align="R")
                    pdf.cell(40, 6, str(cat['count']), border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(190, 6, "No expenses recorded for this month.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

            pdf.ln(6)

            # All time section
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 8, "All-Time Financial Overview", border=0, new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(51, 65, 85)
            pdf.cell(95, 6, f"Lifetime Total Spent: ${overall['total_spending']:,.2f}", border=0)
            pdf.cell(95, 6, f"Total Entries: {overall['total_count']}", border=0, new_x="LMARGIN", new_y="NEXT")
            pdf.cell(95, 6, f"Average / Entry: ${overall['average_expense']:,.2f}", border=0)
            pdf.cell(95, 6, f"Highest Single Expense: ${overall['highest_expense']:,.2f}", border=0, new_x="LMARGIN", new_y="NEXT")

            pdf.output(file_path)
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False
