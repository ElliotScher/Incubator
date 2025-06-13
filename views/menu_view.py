import tkinter as tk

class MenuView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="Menu")
        label.place(relx=0, rely=0, relwidth=1, relheight=0.25)

        button = tk.Button(self, text="Calibration",
                           command=lambda: controller.show_frame("CalibrationView"))
        button.place(relx=0, rely=0.25, relwidth=1, relheight=0.25)

        button2 = tk.Button(self, text="Connection",
                            command=lambda: controller.show_frame("ConnectionView"))
        button2.place(relx=0, rely=0.5, relwidth=1, relheight=0.25)

        button3 = tk.Button(self, text="Run",
                            command=lambda: controller.show_frame("RunView"))
        button3.place(relx=0, rely=0.75, relwidth=1, relheight=0.25)