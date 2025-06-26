import statistics
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from util.calibration.calibration_curve import LogarithmicCalibrationCurve
from util.calibration.calibration_session import CalibrationSession
from util.uart_util import UARTUtil
import matplotlib
from collections import defaultdict

matplotlib.use("TkAgg")


class CalibrationView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.canvas = None
        self.ser = UARTUtil.open_port()

        label = tk.Label(self, text="Calibration", font=("Arial", 18))
        label.pack(side="top", anchor="n", pady=10)

        button = tk.Button(
            self,
            text="Home",
            command=lambda: controller.show_frame("MenuView"),
            font=("Arial", 12),
            width=10,
            height=2,
        )
        button.pack(side="top", anchor="e")

        info_text = "Enter known Optical Density (OD) values for your samples.\nThen run the calibration to generate a curve."

        info_label = tk.Label(
            self, text=info_text, justify="left", fg="black", font=("Arial", 12)
        )
        info_label.pack(pady=(0, 10))

        # Treeview for calibration data
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill="both", expand=True)

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

        button_frame = tk.Frame(self)
        button_frame.pack(side="top", anchor="e", pady=10)

        run_button = tk.Button(
            button_frame,
            text="Run Calibration",
            command=self.run_calibration,
            font=("Arial", 12),
            width=16,
            height=2,
        )
        run_button.pack(side="left", padx=5)

        run_10_button = tk.Button(
            button_frame,
            text="Run 10 Calibrations",
            command=self.run_10_calibrations,
            font=("Arial", 12),
            width=16,
            height=2,
        )
        run_10_button.pack(side="left", padx=5)

        right_frame = tk.Frame(self)
        right_frame.pack(side="left", fill="both", expand=True)

    def on_return_key(self, event):
        # Select the cell and start editing if OD column
        item = self.tree.focus()
        if not item:
            return
        col = self.tree.identify_column(event.x) if hasattr(event, "x") else "#2"
        if col == "#1":
            return
        x, y, width, height = self.tree.bbox(item, col)
        entry = tk.Entry(self.tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus()

        def on_focus_out(event):
            new_val = entry.get()
            if not self.is_valid_od(new_val):
                messagebox.showerror(
                    "Invalid Input", "Please enter a number between 0.0 and 100.0"
                )
                new_val = ""
            self.tree.set(item, column=col, value=new_val)
            entry.destroy()

        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Return>", lambda e: on_focus_out(e))

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if column == "#1" or not item:
            return  # Don't allow editing of Index column

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
                messagebox.showerror(
                    "Invalid Input", "Please enter a number between 0.0 and 100.0"
                )
                new_val = ""
                move_to_next = False  # Don't move if invalid
            self.tree.set(item, column=column, value=new_val)
            entry.destroy()

            if new_val.strip() == "":
                move_to_next = False
                self.tree.selection_remove(item)  # Deselect current row

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

    def is_valid_od(self, value):
        if value == "":
            return True
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

        label = tk.Label(
            modal,
            text="Calibration is running...\nPlease wait or cancel.",
            font=("Arial", 12),
        )
        label.pack(pady=20)

        received_numbers = []

        def on_cancel():
            UARTUtil.send_data(self.ser, "CMD:CANCEL_CALIBRATION")
            modal.grab_release()
            modal.destroy()

        cancel_btn = tk.Button(
            modal, text="Cancel", command=on_cancel, font=("Arial", 12), width=10
        )
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
                    print("Received line:", line, "\n\n\n\n\n")
                    try:
                        number_str = line[3:]
                        number = float(number_str)
                        received_numbers.append(number)
                    except ValueError:
                        pass

                if "CMD:CALIBRATION_FINISHED" in line:
                    print("Calibration finished! Numbers received:", received_numbers)
                    modal.grab_release()
                    modal.destroy()

                    result_array = []
                    tree_items = list(self.tree.get_children())
                    for idx, number in enumerate(received_numbers):
                        if idx < len(tree_items):
                            channel_index = int(
                                self.tree.item(tree_items[idx], "values")[0]
                            )
                            od = float(self.tree.item(tree_items[idx], "values")[1])
                            result_array.append([channel_index, float(number), od])
                    print("Result array:", result_array)

                    self.calibration_session = CalibrationSession(result_array)

                    # We still run this to get the raw data, but will ignore the log fit results
                    graph_channels, graph_V, graph_OD, log, r_squared_log, error_bars = (
                        self.calibration_session.run_calibration()
                    )

                    # --- MODIFICATION: Perform a 1/x fit ---
                    graph_V = np.array(graph_V)
                    graph_OD = np.array(graph_OD)

                    # Transform x-data to 1/x for linear fitting (y = a*x' + b where x' = 1/x)
                    inv_graph_V = 1.0 / graph_V
                    a, b = np.polyfit(inv_graph_V, graph_OD, 1)

                    # Calculate the R-squared value for the new 1/x fit
                    y_predicted = a * inv_graph_V + b
                    ss_res = np.sum((graph_OD - y_predicted) ** 2)
                    ss_tot = np.sum((graph_OD - np.mean(graph_OD)) ** 2)
                    r_squared = 1 - (ss_res / ss_tot)
                    # --- END MODIFICATION ---

                    fig, ax = plt.subplots(figsize=(5, 4))
                    ax.plot(graph_V, graph_OD, "o", color="blue", label="Measured OD")

                    # --- MODIFICATION: Update error bar and fit line plotting for 1/x model ---
                    graph_OD_fit = a / graph_V + b

                    for x, y_fit_val, yerr in zip(graph_V, graph_OD_fit, error_bars):
                        ax.vlines(x, y_fit_val - yerr, y_fit_val + yerr, color="red", linewidth=1)
                        ax.hlines(y_fit_val - yerr, x - 0.05, x + 0.05, color="red")
                        ax.hlines(y_fit_val + yerr, x - 0.05, x + 0.05, color="red")

                    # Plot the new fitted line
                    x_fit = np.linspace(min(graph_V), max(graph_V), 200)
                    y_fit = a / x_fit + b
                    ax.plot(x_fit, y_fit, color="green", label="Fit: y = a/x + b")
                    ax.legend()

                    # Annotate with the new equation and R²
                    equation_text = f"y = {a:.3f}/x + {b:.3f}\n$R^2$ = {r_squared:.4f}"
                    # --- END MODIFICATION ---

                    plt.text(
                        0.10,
                        0.10,
                        equation_text,
                        transform=plt.gca().transAxes,
                        fontsize=10,
                        verticalalignment="bottom",
                        bbox=dict(facecolor="white", alpha=0.7),
                    )

                    for i, label in enumerate(graph_channels):
                        voltage = graph_V[i]
                        od = graph_OD[i]
                        annotation = f"Ch:{label}\nV:{voltage:.2f}\nOD:{od:.2f}"
                        ax.annotate(
                            annotation,
                            (voltage, od),
                            textcoords="offset points",
                            xytext=(10, 10),
                            ha="left",
                            fontsize=8,
                            bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.3),
                        )

                    ax.set_xlabel("Voltage")
                    ax.set_ylabel("Optical Density")
                    ax.set_title("Calibration: Voltage vs Optical Density")
                    ax.grid(True)

                    if self.canvas is not None:
                        self.canvas.get_tk_widget().destroy()

                    self.canvas = FigureCanvasTkAgg(fig, master=self)
                    self.canvas.draw()
                    self.canvas.get_tk_widget().pack(
                        side="right", fill="both", expand=True
                    )

                    # --- MODIFICATION: Handle the initialization of the curve ---
                    # The original code initialized a LogarithmicCalibrationCurve.
                    # This line is now commented out as it's for the wrong model.
                    # You may need to create and initialize a new curve class here.
                    # LogarithmicCalibrationCurve.init(a, b)
                    # --- END MODIFICATION ---
                    return

            modal.after(100, poll_uart)

    def run_calibration_from_json(self):
        self.calibration_session = CalibrationSession(None)

        graph_channels, graph_V, graph_OD, log, r_squared_log, error_bars = (
            self.calibration_session.run_test_json_calibration()
        )

        # --- MODIFICATION: Perform a 1/x fit ---
        graph_V = np.array(graph_V)
        graph_OD = np.array(graph_OD)

        # Transform x-data to 1/x for linear fitting (y = a*x' + b where x' = 1/x)
        inv_graph_V = 1.0 / graph_V
        a, b = np.polyfit(inv_graph_V, graph_OD, 1)

        # Calculate the R-squared value for the new 1/x fit
        y_predicted = a * inv_graph_V + b
        ss_res = np.sum((graph_OD - y_predicted) ** 2)
        ss_tot = np.sum((graph_OD - np.mean(graph_OD)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        # --- END MODIFICATION ---

        fig, ax = plt.subplots(figsize=(5, 4))
        ax.plot(graph_V, graph_OD, "o", color="blue", label="Measured OD")

        # --- MODIFICATION: Update error bar and fit line plotting for 1/x model ---
        graph_OD_fit = a / graph_V + b

        for x, y_fit_val, yerr in zip(graph_V, graph_OD_fit, error_bars):
            ax.vlines(x, y_fit_val - yerr, y_fit_val + yerr, color="red", linewidth=1)
            ax.hlines(y_fit_val - yerr, x - 0.05, x + 0.05, color="red")
            ax.hlines(y_fit_val + yerr, x - 0.05, x + 0.05, color="red")

        # Plot the new fitted line
        x_fit = np.linspace(min(graph_V), max(graph_V), 200)
        y_fit = a / x_fit + b
        ax.plot(x_fit, y_fit, color="green", label="Fit: y = a/x + b")
        ax.legend()

        # Annotate with the new equation and R²
        equation_text = f"y = {a:.3f}/x + {b:.3f}\n$R^2$ = {r_squared:.4f}"
        # --- END MODIFICATION ---

        plt.text(
            0.10,
            0.10,
            equation_text,
            transform=plt.gca().transAxes,
            fontsize=10,
            verticalalignment="bottom",
            bbox=dict(facecolor="white", alpha=0.7),
        )

        for i, label in enumerate(graph_channels):
            voltage = graph_V[i]
            od = graph_OD[i]
            annotation = f"Ch:{label}\nV:{voltage:.2f}\nOD:{od:.2f}"
            ax.annotate(
                annotation,
                (voltage, od),
                textcoords="offset points",
                xytext=(10, 10),
                ha="left",
                fontsize=8,
                bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.3),
            )

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
        for i in range(10):
            modal = tk.Toplevel(self)
            modal.title("Calibration Running")
            modal.geometry("350x200")
            modal.resizable(False, False)

            run_label = tk.Label(
                modal, text=f"Run {i + 1} of 10", font=("Arial", 12, "bold")
            )
            run_label.pack(pady=(10, 0))

            label = tk.Label(
                modal,
                text="Calibration is running...\nPlease wait or cancel.",
                font=("Arial", 12),
            )
            label.pack(pady=10)

            received_numbers = []

            def on_cancel():
                UARTUtil.send_data(self.ser, "CMD:CANCEL_CALIBRATION")
                modal.grab_release()
                modal.destroy()

            cancel_btn = tk.Button(
                modal, text="Cancel", command=on_cancel, font=("Arial", 12), width=10
            )
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
                                od_val = self.tree.item(tree_items[idx], "values")[1]
                                if od_val: # Ensure OD is not empty
                                    channel_index = int(self.tree.item(tree_items[idx], "values")[0])
                                    od = float(od_val)
                                    result_array.append([channel_index, float(number), od])
                        results.append(result_array)
                        return

                modal.after(100, poll_uart)

            poll_uart()
            self.wait_window(modal)

        channel_voltages = defaultdict(list)
        for run in results:
            for channel_index, voltage, od in run:
                channel_voltages[channel_index].append(voltage)

        variance_str = ""
        for channel_index in sorted(channel_voltages.keys()):
            voltages = channel_voltages[channel_index]
            if len(voltages) > 1:
                stdev = statistics.stdev(voltages)
            else:
                stdev = 0.0
            variance_str += f"Channel {channel_index}: ADC StDev = {stdev:.3f}\n"

        messagebox.showinfo("Calibration Statistics", variance_str)