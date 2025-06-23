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
from util.reaction.reaction_data import ReactionData
import time

class RunView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.canvas = None
        self.ser = UARTUtil.open_port()

        # Initialize self.data with 50 ReactionData objects
        self.data = []
        for i in range(50):
            self.data.append(ReactionData(i))
        self.data_iterator = 0

        label = tk.Label(self, text="Reaction", font=("Arial", 18))
        label.pack(side='top', anchor='n', pady=10)

        button = tk.Button(self, text="Home", command=lambda: controller.show_frame("MenuView"),
                           font=("Arial", 12), width=10, height=2)
        button.pack(side='top', anchor='e')

        info_text = (
            "Add text here"
        )
        info_label = tk.Label(self, text=info_text, justify="left", fg="black", font=("Arial", 12))
        info_label.pack(pady=(0, 10))

        # Treeview for calibration data
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill='both', expand=True)

        # Only two columns now: Selected and Index
        self.tree = ttk.Treeview(left_frame, columns=("Selected", "Index"), show="headings", height=15)
        self.tree.heading("Selected", text="✓")
        self.tree.heading("Index", text="Idx")
        self.tree.column("Selected", width=50, minwidth=20, anchor="center", stretch=False)
        self.tree.column("Index", width=50, minwidth=30, anchor="center", stretch=False)
        self.tree.pack(side="left", fill="y", expand=False)

        # Make left_frame take up 1/4 of the parent width
        self.update_idletasks()
        total_width = self.winfo_width() or 800  # fallback if not yet rendered
        left_frame.config(width=int(total_width * 0.25))
        left_frame.pack_propagate(False)

        # Insert 50 rows with default selected state "[ ]"
        for i in range(50):
            self.tree.insert("", "end", values=("[ ]", i + 1))

        self.tree.bind("<Button-1>", self.on_click)

        button_frame = tk.Frame(self)
        button_frame.pack(side='top', anchor='e', pady=10)

        right_frame = tk.Frame(self)
        right_frame.pack(side="left", fill="both", expand=True)

        from matplotlib.animation import FuncAnimation

        # Plotting Frame
        plot_frame = tk.Frame(right_frame)
        plot_frame.pack(fill='both', expand=True)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.line, = self.ax.plot([], [], lw=2)
        self.ax.set_title("Optical Density vs Time")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("OD")
        self.start_time = time.time()
        self.animation = FuncAnimation(self.fig, self.update_plot, interval=500)

        self.lines = {}  # Dictionary to store Line2D objects keyed by index


        # Input for agitation count
        agitation_frame = tk.Frame(button_frame)
        agitation_frame.pack(side='left', padx=10)

        tk.Label(agitation_frame, text="Agitations:", font=("Arial", 10)).pack()
        self.agitation_var = tk.IntVar(value=5)  # default value
        agitation_entry = tk.Entry(agitation_frame, textvariable=self.agitation_var, width=5)
        agitation_entry.pack()


        run_button = tk.Button(button_frame, text="Run Reaction", bg="green", fg="white", font=("Arial", 12, "bold"), width=10, height=2,
                               command=self.run_reaction)
        run_button.pack(side='left', padx=10)

        # E-Stop button in the top right corner
        estop_button = tk.Button(button_frame, text="E-Stop", bg="red", fg="white", font=("Arial", 12, "bold"),
                                width=10, height=2, command=self.cancel_reaction)
        estop_button.pack(side='right', padx=10)

    def on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if column != "#1":  # "Selected" column is now first
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

    def run_reaction(self):
        UARTUtil.send_data(self.ser, "AGITATIONS:" + str(self.agitation_var.get()))
        UARTUtil.send_data(self.ser, "CMD:RUNREACTION")

        self._running = True  # Flag to control polling

        def poll_uart():
            if not self._running:
                self.data[0].export_csv("reaction_data.csv")  # Export data when stopping
                messagebox.showinfo("Info", "Reaction data exported to reaction_data.csv")
                return
            line = UARTUtil.receive_data(self.ser)
            if line:
                if "OD:" in line:
                    print("Processing Channel ", self.data_iterator + 1)
                    print("Received line:", line, "\n")
                    try:
                        number_str = line[3:]  # Everything after "OD:"
                        number = float(number_str)
                        self.data[self.data_iterator].add_entry(
                            time=np.datetime64('now', 'ms'),
                            optical_density=number,
                            temperature=None  # Assuming temperature is not provided in this line
                        )
                        self.data_iterator = (self.data_iterator + 1) % len(self.data)
                        if (self.data_iterator > 50):
                            # Reset iterator if it reaches the end
                            self.data_iterator = 0
                    except ValueError:
                        pass  # Ignore malformed numbers
            # Schedule next poll
            self.update_plot(None)
            self.after(100, poll_uart)  # Poll every 100 ms

        poll_uart()

    def cancel_reaction(self):
        self._running = False  # Stop polling
        UARTUtil.send_data(self.ser, "CMD:CANCEL_REACTION")

    def update_plot(self):
        if not hasattr(self, 'plot_widget') or not hasattr(self, 'curve'):
            return  # Plot not initialized yet

        self.plot_widget.clear()  # Clear old plots

        selected_indices = self.get_selected_indices()
        latest_time = None  # Keep track of latest time for scrolling

        colors = ['r', 'g', 'b', 'y', 'c', 'm', 'w']  # Cycle through colors
        color_index = 0

        for idx in selected_indices:
            try:
                df = self.data[int(idx) - 1].get_all()
                if df.empty or 'time' not in df or 'optical_density' not in df:
                    continue

                # Convert time to milliseconds since epoch for plotting
                times = df['time'].astype('int64')
                ods = df['optical_density']

                pen = pg.mkPen(color=colors[color_index % len(colors)], width=2)
                self.plot_widget.plot(times, ods, pen=pen, name=f"Channel {idx}")
                color_index += 1

                if not times.empty:
                    latest_time = max(latest_time, times.iloc[-1]) if latest_time is not None else times.iloc[-1]

            except (IndexError, ValueError, KeyError, AttributeError):
                continue

        # Optional: auto-scroll to the latest time (last 60 seconds visible)
        if latest_time is not None:
            self.plot_widget.setXRange(latest_time - 60000, latest_time)
