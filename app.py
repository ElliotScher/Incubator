import tkinter as tk
from views.menu_view import MenuView
from views.calibration_view import CalibrationView
from views.connection_view import ConnectionView
from views.run_view import RunView

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cam's Project")
        self.minsize(1920, 1080)
        self.maxsize(1920, 1080)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)  # Make container fill the window

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (MenuView, CalibrationView, ConnectionView, RunView):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")  # Make frames expand

        self.show_frame("MenuView")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
