import tkinter as tk

class RunView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = tk.Label(self, text="Run")
        label.pack(pady=10)

        button = tk.Button(self, text="Home",
                           command=lambda: controller.show_frame("MenuView"))
        button.pack()
