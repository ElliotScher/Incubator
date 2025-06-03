import tkinter as tk
import tksheet
class RunView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="Run")
        label.pack(pady=10)

        homeButton = tk.Button(self, text="Home",
                           command=lambda: controller.show_frame("MenuView"))
        homeButton.pack()

        # Create a frame to hold the buttons above the table
        button_frame = tk.Frame(self)
        button_frame.pack(side="top", fill="x", padx=10, pady=(10, 0))

        selectAll = tk.Button(button_frame, text="Select All", command=lambda: self.select_all_checkboxes())
        selectAll.pack(side="left", padx=5)

        deselectAll = tk.Button(button_frame, text="Deselect All", command=lambda: self.deselect_all_checkboxes())
        deselectAll.pack(side="left", padx=5)

        rePlot = tk.Button(button_frame, text="replot", command=lambda: None)
        rePlot.pack(side="left", padx=5)

        # Create a frame to hold the sheet on the left half
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill='both', expand=True)

        self.sheet = tksheet.Sheet(
            left_frame,
            data=[[""], [""], [""]],
            headers=["✓", "channel", "Serial"],
            show_row_index=False,
            font=("Arial", 24, 'bold'),  # Cell font
            header_font=("Arial", 24, 'bold'),  # Header font
            index_font=("Arial", 24, 'bold'),   # Index font
            show_x_scrollbar=False
        )

        self.sheet.pack(fill="both", expand=True)

        # Set the first column as a checkbox column
        self.sheet.enable_bindings((
            "checkbox_edited",
            "row_select",
            "column_select",
            "edit_cell",
            "single_select",
            "drag_select",
            "arrowkeys",
            "right_click_popup_menu",
            "rc_select",
            "shift_select",
            "ctrl_select",
            "select_all",
        ))
        self.sheet.set_all_column_widths(200)
        self.sheet.bind("<Control-n>", lambda event: self.insert_row())
        self.sheet.bind("<Delete>", lambda event: self.delete_row())
        self.sheet.bind("<BackSpace>", lambda event: self.delete_row())

    def insert_row(self):
        self.sheet.insert_row(idx=self.sheet.get_total_rows())
        # Insert a new row with a checkbox in the first column
        row_idx = self.sheet.get_total_rows() - 1
        self.sheet.create_checkbox(r=row_idx, c=0, checked=False)

    def delete_row(self):
        selected_rows = self.sheet.get_selected_rows()
        if selected_rows:
            # Delete rows in reverse order to avoid index shifting
            for row in sorted(selected_rows, reverse=True):
                self.sheet.delete_row(row)
        self.sheet.select_row(self.sheet.total_rows() - 1)

    def select_all_checkboxes(self):
        for row in range(self.sheet.get_total_rows()):
            self.sheet.create_checkbox(row, 0, True)
    
    def deselect_all_checkboxes(self):
        for row in range(self.sheet.get_total_rows()):
            self.sheet.create_checkbox(row, 0, False)