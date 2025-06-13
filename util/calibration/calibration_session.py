import json
import os
import sys
import numpy as np
from scipy.optimize import curve_fit

class ExpFunction:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    @staticmethod
    def exp_func(x, a, b):
        return a * np.exp(x) + b
        # For base-10 instead of base-e, use:
        # return a * np.power(10, x) + b

class CalibrationSession:
    def __init__(self, table):
        # This is a 2D array of cells. The inner arrays are arrays of 3 elements:
        # [channel, voltage, optical density]
        self.data = table

    def run_calibration(self):
        channels = []
        x = []  # Optical density
        y = []  # Voltage

        for row in self.data:
            if row[1] != 0 and row[1] is not None:
                channels.append(row[0])
                x.append(row[2])  # OD
                y.append(row[1])  # Voltage

        x = np.array(x)
        y = np.array(y)

        params, _ = curve_fit(ExpFunction.exp_func, x, y)
        a, b = params

        # Compute R^2
        y_pred = ExpFunction.exp_func(x, a, b)
        residuals = y - y_pred
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot)

        return channels, x.tolist(), y.tolist(), ExpFunction(a, b), r_squared

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

        channels = []
        x = []
        y = []

        for row in matrix:
            if row[1] != 0 and row[1] is not None:
                channels.append(row[0])
                x.append(row[2])  # OD
                y.append(row[1])  # Voltage

        x = np.array(x)
        y = np.array(y)

        params, _ = curve_fit(ExpFunction.exp_func, x, y)
        a, b = params

        y_pred = ExpFunction.exp_func(x, a, b)
        residuals = y - y_pred
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot)

        return channels, x.tolist(), y.tolist(), ExpFunction(a, b), r_squared
