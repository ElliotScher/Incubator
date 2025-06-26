import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from util.calibration.calibration_session import CalibrationSession
from util.uart_util import UARTUtil
import matplotlib
matplotlib.use("TkAgg")
import re
from collections import defaultdict
from util.reaction.reaction_data import ReactionData
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import os
import shutil
import tempfile
from datetime import datetime
import zipfile


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

        self._running = False  # Flag to control the reaction state
        self._paused = False # Flag to control the pause state

        label = tk.Label(self, text="Reaction", font=("Arial", 18))
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

        info_text = "Add text here"
        info_label = tk.Label(
            self, text=info_text, justify="left", fg="black", font=("Arial", 12)
        )
        info_label.pack(pady=(0, 10))

        # Treeview for calibration data
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill="both", expand=True)

        # Only two columns now: Selected and Index
        self.tree = ttk.Treeview(
            left_frame, columns=("Selected", "Index"), show="headings", height=15
        )
        self.tree.heading("Selected", text="✓")
        self.tree.heading("Index", text="Idx")
        self.tree.column(
            "Selected", width=50, minwidth=20, anchor="center", stretch=False
        )
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
        button_frame.pack(side="top", anchor="e", pady=10)

        right_frame = tk.Frame(self)
        right_frame.pack(side="left", fill="both", expand=True)

        from matplotlib.animation import FuncAnimation

        # Plotting Frame
        plot_frame = tk.Frame(right_frame)
        plot_frame.pack(fill="both", expand=True)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        (self.line,) = self.ax.plot([], [], lw=2)
        self.ax.set_title("Optical Density vs Time")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("OD")
        self.start_time = time.time()
        self.animation = FuncAnimation(self.fig, self.update_plot, interval=500)

        self.lines = {}  # Dictionary to store Line2D objects keyed by index

        # Input for agitation count
        agitation_frame = tk.Frame(button_frame)
        agitation_frame.pack(side="left", padx=10)

        tk.Label(agitation_frame, text="Agitations:", font=("Arial", 10)).pack()
        self.agitation_var = tk.IntVar(value=5)  # default value
        agitation_entry = tk.Entry(
            agitation_frame, textvariable=self.agitation_var, width=5
        )
        agitation_entry.pack()

        # Merged Run/Stop button
        self.run_stop_button = tk.Button(
            button_frame,
            text="Run",
            bg="green",
            fg="white",
            font=("Arial", 12, "bold"),
            width=10,
            height=2,
            command=self.toggle_reaction,
        )
        self.run_stop_button.pack(side="left", padx=10)

        # Play/Pause button
        self.play_pause_button = tk.Button(
            button_frame,
            text="Pause",
            font=("Arial", 12, "bold"),
            width=8,
            height=2,
            command=self.toggle_pause,
            state="disabled"  # Initially disabled
        )
        self.play_pause_button.pack(side="left", padx=5)


        self.last_usb_path = None
        self.after(3000, self.check_usb_and_copy)

    def toggle_reaction(self):
        """Toggles the reaction state between running and stopped."""
        if not self._running:
            # Start the reaction
            self._running = True
            self._paused = False # Ensure reaction starts in an un-paused state
            self.run_stop_button.config(text="Stop", bg="red")
            self.play_pause_button.config(state="normal", text="Pause") # Enable pause button
            self._start_sequence()
        else:
            # Stop the reaction
            self._running = False
            self._paused = False # Reset pause state
            self.run_stop_button.config(text="Run", bg="green")
            self.play_pause_button.config(state="disabled", text="Pause") # Disable pause button
            self._stop_sequence()

    def toggle_pause(self):
        """Toggles the pause state of a running reaction."""
        if not self._running: # Safeguard: button should be disabled if not running
            return
        
        self._paused = not self._paused

        if self._paused:
            self.play_pause_button.config(text="Play")
        else:
            self.play_pause_button.config(text="Pause")

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

    def _start_sequence(self):
        """Handles the logic for starting the reaction sequence."""
        # Clear all ReactionData objects' dataframes
        for rd in self.data:
            rd.clear()
        self.data_iterator = 0
        UARTUtil.send_data(self.ser, "AGITATIONS:" + str(self.agitation_var.get()))
        UARTUtil.send_data(self.ser, "CMD:RUNREACTION")

        def poll_uart():
            if not self._running:
                # This part of the logic might be simplified or removed if stopping
                # is handled exclusively by _stop_sequence, but left for safety.
                messagebox.showinfo(
                    "Info", "Reaction stopped."
                )
                return

            # If paused, skip data processing but keep the poll loop alive
            if self._paused:
                self.after(100, poll_uart)
                return

            line = UARTUtil.receive_data(self.ser)
            if line:
                if "OD:" in line:
                    print("Processing Channel ", self.data_iterator + 1)
                    print("Received line:", line, "\n")
                    try:
                        number_str = line[3:]  # Everything after "OD:"
                        number = float(number_str)
                        channel_index = self.data_iterator  # Capture current index
                        self.data[self.data_iterator].add_entry(
                            time=np.datetime64("now", "ms"),
                            optical_density=number,
                            temperature=None,  # Assuming temperature is not provided in this line
                        )

                        csv_dir = "/var/tmp/incubator/tmp_data"
                        os.makedirs(csv_dir, exist_ok=True)
                        csv_path = f"{csv_dir}/channel_{channel_index + 1}_data.csv"
                        self.data[channel_index].export_csv(csv_path)
                        print(
                            f"Exported CSV for channel {channel_index + 1} to {csv_path}"
                        )

                        self.data_iterator = (self.data_iterator + 1) % len(self.data)
                        if self.data_iterator >= 50:
                            # Reset iterator if it reaches the end
                            self.data_iterator = 0
                    except ValueError:
                        pass  # Ignore malformed numbers
            
            # Schedule next poll regardless of receiving data to keep the loop active
            self.after(100, poll_uart)

        poll_uart()

    def _stop_sequence(self):
        """Handles the logic for stopping the reaction and exporting data."""
        UARTUtil.send_data(self.ser, "CMD:CANCEL_REACTION")
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="reaction_data_")

        # Export each ReactionData object to a CSV file
        for i, rd in enumerate(self.data):
            if not rd.get_all().empty: # Only save if data exists
                filename = f"channel_{i+1}.csv"
                filepath = os.path.join(temp_dir, filename)
                rd.export_csv(filepath)

        # Create output directory if it doesn't exist
        output_dir = "/var/tmp/incubator/processedcsvs"
        os.makedirs(output_dir, exist_ok=True)

        # Create a zip archive
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"reaction_data_{timestamp}.zip"
        archive_path = os.path.join(output_dir, archive_name)

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(
                        file_path, temp_dir
                    )  # relative name inside zip
                    zipf.write(file_path, arcname)

        # Clean up temporary directory
        shutil.rmtree(temp_dir)

        # Notify user
        messagebox.showinfo("Stopped", f"All data exported to:\n{archive_path}")

    def update_plot(self, frame=None):
        # If axes don't exist or if the reaction is paused, do not update the plot
        if not hasattr(self, "ax") or self._paused:
            return

        self.ax.clear()  # Clear old plots

        selected_indices = self.get_selected_indices()
        latest_time = None  # Keep track of latest time for scrolling

        colors = plt.cm.get_cmap('tab10').colors # Use a colormap for more colors
        color_index = 0

        for idx_str in selected_indices:
            try:
                idx = int(idx_str)
                df = self.data[idx - 1].get_all()
                if df.empty or "time" not in df or "optical_density" not in df:
                    continue

                # Convert 'time' to datetime objects if needed
                if not pd.api.types.is_datetime64_any_dtype(df["time"]):
                    times = pd.to_datetime(df["time"])
                else:
                    times = df["time"]

                ods = df["optical_density"]

                self.ax.plot(
                    times,
                    ods,
                    color=colors[color_index % len(colors)],
                    linewidth=2,
                    label=f"Channel {idx}",
                )
                color_index += 1

                if not times.empty:
                    latest_time = (
                        max(latest_time, times.iloc[-1])
                        if latest_time is not None
                        else times.iloc[-1]
                    )

            except (IndexError, ValueError, KeyError, AttributeError):
                continue

        # Auto-scroll to the latest time (last 30 minutes visible)
        if latest_time is not None:
            # Ensure latest_time is a Timestamp for arithmetic
            latest_time_ts = pd.to_datetime(latest_time)
            start_time = latest_time_ts - pd.Timedelta(minutes=30)
            self.ax.set_xlim(start_time, latest_time_ts)
        
        self.ax.set_title("Optical Density vs Time")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("OD")
        self.ax.legend()
        self.ax.grid(True)
        self.fig.autofmt_xdate() # Improve date formatting
        self.fig.canvas.draw_idle()  # Refresh the plot

    def check_usb_and_copy(self):
        usb_mount_base = "/media/incubator"
        try:
            if os.path.exists(usb_mount_base):
                mounted = [os.path.join(usb_mount_base, d) for d in os.listdir(usb_mount_base)]
                mounted = [d for d in mounted if os.path.ismount(d)]

                for mount_point in mounted:
                    if mount_point != self.last_usb_path:
                        self.last_usb_path = mount_point
                        if not self._running:  # Only copy if NOT running
                            try:
                                src_dir = "/var/tmp/incubator/processedcsvs"
                                if not os.path.exists(src_dir) or not os.listdir(src_dir):
                                    continue # Nothing to copy

                                dst_dir = os.path.join(mount_point, "Incubator_Data")
                                os.makedirs(dst_dir, exist_ok=True)

                                for filename in os.listdir(src_dir):
                                    src_path = os.path.join(src_dir, filename)
                                    dst_path = os.path.join(dst_dir, filename)
                                    shutil.copy2(src_path, dst_path)

                                print(f"✅ Data copied to USB: {dst_dir}")

                                response = messagebox.askyesno(
                                    "Data Copied",
                                    "Data was successfully copied to the USB drive.\nDo you want to delete the temporary and processed data?"
                                )
                                if response:
                                    # Clean up processed data
                                    shutil.rmtree(src_dir)
                                    os.makedirs(src_dir, exist_ok=True)
                                    # Clean up temp data
                                    temp_data_dir = "/var/tmp/incubator/tmp_data"
                                    if os.path.exists(temp_data_dir):
                                        shutil.rmtree(temp_data_dir)
                                        os.makedirs(temp_data_dir, exist_ok=True)
                                    print("🗑️ Temporary and processed data deleted.")
                                else:
                                    print("⚠️ Temporary data retained.")

                                    # Move processed CSVs to a saved directory anyway
                                    saved_dir = "/var/tmp/incubator/savedcsvs"
                                    os.makedirs(saved_dir, exist_ok=True)
                                    for filename in os.listdir(src_dir):
                                        src_path = os.path.join(src_dir, filename)
                                        dst_path = os.path.join(saved_dir, filename)
                                        shutil.move(src_path, dst_path)
                                    print(f"📁 Moved processed CSVs to: {saved_dir}")

                            except Exception as e:
                                messagebox.showerror("USB Copy Error", f"Failed to copy data to USB: {e}")
                                print(f"❌ Error copying to USB: {e}")
            else:
                 self.last_usb_path = None
        except Exception as e:
            print(f"An error occurred in check_usb_and_copy: {e}")

        self.after(3000, self.check_usb_and_copy)