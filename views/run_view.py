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
    _first_check_done = False # Class attribute to ensure check runs only once

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.canvas = None
        self.ser = UARTUtil.open_port()

        self.data = [ReactionData(i) for i in range(50)]
        self.data_iterator = 0

        self._running = False
        self._paused = False
        self.arduino_paused_ack = False

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

        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill="both", expand=True)

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

        self.update_idletasks()
        total_width = self.winfo_width() or 800
        left_frame.config(width=int(total_width * 0.25))
        left_frame.pack_propagate(False)

        for i in range(50):
            self.tree.insert("", "end", values=("[ ]", i + 1))

        self.tree.bind("<Button-1>", self.on_click)

        button_frame = tk.Frame(self)
        button_frame.pack(side="top", anchor="e", pady=10)

        right_frame = tk.Frame(self)
        right_frame.pack(side="left", fill="both", expand=True)

        from matplotlib.animation import FuncAnimation

        plot_frame = tk.Frame(right_frame)
        plot_frame.pack(fill="both", expand=True)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.animation = FuncAnimation(self.fig, self.update_plot, interval=500)

        agitation_frame = tk.Frame(button_frame)
        agitation_frame.pack(side="left", padx=10)

        tk.Label(agitation_frame, text="Agitations:", font=("Arial", 10)).pack()
        self.agitation_var = tk.IntVar(value=5)
        agitation_entry = tk.Entry(
            agitation_frame, textvariable=self.agitation_var, width=5
        )
        agitation_entry.pack()

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

        self.play_pause_button = tk.Button(
            button_frame,
            text="Pause",
            font=("Arial", 12, "bold"),
            width=8,
            height=2,
            command=self.toggle_pause,
            state="disabled"
        )
        self.play_pause_button.pack(side="left", padx=5)

        self.action_button = tk.Button(
            button_frame,
            text="Export Final Data",
            font=("Arial", 12, "bold"),
            width=16,
            height=2,
            command=self.export_final_data
        )
        self.action_button.pack(side="left", padx=10)

        # Trigger the one-time check for recovered data
        if not RunView._first_check_done:
            self.after(100, self._check_for_recovered_data)

    def _check_for_recovered_data(self):
        """Checks for leftover data from a failed run, runs only once."""
        RunView._first_check_done = True  # Mark as done immediately
        temp_dir = "/var/tmp/incubator/tmp_data"

        try:
            if os.path.exists(temp_dir) and os.listdir(temp_dir):
                response = messagebox.askyesno(
                    "Recover Data",
                    "Warning: Incomplete reaction data found, likely from a power failure.\n\n"
                    "Do you want to recover this data now?\n\n"
                    "(If you choose 'No', this data will be permanently deleted.)"
                )
                if response:
                    self._recover_data_to_usb()
                else:
                    self._clear_temp_data()
                    messagebox.showinfo("Data Discarded", "The incomplete reaction data has been deleted.")
        except Exception as e:
            messagebox.showerror("Recovery Check Error", f"An error occurred while checking for recovered data: {e}")

    def _recover_data_to_usb(self):
        """Guides the user to save recovered data to a USB drive."""
        messagebox.showinfo("Insert USB", "Please insert a USB drive, then click OK to recover the data.")

        usb_mount_base = "/media/incubator"
        mounted_drives = []
        try:
            if os.path.exists(usb_mount_base):
                mounted_drives = [os.path.join(usb_mount_base, d) for d in os.listdir(usb_mount_base) if os.path.ismount(os.path.join(usb_mount_base, d))]
        except Exception as e:
            messagebox.showerror("USB Error", f"An error occurred while searching for USB drives: {e}")
            return

        if not mounted_drives:
            messagebox.showerror("USB Not Found", "No USB drive was detected. The recovered data could not be saved.")
            return

        mount_point = mounted_drives[0]

        try:
            temp_dir = "/var/tmp/incubator/tmp_data"
            dst_dir = os.path.join(mount_point, "Incubator_Data_Recovered")
            os.makedirs(dst_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"recovered_data_{timestamp}.zip"
            local_archive_path = os.path.join(tempfile.gettempdir(), archive_name)

            with zipfile.ZipFile(local_archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, temp_dir))

            shutil.copy2(local_archive_path, dst_dir)
            os.remove(local_archive_path)

            messagebox.showinfo("Recovery Successful", f"Recovered data successfully saved to:\n{dst_dir}")
            self._clear_temp_data()
        except Exception as e:
            messagebox.showerror("Recovery Error", f"An error occurred during the recovery process: {e}")

    def _clear_temp_data(self):
        """Safely removes and recreates the temporary data directory."""
        temp_dir = "/var/tmp/incubator/tmp_data"
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)
            print(f"Directory {temp_dir} has been cleared.")
        except Exception as e:
            print(f"Error clearing temp data: {e}")

    def toggle_reaction(self):
        if not self._running:
            self._running = True
            self._paused = False
            self.arduino_paused_ack = False
            self.run_stop_button.config(text="Stop", bg="red")
            self.play_pause_button.config(state="normal", text="Pause")
            self.action_button.config(text="Export Partial Data", command=self.start_partial_export)
            self._start_sequence()
        else:
            self._running = False
            self._paused = False
            self.run_stop_button.config(text="Run", bg="green")
            self.play_pause_button.config(state="disabled", text="Pause")
            self.action_button.config(text="Export Final Data", command=self.export_final_data)
            self._stop_sequence()

    def toggle_pause(self):
        if not self._running: return
        self._paused = not self._paused
        if self._paused: UARTUtil.send_data(self.ser, "CMD:PAUSE_REACTION")
        else: UARTUtil.send_data(self.ser, "CMD:RESUME_REACTION")

    def start_partial_export(self):
        self.action_button.config(state="disabled")
        self.play_pause_button.config(state="disabled")
        messagebox.showinfo("Exporting", "Pausing reaction to export partial data. The process will resume automatically.")
        UARTUtil.send_data(self.ser, "CMD:PAUSE_REACTION")
        print("Sent PAUSE command for partial export.")
        self._poll_partial_export_status("waiting_for_pause")

    def _poll_partial_export_status(self, current_state):
        if current_state == "waiting_for_pause":
            if self.arduino_paused_ack:
                print("Pause acknowledged. Starting file operations.")
                self._do_partial_export_files()
                self._poll_partial_export_status("resuming_reaction")
            else:
                self.after(200, self._poll_partial_export_status, "waiting_for_pause")
        elif current_state == "resuming_reaction":
            UARTUtil.send_data(self.ser, "CMD:RESUME_REACTION")
            print("Sent RESUME command after partial export.")
            self._poll_partial_export_status("waiting_for_resume")
        elif current_state == "waiting_for_resume":
            if not self.arduino_paused_ack:
                print("Resume acknowledged. Partial export complete.")
                self.action_button.config(state="normal")
                self.play_pause_button.config(state="normal")
                messagebox.showinfo("Export Complete", "Partial data exported. Reaction has resumed.")
            else:
                self.after(200, self._poll_partial_export_status, "waiting_for_resume")

    def _do_partial_export_files(self):
        try:
            src_dir = "/var/tmp/incubator/tmp_data"
            if not os.path.exists(src_dir) or not os.listdir(src_dir):
                messagebox.showwarning("No Data", "No temporary data found to export.")
                return

            usb_mount_base = "/media/incubator"
            mounted_drives = [os.path.join(usb_mount_base, d) for d in os.listdir(usb_mount_base) if os.path.ismount(os.path.join(usb_mount_base, d))]
            if not mounted_drives:
                messagebox.showerror("USB Not Found", "No USB drive detected. Export failed.")
                return

            mount_point = mounted_drives[0]
            dst_dir = os.path.join(mount_point, "Incubator_Data_Recovered")
            os.makedirs(dst_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"reaction_data_PARTIAL_{timestamp}.zip"
            local_archive_path = os.path.join(tempfile.gettempdir(), archive_name)

            with zipfile.ZipFile(local_archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(src_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, src_dir))

            shutil.copy2(local_archive_path, dst_dir)
            print(f"Copied partial data to {os.path.join(dst_dir, archive_name)}")
            os.remove(local_archive_path)
            print(f"Deleted local temporary zip file: {local_archive_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during partial export: {e}")

    def export_final_data(self):
        src_dir = "/var/tmp/incubator/processedcsvs"
        if not os.path.exists(src_dir) or not os.listdir(src_dir):
            messagebox.showinfo("No Data", "There is no processed data available to export.")
            return

        usb_mount_base = "/media/incubator"
        mounted_drives = []
        try:
            if os.path.exists(usb_mount_base):
                mounted_drives = [os.path.join(usb_mount_base, d) for d in os.listdir(usb_mount_base) if os.path.ismount(os.path.join(usb_mount_base, d))]
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while searching for USB drives: {e}")
            return

        if not mounted_drives:
            messagebox.showerror("USB Not Found", "No USB drive detected. Please insert a USB drive and try again.")
            return

        mount_point = mounted_drives[0]
        try:
            dst_dir = os.path.join(mount_point, "Incubator_Data")
            os.makedirs(dst_dir, exist_ok=True)
            for filename in os.listdir(src_dir):
                shutil.copy2(os.path.join(src_dir, filename), dst_dir)
            
            print(f"Successfully copied final data to {dst_dir}.")
            
            print(f"Cleaning processed data directory: {src_dir}")
            shutil.rmtree(src_dir)
            os.makedirs(src_dir, exist_ok=True)
            
            temp_data_dir = "/var/tmp/incubator/tmp_data"
            if os.path.exists(temp_data_dir):
                print(f"Cleaning temporary data directory: {temp_data_dir}")
                shutil.rmtree(temp_data_dir)
                os.makedirs(temp_data_dir, exist_ok=True)

            messagebox.showinfo(
                "Export Successful",
                f"Data successfully copied to {dst_dir}.\n\nAll temporary and processed data have been cleaned from the device."
            )
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during the export process: {e}")

    def on_click(self, event):
        if self.tree.identify("region", event.x, event.y) != "cell": return
        row_id = self.tree.identify_row(event.y)
        if self.tree.identify_column(event.x) != "#1": return
        current = self.tree.set(row_id, "Selected")
        self.tree.set(row_id, "Selected", "[x]" if current.strip() == "[ ]" else "[ ]")

    def get_selected_indices(self):
        return [self.tree.set(item, "Index") for item in self.tree.get_children() if self.tree.set(item, "Selected") == "[x]"]

    def _start_sequence(self):
        # Before starting, ensure temp data is clear
        self._clear_temp_data() 
        for rd in self.data: rd.clear()
        self.data_iterator = 0
        UARTUtil.send_data(self.ser, "AGITATIONS:" + str(self.agitation_var.get()))
        UARTUtil.send_data(self.ser, "CMD:RUNREACTION")
        self.poll_uart()

    def poll_uart(self):
        if not self._running: return
        line = UARTUtil.receive_data(self.ser)
        if line:
            if "PAUSE SUCCESSFUL" in line:
                self.arduino_paused_ack = True
                self.play_pause_button.config(text="Play")
            elif "RESUME SUCCESSFUL" in line:
                self.arduino_paused_ack = False
                self.play_pause_button.config(text="Pause")
            elif "OD:" in line and not self.arduino_paused_ack:
                try:
                    self.data[self.data_iterator].add_entry(
                        time=np.datetime64("now", "ms"),
                        optical_density=float(line[3:]),
                        temperature=None
                    )
                    csv_dir = "/var/tmp/incubator/tmp_data"
                    os.makedirs(csv_dir, exist_ok=True)
                    self.data[self.data_iterator].export_csv(f"{csv_dir}/channel_{self.data_iterator + 1}_data.csv")
                    self.data_iterator = (self.data_iterator + 1) % len(self.data)
                except (ValueError, IndexError): pass
        self.after(100, self.poll_uart)

    def _stop_sequence(self):
        UARTUtil.send_data(self.ser, "CMD:CANCEL_REACTION")
        temp_dir = tempfile.mkdtemp(prefix="reaction_data_")
        for i, rd in enumerate(self.data):
            if not rd.get_all().empty:
                rd.export_csv(os.path.join(temp_dir, f"channel_{i+1}.csv"))
        output_dir = "/var/tmp/incubator/processedcsvs"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join(output_dir, f"reaction_data_{timestamp}.zip")
        if os.listdir(temp_dir):
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, temp_dir))
            messagebox.showinfo("Reaction Stopped", f"Reaction data processed and ready for export.")
        shutil.rmtree(temp_dir)

    def update_plot(self, frame=None):
        if not hasattr(self, "ax") or self.arduino_paused_ack: return
        self.ax.clear()
        selected_indices = self.get_selected_indices()
        latest_time = None
        colors = plt.cm.get_cmap('tab10').colors
        for i, idx_str in enumerate(selected_indices):
            try:
                df = self.data[int(idx_str) - 1].get_all()
                if not df.empty and "time" in df and "optical_density" in df:
                    times = pd.to_datetime(df["time"])
                    self.ax.plot(times, df["optical_density"], color=colors[i % len(colors)], linewidth=2, label=f"Channel {idx_str}")
                    if not times.empty: latest_time = max(latest_time, times.iloc[-1]) if latest_time else times.iloc[-1]
            except (IndexError, ValueError): continue
        if latest_time: self.ax.set_xlim(pd.to_datetime(latest_time) - pd.Timedelta(minutes=30), pd.to_datetime(latest_time))
        self.ax.set_title("Optical Density vs Time")
        self.ax.set_xlabel("Time"); self.ax.set_ylabel("OD")
        self.ax.legend(); self.ax.grid(True); self.fig.autofmt_xdate(); self.fig.canvas.draw_idle()