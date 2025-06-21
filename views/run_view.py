import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from util.calibration.calibration_session import CalibrationSession
from util.uart_util import UARTUtil
import matplotlib
matplotlib.use('TkAgg')
import re
from collections import defaultdict

class RunView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.canvas = None
        self.ser = UARTUtil.open_port()

        label = tk.Label(self, text="Calibration", font=("Arial", 18))
        label.pack(side='top', anchor='n', pady=10)

        button = tk.Button(self, text="Home", command=lambda: controller.show_frame("MenuView"),
                           font=("Arial", 12), width=10, height=2)
        button.pack(side='top', anchor='e')

        info_text = (
            "Enter calibration values (0-100) in the table below.\n"
            "Double-click a cell to edit. Select a row and press Delete to remove it."
        )
        info_label = tk.Label(self, text=info_text, justify="left", fg="black", font=("Arial", 12))
        info_label.pack(pady=(0, 10))

        # Treeview for calibration data
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill='both', expand=True)

        self.tree = ttk.Treeview(left_frame, columns=("Index", "OD", "Selected"), show="headings")
        self.tree.heading("Index", text="Index")
        self.tree.heading("OD", text="OD")
        self.tree.heading("Selected", text="Selected")
        self.tree.column("Index", width=50, anchor="center")
        self.tree.column("OD", width=100, anchor="center")
        self.tree.column("Selected", width=80, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Insert 50 rows with index
        for i in range(50):
            self.tree.insert("", "end", values=(i + 1, "", "[ ]"))

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-1>", self.on_click)

        button_frame = tk.Frame(self)
        button_frame.pack(side='top', anchor='e', pady=10)

    def on_return_key(self, event):
        item = self.tree.focus()
        if not item:
            return
        col = self.tree.identify_column(event.x) if hasattr(event, 'x') else "#2"
        if col == "#1":
            return
        x, y, width, height = self.tree.bbox(item, col)
        entry = tk.Entry(self.tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus()

        def on_focus_out(event):
            new_val = entry.get()
            if not self.is_valid_od(new_val):
                messagebox.showerror("Invalid Input", "Please enter a number between 0.0 and 100.0")
                new_val = ""
            self.tree.set(item, column=col, value=new_val)
            entry.destroy()

        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Return>", lambda e: on_focus_out(e))

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if column in ("#1", "#3") or not item:
            return  # Don't allow editing of Index or Selected columns

        self.edit_cell(item, column)

    def edit_cell(self, item, column):
        x, y, width, height = self.tree.bbox(item, column)
        entry = tk.Entry(self.tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus()

        def on_focus_out(event):
            new_val = entry.get()
            move_to_next = True

            if not self.is_valid_od(new_val):
                messagebox.showerror("Invalid Input", "Please enter a number between 0.0 and 100.0")
                new_val = ""
                move_to_next = False
            self.tree.set(item, column=column, value=new_val)
            entry.destroy()

            if new_val.strip() == "":
                move_to_next = False
                self.tree.selection_remove(item)

            if move_to_next:
                items = self.tree.get_children()
                current_index = items.index(item)
                if current_index + 1 < len(items):
                    next_item = items[current_index + 1]
                    self.tree.selection_set(next_item)
                    self.tree.focus(next_item)
                    self.tree.see(next_item)
                    self.after(10, lambda: self.edit_cell(next_item, "#2"))

        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Return>", lambda e: on_focus_out(e))

    def on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if column != "#3":  # Only handle clicks on "Selected" column
            return

        current = self.tree.set(row_id, "Selected")
        new_val = "[x]" if current.strip() == "[ ]" else "[ ]"
        self.tree.set(row_id, "Selected", new_val)

    def get_selected_indices(self):
        selected = []
        for item in self.tree.get_children():
            if self.tree.set(item, "Selected") == "[x]":
                selected.append(self.tree.set(item, "Index"))
        return selected

    def is_valid_od(self, val):
        try:
            f = float(val)
            return 0.0 <= f <= 100.0
        except ValueError:
            return False