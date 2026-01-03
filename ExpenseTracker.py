import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
from datetime import datetime, date
import csv
import matplotlib.pyplot as plt

# Database connection setup and initialization
def initialize_database():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root"
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ExpenseTracker")
        cursor.execute("USE ExpenseTracker")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(255),
                amount FLOAT,
                date DATE
            )
        """)
        conn.commit()
        return conn, cursor
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
        exit()

# Insert expense into the database
def add_expense(category, amount, expense_date):
    if not category or not amount or not expense_date:
        messagebox.showerror("Input Error", "All fields are required.")
        return
    try:
        datetime.strptime(expense_date, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Input Error", "Invalid date format. Use YYYY-MM-DD.")
        return
    try:
        cursor.execute(
            "INSERT INTO expenses (category, amount, date) VALUES (%s, %s, %s)",
            (category, amount, expense_date)
        )
        conn.commit()
        messagebox.showinfo("Success", "Expense added successfully!")
        clear_form()
        load_expenses()
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Failed to add expense: {err}")

# Load expenses
def load_expenses(filter_start=None, filter_end=None, min_amount=None, max_amount=None):
    for row in tree.get_children():
        tree.delete(row)

    query = "SELECT * FROM expenses"
    params = []

    if filter_start and filter_end:
        query += " WHERE date BETWEEN %s AND %s"
        params = [filter_start, filter_end]
    elif min_amount is not None and max_amount is not None:
        query += " WHERE amount BETWEEN %s AND %s"
        params = [min_amount, max_amount]

    cursor.execute(query, params)
    expenses = cursor.fetchall()

    for expense in expenses:
        tree.insert("", tk.END, values=expense)

    calculate_total_expense(expenses)

def calculate_total_expense(expenses):
    total = sum(expense[2] for expense in expenses)
    total_label_var.set(f"Total Expense: ₹{total:.2f}")

# Clear input fields
def clear_form():
    category_var.set("")
    amount_var.set("")
    date_var.set(date.today().strftime("%Y-%m-%d"))

# Filter by amount
def filter_by_amount():
    try:
        min_amount = float(min_amount_var.get())
        max_amount = float(max_amount_var.get())
        load_expenses(min_amount=min_amount, max_amount=max_amount)
    except ValueError:
        messagebox.showerror("Input Error", "Enter valid numbers for amount range.")

# Export to CSV
def export_to_csv():
    try:
        cursor.execute("SELECT * FROM expenses")
        rows = cursor.fetchall()
        if not rows:
            messagebox.showinfo("Info", "No expenses to export.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if file_path:
            with open(file_path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Category", "Amount", "Date"])
                writer.writerows(rows)
            messagebox.showinfo("Success", f"Data exported successfully to {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export data: {e}")

# Show analysis
def show_analysis():
    try:
        cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
        data = cursor.fetchall()
        if not data:
            messagebox.showinfo("Info", "No data available for analysis.")
            return
        categories = [row[0] for row in data]
        amounts = [row[1] for row in data]
        plt.bar(categories, amounts, color="orange")
        plt.xlabel("Categories")
        plt.ylabel("Total Expense")
        plt.title("Expense Analysis")
        plt.show()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to show analysis: {e}")

# Delete expense
def delete_expense():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Selection Error", "No expense selected.")
        return
    expense_id = tree.item(selected_item, "values")[0]
    try:
        cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        conn.commit()
        messagebox.showinfo("Success", "Expense deleted successfully!")
        load_expenses()
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Failed to delete expense: {err}")

# Reset filters
def reset_filters(event=None):
    min_amount_var.set("")
    max_amount_var.set("")
    load_expenses()

# GUI setup
def setup_gui():
    global root, tree, category_var, amount_var, date_var
    global min_amount_var, max_amount_var, total_label_var

    root = tk.Tk()
    root.title("Expense Tracker")
    root.geometry("1200x800")
    root.config(bg="teal")

    frame_form = tk.Frame(root, bg="#FDFD96", bd=3, relief="solid")
    frame_form.pack(pady=20, padx=20, fill=tk.X)

    category_var = tk.StringVar()
    amount_var = tk.DoubleVar()
    date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))

    tk.Label(frame_form, text="Category", bg="#FDFD96").grid(row=0, column=0, padx=10)
    tk.Entry(frame_form, textvariable=category_var).grid(row=0, column=1)

    tk.Label(frame_form, text="Amount (₹)", bg="#FDFD96").grid(row=0, column=2, padx=10)
    tk.Entry(frame_form, textvariable=amount_var).grid(row=0, column=3)

    tk.Label(frame_form, text="Date (YYYY-MM-DD)", bg="#FDFD96").grid(row=0, column=4, padx=10)
    tk.Entry(frame_form, textvariable=date_var).grid(row=0, column=5)

    tk.Button(frame_form, text="Add Expense",
              command=lambda: add_expense(
                  category_var.get(),
                  amount_var.get(),
                  date_var.get()
              )).grid(row=0, column=6, padx=10)

    tk.Button(frame_form, text="Clear Form", command=clear_form).grid(row=0, column=7)

    frame_table = tk.Frame(root, bg="#FFFFFF", bd=3, relief="solid")
    frame_table.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

    tree = ttk.Treeview(frame_table, columns=("ID", "Category", "Amount", "Date"), show="headings")
    for col in ("ID", "Category", "Amount", "Date"):
        tree.heading(col, text=col)
    tree.pack(fill=tk.BOTH, expand=True)

    frame_filters = tk.Frame(root, bg="#4C9A2A", bd=3, relief="solid")
    frame_filters.pack(pady=20, padx=20, fill=tk.X)

    min_amount_var = tk.StringVar()
    max_amount_var = tk.StringVar()

    tk.Label(frame_filters, text="Min Amount", bg="#4C9A2A").grid(row=0, column=0)
    tk.Entry(frame_filters, textvariable=min_amount_var).grid(row=0, column=1)

    tk.Label(frame_filters, text="Max Amount", bg="#4C9A2A").grid(row=0, column=2)
    tk.Entry(frame_filters, textvariable=max_amount_var).grid(row=0, column=3)

    tk.Button(frame_filters, text="Filter by Amount", command=filter_by_amount).grid(row=0, column=4)
    tk.Button(frame_filters, text="Export to CSV", command=export_to_csv).grid(row=0, column=5)
    tk.Button(frame_filters, text="Analyze Expenses", command=show_analysis).grid(row=0, column=6)

    tk.Button(root, text="Delete Expense", command=delete_expense).pack(pady=10)

    total_label_var = tk.StringVar(value="Total Expense: ₹0.00")
    tk.Label(root, textvariable=total_label_var, bg="teal", font=("Arial", 16)).pack(pady=10)

    root.bind("<F12>", reset_filters)

    load_expenses()
    root.mainloop()

conn, cursor = initialize_database()
setup_gui()
conn.close()