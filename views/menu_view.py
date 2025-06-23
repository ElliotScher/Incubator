import tkinter as tk


class MenuView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_rowconfigure((0, 1), weight=1)
        self.grid_columnconfigure((0, 1), weight=1)

        label = tk.Label(self, text="Menu", font=("Arial", 56))
        label.grid(row=0, column=0, sticky="nsew")

        button = tk.Button(
            self,
            text="Calibration",
            font=("Arial", 56),
            command=lambda: controller.show_frame("CalibrationView"),
        )
        button.grid(row=0, column=1, sticky="nsew")

        button2 = tk.Button(
            self,
            text="Connection",
            font=("Arial", 56),
            command=lambda: controller.show_frame("ConnectionView"),
        )
        button2.grid(row=1, column=0, sticky="nsew")

        button3 = tk.Button(
            self,
            text="Run",
            font=("Arial", 56),
            command=lambda: controller.show_frame("RunView"),
        )
        button3.grid(row=1, column=1, sticky="nsew")
