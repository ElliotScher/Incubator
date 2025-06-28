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
        return a * np.log10(x) + b

class CalibrationSession:
    def __init__(self, table):
        # This is a 2d array of cells. The inner arrays are arrays of 3 elements,
        # representing the machine channel, the voltage measurement, and the optical density measurement.
        self.data = table
        self.cal_data = []

    def run_calibration(self):
        # Flatten the matrix into x and y arrays
        channels = []
        x = []
        y = []

        for row in self.data:
            if (row[1] != 0 and row[1] is not None):
                channels.append(row[0])
                x.append(row[1])
                y.append(row[2])

        x = np.array(x)
        y = np.array(y)

        params, _ = curve_fit(LogFunction.log_func, x, y)
        a, b = params

        # Compute R^2
        y_pred = LogFunction.log_func(x, a, b)
        residuals = y - y_pred  # These are signed residuals
        abs_residuals = np.abs(residuals)  # absolute residuals for error bars

        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot)

        # Return residuals or absolute residuals as error bars
        return channels, x.tolist(), y.tolist(), LogFunction(a, b), r_squared, abs_residuals.tolist()
    
    def add_calibration_data(self, channel, voltage, optical_density):
        self.cal_data.append([channel, voltage, optical_density])
    
    def run_10_calibrations(self):
        # Run the calibration 10 times and return the results
        for _ in range(self.cal_data):
            result = self.run_calibration()
            self.cal_data.append(result)
        
        # Aggregate the self.cal_data
        channels = self.cal_data[0][0]
        x = np.array([result[1] for result in self.cal_data])
        y = np.array([result[2] for result in self.cal_data])
        log_func_params = [result[3] for result in self.cal_data]
        r_squared_values = [result[4] for result in self.cal_data]
        error_bars = np.array([result[5] for result in self.cal_data])

        # Average the parameters and R^2 values
        avg_a = np.mean([log_func.a for log_func in log_func_params])
        avg_b = np.mean([log_func.b for log_func in log_func_params])
        avg_r_squared = np.mean(r_squared_values)

        # Return aggregated self.cal_data
        return channels, x.tolist(), y.tolist(), LogFunction(avg_a, avg_b), avg_r_squared, error_bars.tolist()