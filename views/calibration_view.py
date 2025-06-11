import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from util.calibration.calibration_session import CalibrationSession
from util.uart_util import UARTUtil
import numpy as np
import matplotlib

matplotlib.use('TkAgg')  # Tkinter backend

class CalibrationView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.canvas = None
        self.ser = UARTUtil.open_port()

        tk.Label(self, text="Calibration", font=("Arial", 18)).pack(side='top', pady=10)

        tk.Button(self, text="Home", command=lambda: controller.show_frame("MenuView"),
                  font=("Arial", 12), width=10, height=2).pack(side='top', anchor='e')

        info_text = (
            "Enter calibration values (0-100) in the table below.\n"
            "Double-click a cell to edit."
        )
        tk.Label(self, text=info_text, justify="left", fg="black", font=("Arial", 12)).pack(pady=(0, 10))

        # Table frame
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill='both', expand=True)

        self.tree = ttk.Treeview(left_frame, columns=("Channel", "OD"), show="headings", height=20)
        self.tree.heading("Channel", text="Channel")
        self.tree.heading("OD", text="OD")
        self.tree.column("Channel", width=100, anchor="center")
        self.tree.column("OD", width=100, anchor="center")
        self.tree.pack(expand=True, fill="both")

        for _ in range(50):
            self.tree.insert("", "end", values=("", ""))

        self.tree.bind("<Double-1>", self.edit_cell)

        # Run calibration button
        tk.Button(self, text="Run Calibration", command=self.run_calibration,
                  font=("Arial", 12), width=16, height=2).pack(side='top', anchor='e', pady=10)

        # Graph area
        right_frame = tk.Frame(self)
        right_frame.pack(side="left", fill="both", expand=True)

    def edit_cell(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item or not column:
            return

        col_index = int(column.replace('#', '')) - 1
        x, y, width, height = self.tree.bbox(item, column)
        old_value = self.tree.set(item, column)

        entry = tk.Entry(self.tree)
        entry.insert(0, old_value)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus()

        def validate_and_save(event=None):
            new_value = entry.get()
            if new_value.strip() == "":
                self.tree.set(item, column, "")
            else:
                try:
                    num = float(new_value)
                    if not (0 <= num <= 100):
                        raise ValueError
                    self.tree.set(item, column, str(num))
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please enter a decimal number between 0 and 100.")
            entry.destroy()

        entry.bind("<Return>", validate_and_save)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def run_calibration(self):
        data = []
        for row_id in self.tree.get_children():
            row = [self.tree.set(row_id, "Channel"), self.tree.set(row_id, "OD")]
            if all(cell.strip() != "" for cell in row):
                data.append(row)
            else:
                break

        self.calibration_session = CalibrationSession(data)
        UARTUtil.send_data(self.ser, "CHANNELS:" + str(len(data)))

    def run_calibration_from_json(self):
        self.calibration_session = CalibrationSession(None)
        graph_channels, graph_V, graph_OD, log = self.calibration_session.run_test_json_calibration()

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

        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()

        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True)
