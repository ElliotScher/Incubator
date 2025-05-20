import tkinter as tk
from views.menu_view import MenuView
from views.calibration_view import CalibrationView
from views.connection_view import ConnectionView
from views.run_view import RunView

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cam's Project")
        self.geometry("800x600")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}

        for F in (MenuView, CalibrationView, ConnectionView, RunView):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MenuView")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
