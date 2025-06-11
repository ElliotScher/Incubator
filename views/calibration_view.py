import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import matplotlib

from util.calibration.calibration_session import CalibrationSession
from util.uart_util import UARTUtil

matplotlib.use('TkAgg')  # Force TkAgg backend

class CalibrationView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.canvas = None
        self.editing_entry = None

        self.ser = UARTUtil.open_port()

        label = tk.Label(self, text="Calibration")
        label.pack(side='top', anchor='n', pady=10)

        button = tk.Button(self, text="Home", command=lambda: controller.show_frame("MenuView"))
        button.pack(side='top', anchor='e')

        info_text = (
            "Enter calibration values (0-100) in the table below.\n"
            "Double-click a cell to edit. Use buttons to add/remove rows."
        )
        info_label = tk.Label(self, text=info_text, justify="left", fg="black")
        info_label.pack(pady=(0, 10))

        label.config(font=("Arial", 18))
        info_label.config(font=("Arial", 12))
        button.config(font=("Arial", 12), width=10, height=2)

        # Left frame with Treeview
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill='both', expand=True)

        self.tree = ttk.Treeview(left_frame, columns=("OD",), show="headings")
        self.tree.heading("OD", text="OD")
        self.tree.pack(fill="both", expand=True)

        for _ in range(50):
            self.tree.insert('', 'end', values=(""))

        self.tree.bind("<Double-1>", self.on_double_click)

        # Buttons for row manipulation
        controls = tk.Frame(left_frame)
        controls.pack(fill='x', pady=5)

        add_btn = tk.Button(controls, text="Add Row", command=self.add_row)
        add_btn.pack(side='left', padx=5)

        del_btn = tk.Button(controls, text="Delete Row", command=self.delete_row)
        del_btn.pack(side='left', padx=5)

        run_button = tk.Button(self, text="Run Calibration", command=self.run_calibration)
        run_button.pack(side='top', anchor='e', pady=10)
        run_button.config(font=("Arial", 12), width=16, height=2)

        # Right frame with graph
        self.right_frame = tk.Frame(self)
        self.right_frame.pack(side="left", fill="both", expand=True)

    def add_row(self):
        self.tree.insert('', 'end', values=(""))

    def delete_row(self):
        selected = self.tree.selection()
        for item in selected:
            self.tree.delete(item)

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if item and column:
            col = int(column[1:]) - 1
            x, y, width, height = self.tree.bbox(item, column)
            value = self.tree.set(item, column)

            self.editing_entry = tk.Entry(self.tree)
            self.editing_entry.insert(0, value)
            self.editing_entry.place(x=x, y=y, width=width, height=height)
            self.editing_entry.focus()

            def save_edit(event):
                new_value = self.editing_entry.get()
                try:
                    num = float(new_value)
                    if not (0 <= num <= 100):
                        raise ValueError
                    self.tree.set(item, column, new_value)
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please enter a number between 0.0 and 100.0")
                finally:
                    self.editing_entry.destroy()
                    self.editing_entry = None

            self.editing_entry.bind("<Return>", save_edit)
            self.editing_entry.bind("<FocusOut>", save_edit)

    def run_calibration(self):
        data = []
        for item in self.tree.get_children():
            row_data = self.tree.item(item)['values']
            data.append([str(cell) for cell in row_data])
        self.calibration_session = CalibrationSession(data)

        populated_count = 0
        for row in data:
            if all(cell.strip() != "" for cell in row):
                populated_count += 1
            else:
                break
        UARTUtil.send_data(self.ser, "CHANNELS:" + str(populated_count))

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
            ax.annotate(str(label), (graph_V[i], graph_OD[i]), textcoords="offset points", xytext=(5, 5), ha='left', fontsize=10)

        ax.set_xlabel("Voltage")
        ax.set_ylabel("Optical Density")
        ax.set_title("Calibration: Voltage vs Optical Density")
        ax.grid(True)

        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()

        self.canvas = FigureCanvasTkAgg(fig, master=self.right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True)
