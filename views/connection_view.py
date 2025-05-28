import tkinter as tk
class ConnectionView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="Connection")
        label.pack(pady=10)

        homeButton = tk.Button(self, text="Home",
                           command=lambda: controller.show_frame("MenuView"))
        homeButton.pack()

        pingButton = tk.Button(self, text="Ping", command=lambda: self.ping_devices())
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

    def ping_devices(self):
        # Ping UART and Gazoscan
        UART_CONNECTED = False
        GAZOSCAN_CONNECTED = False
        self.update_status(UART_CONNECTED, GAZOSCAN_CONNECTED)

    def update_status(self, uart_connected, Gazoscan_connected):
        self.uart_status.config(fg="green" if uart_connected else "gray")
        self.Gazoscan_status.config(fg="green" if Gazoscan_connected else "gray")