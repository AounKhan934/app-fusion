# Expense Tracker & Financial Report Generator

A feature-rich, modern Desktop Application built in Python for recording daily expenses, analyzing financial spending habits, and generating professional reports with interactive data visualizations.

---

## 🌟 Key Features

### 1. 💼 Expense Management (CRUD)
- **Add Expenses**: Intuitive form with input validation (Title, Amount, Category, Date, Payment Method, and Notes/Tags).
- **Edit Expenses**: Double-click or select any expense to open an interactive modal dialog to update details.
- **Delete Expenses**: Safely remove unwanted records with a confirmation prompt.
- **Predefined & Custom Categories**: Food, Travel, Bills, Shopping, Groceries, Entertainment, Health, Education, Other — with support for adding your own custom categories on the fly!
- **Payment Method Tracking**: Cash, Credit Card, Debit Card, UPI / Online, Bank Transfer.

### 2. 📊 Real-Time Financial Dashboard
- **Live KPI Metric Cards**: Current Month Spending, All-Time Total, Daily Average, and Top Spending Category.
- **Interactive Matplotlib Visualizations**:
  - **Category Spending Donut Chart** (visualizes current month proportions).
  - **Monthly Spending History Bar Chart** (tracks multi-month trends).
- **Recent Transactions Feed**: Fast preview of the latest 5 expenses.

### 3. 🔍 Search & Multi-Criteria Filtering
- Search expenses by keyword in titles or notes.
- Filter dynamically by **Category**, **Payment Method**, **Date Range (Start/End)**, and **Amount Range (Min/Max)**.
- Real-time matched records count and total sum calculation.
- Instant **CSV Export** of filtered query results.

### 4. 📈 Reports & Analytics Engine
- **Monthly Breakdown**: Deep-dive into monthly totals, transaction count, daily average, and peak spending dates.
- **Monthly Budget Tracker**: Set monthly spending targets with color-coded progress bars and real-time over-budget warnings.
- **Interactive Chart Switcher**:
  - Category Pie Chart
  - Monthly Trend Bar Chart
  - Daily Spending Timeline Graph
- **Executive Summary Generation**: Formatted summary text ready to review.
- **Export Options**:
  - 📄 **Export to PDF Report** (`.pdf`)
  - 📝 **Export to Text Summary** (`.txt`)
  - 📊 **Export Full / Filtered Expenses to CSV** (`.csv`)

### 5. 🎨 Modern & Responsive Desktop GUI
- Built using **CustomTkinter** for high-DPI scaling, smooth rounded components, and responsive layout.
- Seamless **Dark & Light Mode** toggle (auto-adapts embedded Matplotlib chart themes).
- Offline & persistent storage with **SQLite (`expenses.db`)**.

---

## 📂 Project Structure

```
Task 2/
├── main.py              # Application entry point
├── gui.py               # CustomTkinter GUI layout, views, and embedded Matplotlib canvas
├── database.py          # SQLite database schema, CRUD operations & analytical queries
├── models.py            # Expense data models and validation logic
├── analytics.py         # Summary metrics calculations & formatted reports
├── exporter.py          # CSV and PDF export handlers
├── test_core.py         # Automated unit test suite
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## 🚀 How to Run the Application

### 1. Install Requirements
Make sure you have Python 3.8+ installed. Install the required packages via pip:

```bash
pip install -r requirements.txt
```

### 2. Launch the Desktop Application
Run the `main.py` script:

```bash
python main.py
```

---

## 🧪 Running Automated Tests

To run the unit tests and verify database operations, analytics calculations, and CSV/PDF export generation:

```bash
python -m unittest test_core.py
```
