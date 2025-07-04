import time
import tkinter as tk
from util.uart_util import UARTUtil


class ConnectionView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.ser = UARTUtil.open_port()

        label = tk.Label(self, text="Connection")
        label.pack(pady=10)

        homeButton = tk.Button(
            self, text="Home", command=lambda: controller.show_frame("MenuView")
        )
        homeButton.pack()

        pingButton = tk.Button(self, text="Ping", command=lambda: [self.ping_devices()])
        pingButton.pack()

        # Create checkmark labels for UART and Gazoscan connectivity
        self.uart_status = tk.Label(self, text="✔", font=("Arial", 48), fg="gray")
        self.uart_status.pack(pady=5)
        self.uart_status_label = tk.Label(self, text="UART")
        self.uart_status_label.pack()

        self.Gazoscan_status = tk.Label(self, text="✔", font=("Arial", 48), fg="gray")
        self.Gazoscan_status.pack(pady=5)
        self.Gazoscan_status_label = tk.Label(self, text="Gazoscan")
        self.Gazoscan_status_label.pack()

    def send_arduino_state_transition(self):
        # Send state transition command to Arduino
        try:
            UARTUtil.send_data(self.ser, data="CMD:TESTCONNECTION")
            print("State transition command sent to Arduino.")
        except Exception as e:
            print(f"Failed to send state transition command: {e}")

    def ping_UART(self):
        # Ping UART device
        try:
            response = UARTUtil.receive_data(ser=self.ser)
            UART_CONNECTED = "ping" in response.lower()
        except Exception as e:
            print(f"UART ping failed: {e}")
            UART_CONNECTED = False
        return UART_CONNECTED

    def ping_devices(self):
        # Ping UART and Gazoscan
        GAZOSCAN_CONNECTED = False
        self.send_arduino_state_transition()
        self.update_status(self.ping_UART(), GAZOSCAN_CONNECTED)

    def update_status(self, uart_connected, Gazoscan_connected):
        self.uart_status.config(fg="green" if uart_connected else "gray")
        self.Gazoscan_status.config(fg="green" if Gazoscan_connected else "gray")
