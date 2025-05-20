import tkinter as tk

class MenuView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="Menu")
        label.pack(pady=10)

        button = tk.Button(self, text="Calibration",
                           command=lambda: controller.show_frame("CalibrationView"))
        
        button2 = tk.Button(self, text="Connection",
                           command=lambda: controller.show_frame("ConnectionView"))
        
        button3 = tk.Button(self, text="Run",
                           command=lambda: controller.show_frame("RunView"))
        button.pack()
        button2.pack()
        button3.pack()

