import statistics
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


class CalibrationView(tk.Frame):
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

        self.tree = ttk.Treeview(left_frame, columns=("Index", "OD"), show="headings")
        self.tree.heading("Index", text="Index")
        self.tree.heading("OD", text="OD")
        self.tree.column("Index", width=50, anchor="center")
        self.tree.column("OD", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Insert 50 rows with index
        for i in range(50):
            self.tree.insert("", "end", values=(i + 1, ""))

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Delete>", self.delete_selected_row)
        self.tree.bind("<Return>", self.on_return_key)


        run_button = tk.Button(self, text="Run Calibration", command=self.run_calibration,
                                font=("Arial", 12), width=16, height=2)
        run_button.pack(side='top', anchor='e', pady=10)

        run_10_button = tk.Button(self, text="Run 10 Calibrations", command=self.run_10_calibrations,
                                font=("Arial", 12), width=16, height=2)
        run_10_button.pack(side='top', anchor='e', pady=10)

        right_frame = tk.Frame(self)
        right_frame.pack(side="left", fill="both", expand=True)

    def on_return_key(self, event):
        # Select the cell and start editing if OD column
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
        # Start cell editing
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if column == "#1":
            return  # Prevent editing the index column
        if not item:
            return

        x, y, width, height = self.tree.bbox(item, column)
        entry = tk.Entry(self.tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus()

        def on_focus_out(event):
            new_val = entry.get()
            if not self.is_valid_od(new_val):
                messagebox.showerror("Invalid Input", "Please enter a number between 0.0 and 100.0")
                new_val = ""
            self.tree.set(item, column=column, value=new_val)
            entry.destroy()

        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Return>", lambda e: on_focus_out(e))

    def delete_selected_row(self, event=None):
        selected = self.tree.selection()
        for item in selected:
            self.tree.delete(item)
        self.reindex_tree()

    def reindex_tree(self):
        for i, item in enumerate(self.tree.get_children()):
            od_val = self.tree.item(item, "values")[1]
            self.tree.item(item, values=(i + 1, od_val))

    def is_valid_od(self, value):
        try:
            num = float(value)
            return 0 <= num <= 100
        except ValueError:
            return False

    def run_calibration(self):
        modal = tk.Toplevel(self)
        modal.title("Calibration Running")
        modal.geometry("300x150")
        modal.resizable(False, False)

        label = tk.Label(modal, text="Calibration is running...\nPlease wait or cancel.", font=("Arial", 12))
        label.pack(pady=20)

        received_numbers = []

        def on_cancel():
            UARTUtil.send_data(self.ser, "CMD:CANCEL_CALIBRATION")
            modal.grab_release()
            modal.destroy()

        cancel_btn = tk.Button(modal, text="Cancel", command=on_cancel, font=("Arial", 12), width=10)
        cancel_btn.pack(pady=10)

        modal.protocol("WM_DELETE_WINDOW", lambda: None)
        modal.transient(self)
        modal.grab_set()
        modal.focus_set()

        UARTUtil.send_data(self.ser, "CMD:CALIBRATE")
        data = []
        for item in self.tree.get_children():
            od = self.tree.item(item, "values")[1]
            data.append([od])

        self.calibration_session = CalibrationSession(data)
        populated_count = sum(1 for row in data if row[0].strip() != "")
        UARTUtil.send_data(self.ser, "CHANNELS:" + str(populated_count))

        def poll_uart():
            line = UARTUtil.receive_data(self.ser)
            if line:
                line = line.strip()
                # Check for "OD:" prefix and extract the number
                if "OD:" in line:
                    print("Received line:", line, "\n\n\n\n\n")
                    try:
                        number_str = line[3:]  # Everything after "OD:"
                        number = float(number_str)
                        received_numbers.append(number)
                    except ValueError:
                        pass  # Ignore malformed numbers

                # Check for calibration finished message
                if "CMD:CALIBRATION_FINISHED" in line:
                    print("Calibration finished! Numbers received:", received_numbers)
                    modal.grab_release()
                    modal.destroy()
                    
                    # Create a 2D array: [channel_index, OD, received_number]
                    result_array = []
                    tree_items = list(self.tree.get_children())
                    for idx, number in enumerate(received_numbers):
                        if idx < len(tree_items):
                            channel_index = int(self.tree.item(tree_items[idx], "values")[0])
                            od = float(self.tree.item(tree_items[idx], "values")[1])
                            result_array.append([channel_index, float(number), od])
                    print("Result array:", result_array)

                    self.calibration_session = CalibrationSession(result_array)

                    graph_channels, graph_V, graph_OD, log, r_squared = self.calibration_session.run_calibration()

                    fig, ax = plt.subplots(figsize=(5, 4))
                    ax.scatter(graph_V, graph_OD, color='blue')
                    a, b = log.a, log.b
                    x_fit = np.linspace(min(graph_V), max(graph_V), 200)
                    y_fit = a * np.log(x_fit) + b
                    ax.plot(x_fit, y_fit, color='red', label='Fit: a*log(V)+b')
                    ax.legend()

                     # Annotate with equation and R²
                    equation_text = f'y = {a:.3f}ln(x) + {b:.3f}\n$R^2$ = {r_squared:.4f}'
                    plt.text(0.05, 0.95, equation_text, transform=plt.gca().transAxes,
                            fontsize=10, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7))
                    
                    for i, label in enumerate(graph_channels):
                        voltage = graph_V[i]
                        od = graph_OD[i]
                        annotation = f"Ch:{label}\nV:{voltage:.2f}\nOD:{od:.2f}"
                        ax.annotate(annotation, (voltage, od), textcoords="offset points", xytext=(10, 10), ha='left', fontsize=8, bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.3))

                    for i, label in enumerate(graph_channels):
                        ax.annotate(str(label), (graph_V[i], graph_OD[i]), textcoords="offset points", xytext=(5, 5), ha='left', fontsize=10)

                    ax.set_xlabel("Voltage")
                    ax.set_ylabel("Optical Density")
                    ax.set_title("Calibration: Voltage vs Optical Density")
                    ax.grid(True)

                    if self.canvas is not None:
                        self.canvas.get_tk_widget().destroy()

                    self.canvas = FigureCanvasTkAgg(fig, master=self)
                    self.canvas.draw()
                    self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True)
                    return

            # Poll again after 100 ms
            modal.after(100, poll_uart)

        poll_uart()

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

        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

    def run_10_calibrations(self):
        results = []
        for _ in range(10):
            modal = tk.Toplevel(self)
            modal.title("Calibration Running")
            modal.geometry("300x150")
            modal.resizable(False, False)

            label = tk.Label(modal, text="Calibration is running...\nPlease wait or cancel.", font=("Arial", 12))
            label.pack(pady=20)

            received_numbers = []

            def on_cancel():
                UARTUtil.send_data(self.ser, "CMD:CANCEL_CALIBRATION")
                modal.grab_release()
                modal.destroy()

            cancel_btn = tk.Button(modal, text="Cancel", command=on_cancel, font=("Arial", 12), width=10)
            cancel_btn.pack(pady=10)

            modal.protocol("WM_DELETE_WINDOW", lambda: None)
            modal.transient(self)
            modal.grab_set()
            modal.focus_set()

            UARTUtil.send_data(self.ser, "CMD:CALIBRATE")
            data = []
            for item in self.tree.get_children():
                od = self.tree.item(item, "values")[1]
                data.append([od])

            self.calibration_session = CalibrationSession(data)
            populated_count = sum(1 for row in data if row[0].strip() != "")
            UARTUtil.send_data(self.ser, "CHANNELS:" + str(populated_count))

            def poll_uart():
                line = UARTUtil.receive_data(self.ser)
                if line:
                    line = line.strip()
                    if "OD:" in line:
                        try:
                            number_str = line[3:]
                            number = float(number_str)
                            received_numbers.append(number)
                        except ValueError:
                            pass

                    if "CMD:CALIBRATION_FINISHED" in line:
                        modal.grab_release()
                        modal.destroy()
                        result_array = []
                        tree_items = list(self.tree.get_children())
                        for idx, number in enumerate(received_numbers):
                            if idx < len(tree_items):
                                channel_index = int(self.tree.item(tree_items[idx], "values")[0])
                                od = float(self.tree.item(tree_items[idx], "values")[1])
                                result_array.append([channel_index, float(number), od])
                        results.append(result_array)
                        return

            modal.after(100, poll_uart)

            poll_uart()
            self.wait_window(modal)

        # After all calibrations, results is a list of 10 runs, each with [channel_index, voltage, od]
        # You can process or save results here as needed
        result_str = "All calibration runs complete. Results:\n"
        # Organize results by channel
        channel_data = {}
        for run in results:
            for channel_index, voltage, od in run:
                if channel_index not in channel_data:
                    channel_data[channel_index] = []
                channel_data[channel_index].append(voltage)
        for run_idx, run in enumerate(results):
            result_str += f"Run {run_idx+1}:\n"
            for channel_index, voltage, od in run:
                result_str += f"  Channel: {channel_index}, Voltage: {voltage}, OD: {od}\n"
        result_str += "\nVoltage Variance by Channel:\n"
        for channel_index in sorted(channel_data.keys()):
            voltages = channel_data[channel_index]
            if len(voltages) > 1:
                var = statistics.variance(voltages)
            else:
                var = 0.0
                result_str += f"  Channel {channel_index}: Variance = {var:.6f}\n"
        messagebox.showinfo("Calibration Results", result_str)