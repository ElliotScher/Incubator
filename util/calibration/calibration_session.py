import json
import os
import sys
import numpy as np
from scipy.optimize import curve_fit
import statistics

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
    
    def run_calibration(self, data):
        # Flatten the matrix into x and y arrays
        channels = []
        x = []
        y = []

        for row in data:
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
    
    def run_10_calibrations(self, data):
        """
        Runs 10 calibrations and returns the average of the results.
        :param data: The calibration data to run.
        :return: The average of the results.
        """
        results = []
        for i in range(len(data)):
            self.data = data
            result = self.run_calibration(data[i])
            results.append(result)
        
        # Average the results
        avg_channels = results[0][0]
        avg_x = np.mean([result[1] for result in results], axis=0).tolist()
        avg_y = np.mean([result[2] for result in results], axis=0).tolist()
        avg_log_func = LogFunction(np.mean([result[3].a for result in results]), 
                                   np.mean([result[3].b for result in results]))
        avg_r_squared = np.mean([result[4] for result in results])
        avg_error_bars = np.mean([result[5] for result in results], axis=0).tolist()


        adcs = []
        standard_deviations = []

        for i in range(len(results)):
            for j in range(len(results[i])):
                adcs.append(results[i][j][1])
            standard_deviations.append(statistics.stdev(adcs))
            adcs = []


        return avg_channels, avg_x, avg_y, avg_log_func, avg_r_squared, standard_deviations