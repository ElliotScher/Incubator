import json
import os
import sys
import numpy as np
from scipy.optimize import curve_fit

class LogFunction:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    @staticmethod
    def log_func(x, a, b):
        return a * np.log(x) + b

class CalibrationSession:
    def __init__(self, table):
        # This is a 2d array of cells. The inner arrays are arrays of 3 elements, representing the machine channel, the OD measurement, and the corresponding voltage
        self.data = table

    @staticmethod        
    def run_test_json_calibration():
        try:
            base_path = sys._MEIPASS  # PyInstaller sets this at runtime
        except AttributeError:
            base_path = os.path.abspath(".")

        path = os.path.join(base_path, 'util/calibration/test_calibration.json')
        with open(path, 'r') as f:
            obj = json.load(f)
        matrix = obj.get("matrix")
        

        # Flatten the matrix into x and y arrays
        channels = []
        x = []
        y = []
        
        for row in matrix:
            if (row[1] != 0 and row[1] is not None):
                channels.append(row[0])
                x.append(row[1])
                y.append(row[2])

        params, _ = curve_fit(LogFunction.log_func, x, y)
        a, b = params
        
        return channels, x, y, LogFunction(a, b)