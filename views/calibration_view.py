import tkinter as tk
import tksheet
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from util.calibration.calibration_session import CalibrationSession
import numpy as np
import matplotlib
from util.uart_util import UARTUtil
matplotlib.use('TkAgg')  # Force TkAgg backend

class CalibrationView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.canvas = None

        self.ser = UARTUtil.open_port()

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
        left_frame.pack(side="left", fill='both', expand=True)

        self.sheet = tksheet.Sheet(
            left_frame,
            data=[["", ""] for _ in range(50)],
            headers=["Channel", "OD"],
            font=("Arial", 24, 'bold'),  # Cell font
            header_font=("Arial", 24, 'bold'),  # Header font
            index_font=("Arial", 24, 'bold'),   # Index font
            show_x_scrollbar=False,
        )
        self.sheet.set_index_width(40)
        self.sheet.set_all_column_widths(200)
        self.sheet.enable_bindings((
            "edit_cell",
            "arrowkeys",
        ))
        self.sheet.extra_bindings([
            ("end_edit_cell", self.validate_cell)
        ])
        self.sheet.pack()
        self.sheet.pack(fill="both", expand=True)
        label.config(font=("Arial", 18))
        info_label.config(font=("Arial", 12))
        button.config(font=("Arial", 12), width=10, height=2)

        run_button = tk.Button(self, text="Run Calibration", command=lambda: self.run_calibration())
        run_button.pack(side='top', anchor='e', pady=10)
        run_button.config(font=("Arial", 12), width=16, height=2)

        # Create a frame to hold the graph on the right half
        right_frame = tk.Frame(self)
        right_frame.pack(side="left", fill="both", expand=True)
        
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

    def run_calibration(self):
        # Retrieve data from the sheet
        data = self.sheet.get_sheet_data()
        self.calibration_session = CalibrationSession(data)
        # Count how many rows have both cells populated, starting from the top
        populated_count = 0
        for row in data:
            if all(cell.strip() != "" for cell in row):
                populated_count += 1
            else:
                break
        UARTUtil.send_data(self.ser, "CHANNELS:" + str(populated_count))

    def run_calibration_from_json(self):
        # Run calibration
        self.calibration_session = CalibrationSession(None)
        graph_channels, graph_V, graph_OD, log = self.calibration_session.run_test_json_calibration()

        # Create the figure and axes
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.scatter(graph_V, graph_OD, color='blue')
        a, b = log.a, log.b
        x_fit = np.linspace(min(graph_V), max(graph_V), 200)
        y_fit = a * np.log(x_fit) + b
        ax.plot(x_fit, y_fit, color='red', label='Fit: a*log(V)+b')
        ax.legend()

        for i, label in enumerate(graph_channels):
            ax.annotate(str(label), (graph_V[i], graph_OD[i]), textcoords="offset points", xytext=(5,5), ha='left', fontsize=10)

        ax.set_xlabel("Voltage")
        ax.set_ylabel("Optical Density")
        ax.set_title("Calibration: Voltage vs Optical Density")
        ax.grid(True)

        # Clear the old canvas if it exists
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()

        # Create and store new canvas
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True)
