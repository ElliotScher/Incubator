import tkinter as tk

class CalibrationView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="Calibration")
        label.pack(pady=10)

        button = tk.Button(self, text="Home",
                           command=lambda: controller.show_frame("MenuView"))
        button.pack()
