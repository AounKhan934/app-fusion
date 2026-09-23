import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from datetime import datetime
from typing import Optional, List

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from models import Expense, validate_expense_input, DEFAULT_PAYMENT_METHODS
from database import DatabaseManager
from analytics import AnalyticsEngine
from exporter import Exporter

# Set global appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class EditExpenseDialog(ctk.CTkToplevel):
    """Modal popup dialog to edit an existing expense."""
    def __init__(self, parent, expense: Expense, on_save_callback):
        super().__init__(parent)
        self.parent = parent
        self.expense = expense
        self.on_save_callback = on_save_callback

        self.title("Edit Expense")
        self.geometry("460x560")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = ctk.CTkLabel(
            self,
            text=f"Edit Expense (ID: #{self.expense.id})",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(pady=(20, 15), padx=25, anchor="w")

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=25, pady=5)

        # Title
        ctk.CTkLabel(form_frame, text="Title / Description *", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.title_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g. Grocery shopping")
        self.title_entry.insert(0, self.expense.title)
        self.title_entry.pack(fill="x", pady=(0, 10))

        # Amount
        ctk.CTkLabel(form_frame, text="Amount ($) *", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.amount_entry = ctk.CTkEntry(form_frame, placeholder_text="0.00")
        self.amount_entry.insert(0, f"{self.expense.amount:.2f}")
        self.amount_entry.pack(fill="x", pady=(0, 10))

        # Category & Payment Method in grid
        grid_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        grid_frame.pack(fill="x", pady=(0, 10))
        grid_frame.columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(grid_frame, text="Category *", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ctk.CTkLabel(grid_frame, text="Payment Method", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=1, sticky="w", padx=(5, 0))

        categories = self.parent.db.get_categories()
        self.category_opt = ctk.CTkOptionMenu(grid_frame, values=categories)
        if self.expense.category in categories:
            self.category_opt.set(self.expense.category)
        else:
            self.category_opt.set(categories[0] if categories else "Food")
        self.category_opt.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(2, 0))

        self.payment_opt = ctk.CTkOptionMenu(grid_frame, values=DEFAULT_PAYMENT_METHODS)
        if self.expense.payment_method in DEFAULT_PAYMENT_METHODS:
            self.payment_opt.set(self.expense.payment_method)
        else:
            self.payment_opt.set("Cash")
        self.payment_opt.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(2, 0))

        # Date
        ctk.CTkLabel(form_frame, text="Date (YYYY-MM-DD) *", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.date_entry = ctk.CTkEntry(form_frame, placeholder_text="YYYY-MM-DD")
        self.date_entry.insert(0, self.expense.date)
        self.date_entry.pack(fill="x", pady=(0, 10))

        # Notes
        ctk.CTkLabel(form_frame, text="Notes (Optional)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.notes_entry = ctk.CTkEntry(form_frame, placeholder_text="Additional details")
        self.notes_entry.insert(0, self.expense.notes or "")
        self.notes_entry.pack(fill="x", pady=(0, 15))

        # Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(0, 20))

        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", fg_color="gray50", hover_color="gray40", command=self.destroy)
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        save_btn = ctk.CTkButton(btn_frame, text="Save Changes", fg_color="#2563eb", hover_color="#1d4ed8", command=self.save_changes)
        save_btn.pack(side="right", fill="x", expand=True, padx=(8, 0))

    def save_changes(self):
        title = self.title_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        category = self.category_opt.get()
        payment_method = self.payment_opt.get()
        date_str = self.date_entry.get().strip()
        notes = self.notes_entry.get().strip()

        valid, error_msg = validate_expense_input(title, amount_str, category, date_str)
        if not valid:
            messagebox.showerror("Input Error", error_msg, parent=self)
            return

        self.expense.title = title
        self.expense.amount = float(amount_str)
        self.expense.category = category
        self.expense.payment_method = payment_method
        self.expense.date = date_str
        self.expense.notes = notes

        success = self.parent.db.update_expense(self.expense)
        if success:
            self.on_save_callback()
            self.destroy()
        else:
            messagebox.showerror("Database Error", "Failed to update the expense record.", parent=self)


class ExpenseTrackerApp(ctk.CTk):
    """Main Desktop Application Window."""
    def __init__(self):
        super().__init__()

        self.title("Expense Tracker & Financial Report Generator")
        self.geometry("1180x760")
        self.minsize(980, 640)

        # Database & Analytics Engine
        self.db = DatabaseManager()
        self.analytics = AnalyticsEngine(self.db)

        # Matplotlib styling helper
        self.chart_theme_dark = True

        # Setup GUI Components
        self.setup_layout()
        self.show_view("dashboard")

    def setup_layout(self):
        # Configure Grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. Sidebar Frame
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        # App Logo / Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="💰 ExpensePro",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(24, 8), sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Tracker & Reports",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Nav Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("add", "➕  Add Expense"),
            ("expenses", "📋  All Expenses"),
            ("filter", "🔍  Search & Filter"),
            ("reports", "📈  Reports & Analytics"),
            ("settings", "⚙️  Settings & Tools"),
        ]

        for i, (key, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=label,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray25"),
                height=40,
                command=lambda k=key: self.show_view(k)
            )
            btn.grid(row=i, column=0, padx=12, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        # Quick Status in Sidebar Bottom
        self.sidebar_footer = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_footer.grid(row=8, column=0, padx=16, pady=16, sticky="ew")

        self.theme_label = ctk.CTkLabel(self.sidebar_footer, text="Theme Mode", font=ctk.CTkFont(size=11))
        self.theme_label.pack(anchor="w")
        self.theme_option = ctk.CTkOptionMenu(
            self.sidebar_footer,
            values=["Dark", "Light", "System"],
            command=self.change_theme,
            height=28
        )
        self.theme_option.set("Dark")
        self.theme_option.pack(fill="x", pady=(2, 0))

        # 2. Main Content Container
        self.content_container = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray95", "gray12"))
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # Create Views
        self.views = {
            "dashboard": self.create_dashboard_view(),
            "add": self.create_add_expense_view(),
            "expenses": self.create_expenses_view(),
            "filter": self.create_filter_view(),
            "reports": self.create_reports_view(),
            "settings": self.create_settings_view()
        }

    def show_view(self, view_name: str):
        # Update sidebar button highlighting
        for key, btn in self.nav_buttons.items():
            if key == view_name:
                btn.configure(fg_color=("#2563eb", "#1d4ed8"), text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"))

        # Hide all views and show selected
        for v_name, view in self.views.items():
            view.grid_forget()

        selected_view = self.views.get(view_name)
        if selected_view:
            selected_view.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Refresh dynamic data for views
        if view_name == "dashboard":
            self.refresh_dashboard()
        elif view_name == "expenses":
            self.refresh_expenses_table()
        elif view_name == "filter":
            self.apply_filters()
        elif view_name == "reports":
            self.refresh_reports_view()
        elif view_name == "add":
            self.reset_add_form()

    def change_theme(self, mode: str):
        ctk.set_appearance_mode(mode)
        self.chart_theme_dark = (mode != "Light")
        self.refresh_dashboard()
        self.refresh_reports_view()

    # -------------------------------------------------------------
    # VIEW 1: DASHBOARD
    # -------------------------------------------------------------
    def create_dashboard_view(self) -> ctk.CTkFrame:
        view = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Top Header
        header_frame = ctk.CTkFrame(view, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 15))
        ctk.CTkLabel(
            header_frame,
            text="Financial Dashboard",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")

        # Quick Add Button in header
        quick_add_btn = ctk.CTkButton(
            header_frame,
            text="+ Add New Expense",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=lambda: self.show_view("add"),
            width=150,
            height=32
        )
        quick_add_btn.pack(side="right")

        # 4 Metric Cards
        self.kpi_cards = {}
        kpi_configs = [
            ("month_spend", "This Month Spend", "$0.00", "#3b82f6"),
            ("total_spend", "All-Time Spending", "$0.00", "#10b981"),
            ("daily_avg", "Daily Average (Month)", "$0.00", "#f59e0b"),
            ("top_cat", "Top Category", "N/A", "#8b5cf6")
        ]

        for col, (key, title, default_val, color) in enumerate(kpi_configs):
            card = ctk.CTkFrame(view, corner_radius=10)
            card.grid(row=1, column=col, padx=6, pady=6, sticky="ew")

            # Title
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11), text_color="gray60").pack(anchor="w", padx=14, pady=(12, 2))
            
            # Value
            val_lbl = ctk.CTkLabel(card, text=default_val, font=ctk.CTkFont(size=20, weight="bold"), text_color=color)
            val_lbl.pack(anchor="w", padx=14, pady=(0, 12))
            self.kpi_cards[key] = val_lbl

        # Charts Section
        chart_container = ctk.CTkFrame(view, corner_radius=10)
        chart_container.grid(row=2, column=0, columnspan=4, padx=6, pady=15, sticky="nsew")
        chart_container.grid_columnconfigure((0, 1), weight=1)

        # Left Chart: Category Donut
        self.dash_chart_left_frame = ctk.CTkFrame(chart_container, fg_color="transparent")
        self.dash_chart_left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Right Chart: Monthly Trend
        self.dash_chart_right_frame = ctk.CTkFrame(chart_container, fg_color="transparent")
        self.dash_chart_right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Recent Transactions Section
        recent_frame = ctk.CTkFrame(view, corner_radius=10)
        recent_frame.grid(row=3, column=0, columnspan=4, padx=6, pady=6, sticky="ew")
        
        recent_hdr = ctk.CTkFrame(recent_frame, fg_color="transparent")
        recent_hdr.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(recent_hdr, text="Recent Transactions", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        view_all_btn = ctk.CTkButton(
            recent_hdr,
            text="View All →",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color="#3b82f6",
            hover_color=("gray85", "gray30"),
            width=80,
            height=24,
            command=lambda: self.show_view("expenses")
        )
        view_all_btn.pack(side="right")

        self.recent_list_container = ctk.CTkFrame(recent_frame, fg_color="transparent")
        self.recent_list_container.pack(fill="x", padx=14, pady=(0, 12))

        return view

    def refresh_dashboard(self):
        curr_month = datetime.now().strftime("%Y-%m")
        metrics = self.analytics.get_monthly_metrics(curr_month)
        overall = self.db.get_overall_stats()

        # Update KPI Cards
        self.kpi_cards["month_spend"].configure(text=f"${metrics['total_spent']:,.2f}")
        self.kpi_cards["total_spend"].configure(text=f"${overall['total_spending']:,.2f}")
        self.kpi_cards["daily_avg"].configure(text=f"${metrics['daily_average']:,.2f}")
        
        top_cat_display = metrics["top_category"]
        if len(top_cat_display) > 12:
            top_cat_display = top_cat_display[:10] + ".."
        self.kpi_cards["top_cat"].configure(text=f"{top_cat_display}")

        # Render Left Chart (Category Donut Chart)
        for widget in self.dash_chart_left_frame.winfo_children():
            widget.destroy()

        cat_data = metrics["categories"]
        bg_color = "#1e293b" if self.chart_theme_dark else "#f8fafc"
        text_color = "#f1f5f9" if self.chart_theme_dark else "#0f172a"

        fig_left = Figure(figsize=(4.5, 3.2), dpi=100, facecolor=bg_color)
        ax_left = fig_left.add_subplot(111)
        ax_left.set_facecolor(bg_color)

        if cat_data:
            labels = [c["category"] for c in cat_data[:5]]
            amounts = [c["total_amount"] for c in cat_data[:5]]
            colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]
            
            wedges, texts, autotexts = ax_left.pie(
                amounts,
                labels=labels,
                autopct='%1.0f%%',
                startangle=140,
                colors=colors[:len(labels)],
                textprops=dict(color=text_color, size=8),
                wedgeprops=dict(width=0.4, edgecolor=bg_color)
            )
            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontsize(8)
                autotext.set_weight("bold")
            ax_left.set_title("Spending by Category (This Month)", color=text_color, fontsize=11, fontweight="bold", pad=8)
        else:
            ax_left.text(0.5, 0.5, "No expense data yet.\nClick '+ Add New Expense' to begin!", 
                         horizontalalignment='center', verticalalignment='center', color="gray", fontsize=10)
            ax_left.axis("off")

        fig_left.tight_layout()
        canvas_left = FigureCanvasTkAgg(fig_left, master=self.dash_chart_left_frame)
        canvas_left.draw()
        canvas_left.get_tk_widget().pack(fill="both", expand=True)

        # Render Right Chart (Monthly Comparison Bar Chart)
        for widget in self.dash_chart_right_frame.winfo_children():
            widget.destroy()

        monthly_data = self.db.get_monthly_summary()
        fig_right = Figure(figsize=(4.5, 3.2), dpi=100, facecolor=bg_color)
        ax_right = fig_right.add_subplot(111)
        ax_right.set_facecolor(bg_color)

        if monthly_data:
            months = [m["month"] for m in monthly_data[-6:]]
            totals = [m["total_amount"] for m in monthly_data[-6:]]
            bars = ax_right.bar(months, totals, color="#3b82f6", width=0.5, edgecolor="none")
            
            ax_right.tick_params(colors=text_color, labelsize=8)
            ax_right.spines['top'].set_visible(False)
            ax_right.spines['right'].set_visible(False)
            ax_right.spines['bottom'].set_color("gray")
            ax_right.spines['left'].set_color("gray")
            ax_right.grid(axis='y', linestyle='--', alpha=0.3, color="gray")
            ax_right.set_title("Monthly Spending History", color=text_color, fontsize=11, fontweight="bold", pad=8)
            
            for bar in bars:
                height = bar.get_height()
                ax_right.annotate(f"${height:,.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=7, color=text_color, fontweight='bold')
        else:
            ax_right.text(0.5, 0.5, "No historical data available", 
                          horizontalalignment='center', verticalalignment='center', color="gray", fontsize=10)
            ax_right.axis("off")

        fig_right.tight_layout()
        canvas_right = FigureCanvasTkAgg(fig_right, master=self.dash_chart_right_frame)
        canvas_right.draw()
        canvas_right.get_tk_widget().pack(fill="both", expand=True)

        # Render Recent Transactions
        for widget in self.recent_list_container.winfo_children():
            widget.destroy()

        all_expenses = self.db.get_all_expenses()
        recent_5 = all_expenses[:5]

        if not recent_5:
            ctk.CTkLabel(self.recent_list_container, text="No transactions recorded yet.", text_color="gray").pack(pady=8)
        else:
            for exp in recent_5:
                row_f = ctk.CTkFrame(self.recent_list_container, fg_color=("gray90", "gray18"), height=36)
                row_f.pack(fill="x", pady=2)
                
                # Date & Category badge
                ctk.CTkLabel(row_f, text=exp.date, font=ctk.CTkFont(size=11), text_color="gray60", width=85).pack(side="left", padx=(10, 5))
                badge = ctk.CTkLabel(row_f, text=f" {exp.category} ", font=ctk.CTkFont(size=10, weight="bold"), 
                                     fg_color=("#2563eb", "#1e40af"), text_color="white", corner_radius=6)
                badge.pack(side="left", padx=5)
                
                # Title
                ctk.CTkLabel(row_f, text=exp.title, font=ctk.CTkFont(size=12)).pack(side="left", padx=10)

                # Amount
                ctk.CTkLabel(row_f, text=f"${exp.amount:,.2f}", font=ctk.CTkFont(size=12, weight="bold"), 
                             text_color="#10b981").pack(side="right", padx=15)

    # -------------------------------------------------------------
    # VIEW 2: ADD EXPENSE
    # -------------------------------------------------------------
    def create_add_expense_view(self) -> ctk.CTkFrame:
        view = ctk.CTkFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            view,
            text="Add New Expense",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", pady=(0, 15))

        card = ctk.CTkFrame(view, corner_radius=12)
        card.pack(fill="both", expand=True, padx=4, pady=4)

        form_inner = ctk.CTkFrame(card, fg_color="transparent")
        form_inner.pack(padx=30, pady=25, fill="both", expand=True)

        # Title
        ctk.CTkLabel(form_inner, text="Expense Title / Description *", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.add_title_entry = ctk.CTkEntry(form_inner, placeholder_text="e.g. Weekly Supermarket Groceries", height=38)
        self.add_title_entry.pack(fill="x", pady=(0, 12))

        # Amount & Date (2 columns)
        r1_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        r1_frame.pack(fill="x", pady=(0, 12))
        r1_frame.columnconfigure((0, 1), weight=1)

        # Amount
        ctk.CTkLabel(r1_frame, text="Amount ($) *", font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.add_amount_entry = ctk.CTkEntry(r1_frame, placeholder_text="e.g. 45.50", height=38)
        self.add_amount_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(2, 0))

        # Date with "Today" shortcut
        date_hdr = ctk.CTkFrame(r1_frame, fg_color="transparent")
        date_hdr.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        ctk.CTkLabel(date_hdr, text="Date (YYYY-MM-DD) *", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        today_btn = ctk.CTkButton(date_hdr, text="Today", width=50, height=20, font=ctk.CTkFont(size=10),
                                  fg_color="gray50", hover_color="gray40", command=self.set_add_date_today)
        today_btn.pack(side="right")

        self.add_date_entry = ctk.CTkEntry(r1_frame, placeholder_text="YYYY-MM-DD", height=38)
        self.add_date_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(2, 0))
        self.add_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Category & Payment Method (2 columns)
        r2_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        r2_frame.pack(fill="x", pady=(0, 12))
        r2_frame.columnconfigure((0, 1), weight=1)

        # Category
        cat_hdr = ctk.CTkFrame(r2_frame, fg_color="transparent")
        cat_hdr.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ctk.CTkLabel(cat_hdr, text="Category *", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        new_cat_btn = ctk.CTkButton(cat_hdr, text="+ New", width=50, height=20, font=ctk.CTkFont(size=10),
                                   fg_color="gray50", hover_color="gray40", command=self.prompt_add_category)
        new_cat_btn.pack(side="right")

        self.add_cat_opt = ctk.CTkOptionMenu(r2_frame, values=self.db.get_categories(), height=38)
        self.add_cat_opt.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(2, 0))

        # Payment Method
        ctk.CTkLabel(r2_frame, text="Payment Method", font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.add_pay_opt = ctk.CTkOptionMenu(r2_frame, values=DEFAULT_PAYMENT_METHODS, height=38)
        self.add_pay_opt.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(2, 0))

        # Notes
        ctk.CTkLabel(form_inner, text="Notes / Tags (Optional)", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.add_notes_entry = ctk.CTkEntry(form_inner, placeholder_text="e.g. Receipt #1234, tax deductible", height=38)
        self.add_notes_entry.pack(fill="x", pady=(0, 20))

        # Form Buttons
        action_bar = ctk.CTkFrame(form_inner, fg_color="transparent")
        action_bar.pack(fill="x", pady=(10, 0))

        reset_btn = ctk.CTkButton(
            action_bar,
            text="Reset Form",
            font=ctk.CTkFont(size=13),
            fg_color="gray40",
            hover_color="gray30",
            height=42,
            command=self.reset_add_form
        )
        reset_btn.pack(side="left", padx=(0, 10))

        submit_btn = ctk.CTkButton(
            action_bar,
            text="✔ Save Expense",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=42,
            command=self.submit_new_expense
        )
        submit_btn.pack(side="right", fill="x", expand=True)

        return view

    def set_add_date_today(self):
        self.add_date_entry.delete(0, "end")
        self.add_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def reset_add_form(self):
        self.add_title_entry.delete(0, "end")
        self.add_amount_entry.delete(0, "end")
        self.add_notes_entry.delete(0, "end")
        self.set_add_date_today()
        cats = self.db.get_categories()
        self.add_cat_opt.configure(values=cats)
        if cats:
            self.add_cat_opt.set(cats[0])
        self.add_pay_opt.set("Cash")

    def prompt_add_category(self):
        dialog = ctk.CTkInputDialog(text="Enter new category name:", title="Add Custom Category")
        new_cat = dialog.get_input()
        if new_cat and new_cat.strip():
            added = self.db.add_category(new_cat.strip())
            if added:
                cats = self.db.get_categories()
                self.add_cat_opt.configure(values=cats)
                self.add_cat_opt.set(new_cat.strip())
                messagebox.showinfo("Success", f"Category '{new_cat.strip()}' added!")
            else:
                messagebox.showwarning("Warning", "Category already exists or is invalid.")

    def submit_new_expense(self):
        title = self.add_title_entry.get().strip()
        amount_str = self.add_amount_entry.get().strip()
        category = self.add_cat_opt.get()
        payment_method = self.add_pay_opt.get()
        date_str = self.add_date_entry.get().strip()
        notes = self.add_notes_entry.get().strip()

        valid, error_msg = validate_expense_input(title, amount_str, category, date_str)
        if not valid:
            messagebox.showerror("Validation Error", error_msg, parent=self)
            return

        expense = Expense(
            title=title,
            amount=float(amount_str),
            category=category,
            payment_method=payment_method,
            date=date_str,
            notes=notes
        )

        expense_id = self.db.add_expense(expense)
        if expense_id:
            messagebox.showinfo("Success", f"Expense '{title}' (${expense.amount:.2f}) added successfully!")
            self.reset_add_form()
            self.show_view("dashboard")
        else:
            messagebox.showerror("Error", "Could not save expense to database.", parent=self)

    # -------------------------------------------------------------
    # VIEW 3: ALL EXPENSES & MANAGEMENT
    # -------------------------------------------------------------
    def create_expenses_view(self) -> ctk.CTkFrame:
        view = ctk.CTkFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(2, weight=1)

        # Header bar
        hdr = ctk.CTkFrame(view, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(hdr, text="All Expenses Records", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        
        self.exp_count_lbl = ctk.CTkLabel(hdr, text="0 Records | Total: $0.00", font=ctk.CTkFont(size=12), text_color="gray60")
        self.exp_count_lbl.pack(side="left", padx=20)

        # Action Buttons in Top Bar
        export_csv_btn = ctk.CTkButton(hdr, text="Export CSV", width=100, height=32, command=self.export_all_to_csv)
        export_csv_btn.pack(side="right", padx=(5, 0))

        del_btn = ctk.CTkButton(hdr, text="Delete Selected", width=115, height=32, fg_color="#ef4444", hover_color="#dc2626", command=self.delete_selected_expense)
        del_btn.pack(side="right", padx=(5, 5))

        edit_btn = ctk.CTkButton(hdr, text="Edit Selected", width=105, height=32, fg_color="#2563eb", hover_color="#1d4ed8", command=self.edit_selected_expense)
        edit_btn.pack(side="right", padx=(5, 5))

        # Quick Search Bar
        search_bar = ctk.CTkFrame(view, corner_radius=8)
        search_bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(search_bar, text="Quick Search:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(12, 6), pady=8)
        self.quick_search_entry = ctk.CTkEntry(search_bar, placeholder_text="Search by title, notes...", height=30)
        self.quick_search_entry.pack(side="left", fill="x", expand=True, padx=6, pady=8)
        self.quick_search_entry.bind("<KeyRelease>", lambda e: self.refresh_expenses_table())

        clear_search_btn = ctk.CTkButton(search_bar, text="Clear", width=60, height=30, fg_color="gray50", hover_color="gray40", command=self.clear_quick_search)
        clear_search_btn.pack(side="left", padx=(6, 12), pady=8)

        # Table Frame using ttk.Treeview
        table_container = ctk.CTkFrame(view, corner_radius=8)
        table_container.grid(row=2, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Style Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Expense.Treeview",
            background="#1e293b",
            foreground="#f8fafc",
            fieldbackground="#1e293b",
            rowheight=30,
            font=("Helvetica", 10)
        )
        style.configure(
            "Expense.Treeview.Heading",
            background="#0f172a",
            foreground="#ffffff",
            font=("Helvetica", 10, "bold"),
            relief="flat"
        )
        style.map("Expense.Treeview", background=[("selected", "#2563eb")])

        columns = ("id", "date", "title", "amount", "category", "payment", "notes")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", style="Expense.Treeview", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("title", text="Title / Description")
        self.tree.heading("amount", text="Amount ($)")
        self.tree.heading("category", text="Category")
        self.tree.heading("payment", text="Payment Method")
        self.tree.heading("notes", text="Notes")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("date", width=95, anchor="center")
        self.tree.column("title", width=220, anchor="w")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("category", width=120, anchor="center")
        self.tree.column("payment", width=130, anchor="center")
        self.tree.column("notes", width=200, anchor="w")

        # Scrollbars
        v_scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=2)
        v_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 2), pady=2)

        # Double click to edit
        self.tree.bind("<Double-1>", lambda e: self.edit_selected_expense())

        return view

    def clear_quick_search(self):
        self.quick_search_entry.delete(0, "end")
        self.refresh_expenses_table()

    def refresh_expenses_table(self):
        # Clear items
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_query = self.quick_search_entry.get().strip() if hasattr(self, "quick_search_entry") else ""
        if search_query:
            expenses = self.db.filter_expenses(search_keyword=search_query)
        else:
            expenses = self.db.get_all_expenses()

        total_sum = sum(e.amount for e in expenses)
        self.exp_count_lbl.configure(text=f"{len(expenses)} Records | Total: ${total_sum:,.2f}")

        for exp in expenses:
            self.tree.insert("", "end", iid=str(exp.id), values=(
                exp.id,
                exp.date,
                exp.title,
                f"${exp.amount:,.2f}",
                exp.category,
                exp.payment_method,
                exp.notes
            ))

    def get_selected_expense_id(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Item", "Please select an expense row first.")
            return None
        return int(selected[0])

    def edit_selected_expense(self):
        exp_id = self.get_selected_expense_id()
        if not exp_id:
            return
        expense = self.db.get_expense(exp_id)
        if expense:
            EditExpenseDialog(self, expense, on_save_callback=self.refresh_expenses_table)

    def delete_selected_expense(self):
        exp_id = self.get_selected_expense_id()
        if not exp_id:
            return
        expense = self.db.get_expense(exp_id)
        if not expense:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete:\n\n'{expense.title}' - ${expense.amount:.2f} ({expense.date})?",
            parent=self
        )
        if confirm:
            self.db.delete_expense(exp_id)
            self.refresh_expenses_table()
            messagebox.showinfo("Deleted", "Expense successfully deleted.", parent=self)

    def export_all_to_csv(self):
        expenses = self.db.get_all_expenses()
        if not expenses:
            messagebox.showwarning("Export CSV", "No expenses to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"expenses_export_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if file_path:
            success = Exporter.export_to_csv(expenses, file_path)
            if success:
                messagebox.showinfo("Export Successful", f"Saved {len(expenses)} records to:\n{file_path}")
            else:
                messagebox.showerror("Export Failed", "Could not write to the chosen CSV file.")

    # -------------------------------------------------------------
    # VIEW 4: SEARCH & ADVANCED FILTERS
    # -------------------------------------------------------------
    def create_filter_view(self) -> ctk.CTkFrame:
        view = ctk.CTkFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(2, weight=1)

        # Header
        ctk.CTkLabel(view, text="Search & Filter Expenses", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Filter Controls Panel
        filter_panel = ctk.CTkFrame(view, corner_radius=10)
        filter_panel.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        filter_panel.columnconfigure((0, 1, 2, 3), weight=1)

        # Row 1: Keyword, Category, Payment Method
        ctk.CTkLabel(filter_panel, text="Search Keyword:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))
        self.flt_keyword = ctk.CTkEntry(filter_panel, placeholder_text="Keyword in title or notes", height=32)
        self.flt_keyword.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        ctk.CTkLabel(filter_panel, text="Category:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, sticky="w", padx=10, pady=(10, 2))
        self.flt_category = ctk.CTkOptionMenu(filter_panel, values=["All"] + self.db.get_categories(), height=32)
        self.flt_category.set("All")
        self.flt_category.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 10))

        ctk.CTkLabel(filter_panel, text="Payment Method:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=2, sticky="w", padx=10, pady=(10, 2))
        self.flt_payment = ctk.CTkOptionMenu(filter_panel, values=["All"] + DEFAULT_PAYMENT_METHODS, height=32)
        self.flt_payment.set("All")
        self.flt_payment.grid(row=1, column=2, sticky="ew", padx=10, pady=(0, 10))

        # Action Buttons in Row 1 Col 3
        btn_box = ctk.CTkFrame(filter_panel, fg_color="transparent")
        btn_box.grid(row=1, column=3, sticky="ew", padx=10, pady=(0, 10))
        btn_box.columnconfigure((0, 1), weight=1)

        apply_btn = ctk.CTkButton(btn_box, text="Apply Filter", fg_color="#2563eb", hover_color="#1d4ed8", height=32, command=self.apply_filters)
        apply_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        reset_flt_btn = ctk.CTkButton(btn_box, text="Reset", fg_color="gray50", hover_color="gray40", height=32, command=self.reset_filters)
        reset_flt_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # Row 2: Date Range and Amount Range
        ctk.CTkLabel(filter_panel, text="Start Date (YYYY-MM-DD):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=0, sticky="w", padx=10, pady=(2, 2))
        self.flt_start_date = ctk.CTkEntry(filter_panel, placeholder_text="e.g. 2026-01-01", height=32)
        self.flt_start_date.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 12))

        ctk.CTkLabel(filter_panel, text="End Date (YYYY-MM-DD):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=1, sticky="w", padx=10, pady=(2, 2))
        self.flt_end_date = ctk.CTkEntry(filter_panel, placeholder_text="e.g. 2026-12-31", height=32)
        self.flt_end_date.grid(row=3, column=1, sticky="ew", padx=10, pady=(0, 12))

        ctk.CTkLabel(filter_panel, text="Min Amount ($):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=2, sticky="w", padx=10, pady=(2, 2))
        self.flt_min_amt = ctk.CTkEntry(filter_panel, placeholder_text="Min $", height=32)
        self.flt_min_amt.grid(row=3, column=2, sticky="ew", padx=10, pady=(0, 12))

        ctk.CTkLabel(filter_panel, text="Max Amount ($):", font=ctk.CTkFont(size=11, weight="bold")).grid(row=2, column=3, sticky="w", padx=10, pady=(2, 2))
        self.flt_max_amt = ctk.CTkEntry(filter_panel, placeholder_text="Max $", height=32)
        self.flt_max_amt.grid(row=3, column=3, sticky="ew", padx=10, pady=(0, 12))

        # Results Table & Export
        results_container = ctk.CTkFrame(view, corner_radius=10)
        results_container.grid(row=2, column=0, sticky="nsew")
        results_container.grid_rowconfigure(1, weight=1)
        results_container.grid_columnconfigure(0, weight=1)

        # Summary Bar above results
        res_hdr = ctk.CTkFrame(results_container, fg_color="transparent")
        res_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        
        self.filter_status_lbl = ctk.CTkLabel(res_hdr, text="Matching Results: 0 | Total Sum: $0.00", font=ctk.CTkFont(size=13, weight="bold"))
        self.filter_status_lbl.pack(side="left")

        export_filtered_btn = ctk.CTkButton(
            res_hdr,
            text="Export Filtered CSV",
            height=28,
            fg_color="#10b981",
            hover_color="#059669",
            command=self.export_filtered_to_csv
        )
        export_filtered_btn.pack(side="right")

        # Treeview
        columns = ("id", "date", "title", "amount", "category", "payment", "notes")
        self.flt_tree = ttk.Treeview(results_container, columns=columns, show="headings", style="Expense.Treeview", selectmode="browse")

        self.flt_tree.heading("id", text="ID")
        self.flt_tree.heading("date", text="Date")
        self.flt_tree.heading("title", text="Title / Description")
        self.flt_tree.heading("amount", text="Amount ($)")
        self.flt_tree.heading("category", text="Category")
        self.flt_tree.heading("payment", text="Payment Method")
        self.flt_tree.heading("notes", text="Notes")

        self.flt_tree.column("id", width=50, anchor="center")
        self.flt_tree.column("date", width=95, anchor="center")
        self.flt_tree.column("title", width=220, anchor="w")
        self.flt_tree.column("amount", width=100, anchor="e")
        self.flt_tree.column("category", width=120, anchor="center")
        self.flt_tree.column("payment", width=130, anchor="center")
        self.flt_tree.column("notes", width=200, anchor="w")

        flt_v_scroll = ttk.Scrollbar(results_container, orient="vertical", command=self.flt_tree.yview)
        self.flt_tree.configure(yscrollcommand=flt_v_scroll.set)

        self.flt_tree.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(0, 10))
        flt_v_scroll.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=(0, 10))

        self.current_filtered_expenses = []
        return view

    def reset_filters(self):
        self.flt_keyword.delete(0, "end")
        self.flt_start_date.delete(0, "end")
        self.flt_end_date.delete(0, "end")
        self.flt_min_amt.delete(0, "end")
        self.flt_max_amt.delete(0, "end")
        self.flt_category.set("All")
        self.flt_payment.set("All")
        self.apply_filters()

    def apply_filters(self):
        keyword = self.flt_keyword.get().strip() or None
        category = self.flt_category.get()
        payment = self.flt_payment.get()
        start_d = self.flt_start_date.get().strip() or None
        end_d = self.flt_end_date.get().strip() or None

        min_amt = None
        max_amt = None
        try:
            if self.flt_min_amt.get().strip():
                min_amt = float(self.flt_min_amt.get().strip())
            if self.flt_max_amt.get().strip():
                max_amt = float(self.flt_max_amt.get().strip())
        except ValueError:
            messagebox.showwarning("Filter Warning", "Please enter valid numeric values for min/max amounts.")
            return

        self.current_filtered_expenses = self.db.filter_expenses(
            category=category,
            start_date=start_d,
            end_date=end_d,
            min_amount=min_amt,
            max_amount=max_amt,
            search_keyword=keyword,
            payment_method=payment
        )

        for item in self.flt_tree.get_children():
            self.flt_tree.delete(item)

        total_sum = sum(e.amount for e in self.current_filtered_expenses)
        self.filter_status_lbl.configure(text=f"Matching Results: {len(self.current_filtered_expenses)} | Total Sum: ${total_sum:,.2f}")

        for exp in self.current_filtered_expenses:
            self.flt_tree.insert("", "end", iid=str(exp.id), values=(
                exp.id,
                exp.date,
                exp.title,
                f"${exp.amount:,.2f}",
                exp.category,
                exp.payment_method,
                exp.notes
            ))

    def export_filtered_to_csv(self):
        if not self.current_filtered_expenses:
            messagebox.showwarning("Export CSV", "No filtered records to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"filtered_expenses_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if file_path:
            success = Exporter.export_to_csv(self.current_filtered_expenses, file_path)
            if success:
                messagebox.showinfo("Export Successful", f"Saved {len(self.current_filtered_expenses)} records to:\n{file_path}")
            else:
                messagebox.showerror("Export Failed", "Could not write to the chosen CSV file.")

    # -------------------------------------------------------------
    # VIEW 5: REPORTS & ANALYTICS
    # -------------------------------------------------------------
    def create_reports_view(self) -> ctk.CTkFrame:
        view = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)

        # Header Bar with Month Picker & Export Buttons
        top_bar = ctk.CTkFrame(view, corner_radius=10)
        top_bar.pack(fill="x", pady=(0, 15))

        top_inner = ctk.CTkFrame(top_bar, fg_color="transparent")
        top_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(top_inner, text="Monthly Report Generator", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")

        # Export Buttons
        export_pdf_btn = ctk.CTkButton(
            top_inner,
            text="📄 Export PDF Report",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            height=32,
            command=self.export_report_pdf
        )
        export_pdf_btn.pack(side="right", padx=(8, 0))

        export_txt_btn = ctk.CTkButton(
            top_inner,
            text="📝 Export Text Summary",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="gray40",
            hover_color="gray30",
            height=32,
            command=self.export_report_text
        )
        export_txt_btn.pack(side="right", padx=(8, 0))

        # Month Selector
        self.report_month_opt = ctk.CTkOptionMenu(
            top_inner,
            values=[datetime.now().strftime("%Y-%m")],
            command=lambda m: self.refresh_reports_view(),
            height=32
        )
        self.report_month_opt.pack(side="right", padx=(10, 0))
        ctk.CTkLabel(top_inner, text="Select Month:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="right")

        # Budget Progress / Alert Card
        self.budget_card = ctk.CTkFrame(view, corner_radius=10)
        self.budget_card.pack(fill="x", pady=(0, 15))
        
        self.budget_inner = ctk.CTkFrame(self.budget_card, fg_color="transparent")
        self.budget_inner.pack(fill="x", padx=16, pady=12)

        # Overview Stats Grid
        self.report_stats_frame = ctk.CTkFrame(view, fg_color="transparent")
        self.report_stats_frame.pack(fill="x", pady=(0, 15))
        self.report_stats_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self.rep_kpi_labels = {}
        r_kpis = [
            ("total", "Total Month Spend", "$0.00", "#3b82f6"),
            ("txs", "Total Transactions", "0", "#10b981"),
            ("daily_avg", "Daily Average", "$0.00", "#f59e0b"),
            ("peak_day", "Highest Spend Day", "N/A", "#ec4899")
        ]
        for col, (k, title, val, color) in enumerate(r_kpis):
            c = ctk.CTkFrame(self.report_stats_frame, corner_radius=10)
            c.grid(row=0, column=col, padx=4, sticky="ew")
            ctk.CTkLabel(c, text=title, font=ctk.CTkFont(size=11), text_color="gray60").pack(anchor="w", padx=12, pady=(10, 2))
            lbl = ctk.CTkLabel(c, text=val, font=ctk.CTkFont(size=18, weight="bold"), text_color=color)
            lbl.pack(anchor="w", padx=12, pady=(0, 10))
            self.rep_kpi_labels[k] = lbl

        # Chart Visualizer Section with interactive switcher
        chart_section = ctk.CTkFrame(view, corner_radius=10)
        chart_section.pack(fill="x", pady=(0, 15))

        chart_hdr = ctk.CTkFrame(chart_section, fg_color="transparent")
        chart_hdr.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(chart_hdr, text="Data Visualizations", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        
        self.chart_type_segmented = ctk.CTkSegmentedButton(
            chart_hdr,
            values=["Category Pie", "Monthly Comparison", "Daily Spend Trend"],
            command=lambda v: self.render_report_chart(v)
        )
        self.chart_type_segmented.set("Category Pie")
        self.chart_type_segmented.pack(side="right")

        self.rep_chart_container = ctk.CTkFrame(chart_section, fg_color="transparent")
        self.rep_chart_container.pack(fill="x", padx=16, pady=(0, 16))

        # Text Summary Box
        summary_box = ctk.CTkFrame(view, corner_radius=10)
        summary_box.pack(fill="x", pady=(0, 15))

        sum_hdr = ctk.CTkFrame(summary_box, fg_color="transparent")
        sum_hdr.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(sum_hdr, text="Formatted Executive Summary", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        self.summary_textbox = ctk.CTkTextbox(summary_box, height=220, font=("Consolas", 11))
        self.summary_textbox.pack(fill="x", padx=16, pady=(0, 16))

        return view

    def refresh_reports_view(self):
        # Update Month list in dropdown
        monthly_summary = self.db.get_monthly_summary()
        months = [m["month"] for m in monthly_summary] if monthly_summary else [datetime.now().strftime("%Y-%m")]
        curr_m = datetime.now().strftime("%Y-%m")
        if curr_m not in months:
            months.append(curr_m)
        months.sort(reverse=True)
        self.report_month_opt.configure(values=months)

        selected_month = self.report_month_opt.get()
        if selected_month not in months:
            selected_month = months[0]
            self.report_month_opt.set(selected_month)

        metrics = self.analytics.get_monthly_metrics(selected_month)

        # Update KPIs
        self.rep_kpi_labels["total"].configure(text=f"${metrics['total_spent']:,.2f}")
        self.rep_kpi_labels["txs"].configure(text=str(metrics["total_count"]))
        self.rep_kpi_labels["daily_avg"].configure(text=f"${metrics['daily_average']:,.2f}")
        self.rep_kpi_labels["peak_day"].configure(text=f"{metrics['highest_day']} (${metrics['highest_day_amount']:,.2f})")

        # Update Budget Banner
        for widget in self.budget_inner.winfo_children():
            widget.destroy()

        if metrics["budget"] is not None and metrics["budget"] > 0:
            budget_val = metrics["budget"]
            spent = metrics["total_spent"]
            remaining = metrics["budget_remaining"]
            pct = metrics["budget_percent_used"]

            is_over = remaining < 0
            badge_color = "#ef4444" if is_over else "#10b981"
            status_text = f"OVER BUDGET by ${abs(remaining):,.2f}!" if is_over else f"${remaining:,.2f} remaining within limit"

            b_hdr = ctk.CTkFrame(self.budget_inner, fg_color="transparent")
            b_hdr.pack(fill="x")
            ctk.CTkLabel(b_hdr, text=f"Monthly Budget: ${budget_val:,.2f}", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
            ctk.CTkLabel(b_hdr, text=f"Status: {status_text} ({pct:.1f}% used)", font=ctk.CTkFont(size=12, weight="bold"), text_color=badge_color).pack(side="right")

            # Progress bar
            prog_val = min(1.0, spent / budget_val) if budget_val > 0 else 1.0
            prog_color = "#ef4444" if is_over else ("#f59e0b" if prog_val > 0.8 else "#3b82f6")
            prog_bar = ctk.CTkProgressBar(self.budget_inner, progress_color=prog_color)
            prog_bar.set(prog_val)
            prog_bar.pack(fill="x", pady=(6, 2))
        else:
            ctk.CTkLabel(self.budget_inner, text="No budget configured for this month. Set one in Settings & Tools!", text_color="gray60").pack(anchor="w")

        # Render Chart
        self.render_report_chart(self.chart_type_segmented.get())

        # Update Text Summary
        text_rep = self.analytics.generate_text_summary(selected_month)
        self.summary_textbox.delete("1.0", "end")
        self.summary_textbox.insert("1.0", text_rep)

    def render_report_chart(self, chart_type: str):
        for widget in self.rep_chart_container.winfo_children():
            widget.destroy()

        selected_month = self.report_month_opt.get()
        metrics = self.analytics.get_monthly_metrics(selected_month)
        bg_color = "#1e293b" if self.chart_theme_dark else "#f8fafc"
        text_color = "#f1f5f9" if self.chart_theme_dark else "#0f172a"

        fig = Figure(figsize=(9, 3.8), dpi=100, facecolor=bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(bg_color)

        if chart_type == "Category Pie":
            cats = metrics["categories"]
            if cats:
                labels = [c["category"] for c in cats]
                amounts = [c["total_amount"] for c in cats]
                colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16", "#eab308"]
                
                wedges, texts, autotexts = ax.pie(
                    amounts,
                    labels=labels,
                    autopct='%1.1f%%',
                    startangle=140,
                    colors=colors[:len(labels)],
                    textprops=dict(color=text_color, size=9),
                    wedgeprops=dict(edgecolor=bg_color, linewidth=1.5)
                )
                for autotext in autotexts:
                    autotext.set_color("white")
                    autotext.set_fontsize(8)
                    autotext.set_weight("bold")
                ax.set_title(f"Expense Breakdown by Category ({selected_month})", color=text_color, fontsize=12, fontweight="bold", pad=10)
            else:
                ax.text(0.5, 0.5, f"No expenses found for {selected_month}", horizontalalignment='center', verticalalignment='center', color="gray", fontsize=11)
                ax.axis("off")

        elif chart_type == "Monthly Comparison":
            monthly_data = self.db.get_monthly_summary()
            if monthly_data:
                months = [m["month"] for m in monthly_data]
                totals = [m["total_amount"] for m in monthly_data]
                bars = ax.bar(months, totals, color="#2563eb", width=0.45)
                
                ax.tick_params(colors=text_color, labelsize=9)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_color("gray")
                ax.spines['left'].set_color("gray")
                ax.grid(axis='y', linestyle='--', alpha=0.3, color="gray")
                ax.set_title("Monthly Total Expenses Comparison", color=text_color, fontsize=12, fontweight="bold", pad=10)
                
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f"${height:,.0f}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, color=text_color, fontweight='bold')
            else:
                ax.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center', color="gray", fontsize=11)
                ax.axis("off")

        elif chart_type == "Daily Spend Trend":
            daily_data = self.db.get_daily_trend(month=selected_month)
            if daily_data:
                dates = [d["date"][-5:] for d in daily_data] # MM-DD
                totals = [d["daily_total"] for d in daily_data]
                
                ax.plot(dates, totals, marker='o', color="#10b981", linewidth=2.5, markersize=5)
                ax.fill_between(dates, totals, color="#10b981", alpha=0.15)
                
                ax.tick_params(colors=text_color, labelsize=8, rotation=35)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_color("gray")
                ax.spines['left'].set_color("gray")
                ax.grid(axis='both', linestyle='--', alpha=0.25, color="gray")
                ax.set_title(f"Daily Spending Timeline ({selected_month})", color=text_color, fontsize=12, fontweight="bold", pad=10)
            else:
                ax.text(0.5, 0.5, f"No daily entries for {selected_month}", horizontalalignment='center', verticalalignment='center', color="gray", fontsize=11)
                ax.axis("off")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.rep_chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def export_report_pdf(self):
        month = self.report_month_opt.get()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")],
            initialfile=f"expense_report_{month}.pdf"
        )
        if file_path:
            success = Exporter.export_summary_to_pdf(self.db, file_path, month)
            if success:
                messagebox.showinfo("PDF Generated", f"Executive PDF report saved to:\n{file_path}")
            else:
                messagebox.showerror("Error", "Could not generate PDF report.")

    def export_report_text(self):
        month = self.report_month_opt.get()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=f"expense_summary_{month}.txt"
        )
        if file_path:
            success = Exporter.export_summary_to_text(self.db, file_path, month)
            if success:
                messagebox.showinfo("Text Report Saved", f"Summary report saved to:\n{file_path}")
            else:
                messagebox.showerror("Error", "Could not save text summary report.")

    # -------------------------------------------------------------
    # VIEW 6: SETTINGS & TOOLS
    # -------------------------------------------------------------
    def create_settings_view(self) -> ctk.CTkFrame:
        view = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)

        # Header
        ctk.CTkLabel(view, text="Settings & Data Management", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", pady=(0, 15))

        # 1. Monthly Budget Configuration Card
        budget_card = ctk.CTkFrame(view, corner_radius=10)
        budget_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(budget_card, text="🎯 Set Monthly Spending Budget", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(budget_card, text="Define a monthly budget target to track spending alerts and thresholds.", font=ctk.CTkFont(size=11), text_color="gray60").pack(anchor="w", padx=16, pady=(0, 10))

        b_row = ctk.CTkFrame(budget_card, fg_color="transparent")
        b_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(b_row, text="Target Month (YYYY-MM):", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 8))
        self.set_budget_month_entry = ctk.CTkEntry(b_row, width=120, height=32)
        self.set_budget_month_entry.insert(0, datetime.now().strftime("%Y-%m"))
        self.set_budget_month_entry.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(b_row, text="Budget Limit ($):", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 8))
        self.set_budget_limit_entry = ctk.CTkEntry(b_row, placeholder_text="e.g. 1000", width=120, height=32)
        self.set_budget_limit_entry.pack(side="left", padx=(0, 15))

        save_budget_btn = ctk.CTkButton(b_row, text="Save Budget", fg_color="#2563eb", hover_color="#1d4ed8", height=32, command=self.save_budget_setting)
        save_budget_btn.pack(side="left")

        # 2. Category Management Card
        cat_card = ctk.CTkFrame(view, corner_radius=10)
        cat_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(cat_card, text="🏷️ Custom Expense Categories", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(cat_card, text="Add custom categories tailored to your personal or business tracking needs.", font=ctk.CTkFont(size=11), text_color="gray60").pack(anchor="w", padx=16, pady=(0, 10))

        cat_row = ctk.CTkFrame(cat_card, fg_color="transparent")
        cat_row.pack(fill="x", padx=16, pady=(0, 14))

        self.new_cat_entry = ctk.CTkEntry(cat_row, placeholder_text="e.g. Subscriptions, Freelance, Insurance", width=260, height=32)
        self.new_cat_entry.pack(side="left", padx=(0, 12))

        add_cat_btn = ctk.CTkButton(cat_row, text="+ Add Category", fg_color="#10b981", hover_color="#059669", height=32, command=self.add_custom_category)
        add_cat_btn.pack(side="left")

        # 3. Data Tools Card (Sample Data & Reset)
        data_card = ctk.CTkFrame(view, corner_radius=10)
        data_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(data_card, text="🛠️ Database & Demonstration Tools", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(data_card, text="Populate realistic demo records or reset the database.", font=ctk.CTkFont(size=11), text_color="gray60").pack(anchor="w", padx=16, pady=(0, 10))

        tools_row = ctk.CTkFrame(data_card, fg_color="transparent")
        tools_row.pack(fill="x", padx=16, pady=(0, 14))

        seed_btn = ctk.CTkButton(
            tools_row,
            text="🌱 Load Realistic Sample Data",
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            height=34,
            command=self.seed_demo_data
        )
        seed_btn.pack(side="left", padx=(0, 12))

        clear_btn = ctk.CTkButton(
            tools_row,
            text="🗑️ Clear All Expenses",
            fg_color="#ef4444",
            hover_color="#dc2626",
            height=34,
            command=self.clear_database_data
        )
        clear_btn.pack(side="left")

        # 4. About & System Info
        about_card = ctk.CTkFrame(view, corner_radius=10)
        about_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(about_card, text="ℹ️ System & Project Information", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        info_text = (
            "• Project: Expense Tracker & Report Generator (Desktop GUI)\n"
            "• Architecture: SQLite3 Database + CustomTkinter UI + Matplotlib Canvas + FPDF2 Exporter\n"
            "• Storage: Persistent local SQLite database (expenses.db)\n"
            "• Status: Fully operational & responsive"
        )
        ctk.CTkLabel(about_card, text=info_text, justify="left", font=ctk.CTkFont(size=11), text_color="gray70").pack(anchor="w", padx=16, pady=(0, 14))

        return view

    def save_budget_setting(self):
        month = self.set_budget_month_entry.get().strip()
        limit_str = self.set_budget_limit_entry.get().strip()

        if not month or len(month) != 7 or "-" not in month:
            messagebox.showwarning("Invalid Month", "Please provide month in YYYY-MM format (e.g. 2026-09).")
            return

        try:
            limit = float(limit_str)
            if limit <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Invalid Budget", "Please enter a valid positive numeric budget limit.")
            return

        self.db.set_budget(month, limit)
        messagebox.showinfo("Budget Saved", f"Monthly budget of ${limit:,.2f} set for {month}!")
        self.set_budget_limit_entry.delete(0, "end")

    def add_custom_category(self):
        cat_name = self.new_cat_entry.get().strip()
        if not cat_name:
            messagebox.showwarning("Empty Name", "Please type a category name.")
            return

        if self.db.add_category(cat_name):
            messagebox.showinfo("Category Added", f"Category '{cat_name}' has been created successfully.")
            self.new_cat_entry.delete(0, "end")
        else:
            messagebox.showwarning("Exists", "Category already exists or is invalid.")

    def seed_demo_data(self):
        confirm = messagebox.askyesno(
            "Load Demo Data",
            "This will add realistic sample expense records across multiple categories and dates.\nProceed?",
            parent=self
        )
        if confirm:
            self.db.seed_sample_data()
            messagebox.showinfo("Demo Data Loaded", "Sample expense records have been populated successfully!", parent=self)
            self.show_view("dashboard")

    def clear_database_data(self):
        confirm = messagebox.askyesno(
            "Confirm Database Reset",
            "⚠️ WARNING: This will permanently delete ALL recorded expenses from the database!\nAre you sure?",
            parent=self
        )
        if confirm:
            self.db.clear_all_expenses()
            messagebox.showinfo("Database Cleared", "All expense records have been removed.", parent=self)
            self.show_view("dashboard")
