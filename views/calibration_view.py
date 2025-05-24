import tkinter as tk
import tksheet
import time
class CalibrationView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="Calibration")
        label.pack(side='top', anchor='n', pady=10)

        button = tk.Button(self, text="Home", command=lambda: controller.show_frame("MenuView"))
        button.pack(side='top', anchor='e')
        
        info_text = (
            "Enter calibration values (0-100) in the table below.\n"
            "Double-click a cell to edit. Press Ctrl+N to add a row.\n"
            "Select a row and press Delete or Backspace to remove it."
        )
        info_label = tk.Label(self, text=info_text, justify="left", fg="black")
        info_label.pack(pady=(0, 10))

        # Create a frame to hold the sheet on the left half
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill='y')
        left_frame.pack()

        self.sheet = tksheet.Sheet(
            left_frame,
            data=[[""], [""]],
            headers=["Channel", "Value"],
            font=("Arial", 24, 'bold'),  # Cell font
            header_font=("Arial", 24, 'bold'),  # Header font
            index_font=("Arial", 24, 'bold'),   # Index font
            show_x_scrollbar=False
        )
        self.sheet.set_index_width(30)
        # Set column widths to evenly fill remaining space after index width
        def resize_columns(event=None):
            total_width = left_frame.winfo_width()
            index_width = 30
            num_columns = len(self.sheet.headers())
            if num_columns > 0:
                col_width = max(50, int((total_width - index_width) / num_columns))
                for col in range(num_columns):
                    self.sheet.column_width(col, col_width)
        left_frame.bind("<Configure>", resize_columns)
        self.after(100, resize_columns)
        self.sheet.enable_bindings((
            "single_select",
            "row_select",
            "edit_cell",
            "shift_select",
            "ctrl_select",
            "select_all",
            "drag_select",
            "arrowkeys"
        ))
        self.sheet.bind("<Delete>", lambda event: self.delete_row())
        self.sheet.bind("<BackSpace>", lambda event: self.delete_row())
        self.sheet.extra_bindings([
            ("end_edit_cell", self.validate_cell)
        ])
        self.sheet.pack()
        self.sheet.pack(fill="both", expand=True)
        label.config(font=("Arial", 18))
        info_label.config(font=("Arial", 12))
        button.config(font=("Arial", 12), width=10, height=2)
    def delete_row(self):
        selected_rows = self.sheet.get_selected_rows()
        if selected_rows:
            # Delete rows in reverse order to avoid index shifting
            for row in sorted(selected_rows, reverse=True):
                self.sheet.delete_row(row)
        self.sheet.select_row(self.sheet.total_rows() - 1)
        
    def validate_cell(self, event):
        row, col = event.row, event.column
        value = self.sheet.get_cell_data(row, col)
        try:
            num = float(value)
            if not (0 <= num <= 100):
                raise ValueError
        except ValueError:
            self.sheet.set_cell_data(row, col, "")
            tk.messagebox.showerror("Invalid Input", "Please enter a decimal number between 0.0 and 100.0")