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
            Processes data from 10 calibration runs.

            This function should:
            1. Calculate the average voltage (x) and average optical density (y) for each data point across the 10 runs.
            2. Perform a single curve fit on these averaged data points.
            3. Calculate the standard deviation of the voltage measurements for each data point across the 10 runs to be used as error bars.

            :param data: A list of 10 runs. Each run is a list of [channel, voltage, OD] points.
            :return: Averaged channels, averaged voltages, averaged ODs, the fitted curve function, R^2, and the calculated standard deviations for the voltages.
            """
            # Ensure the data is in a consistent format (numpy array is best)
            # Shape will be (10_runs, num_points_per_run, 3_columns)
            data_np = np.array(data)

            # 1. Calculate Averages and Standard Deviations across the 10 runs
            # axis=0 averages along the "runs" dimension
            avg_voltages = np.mean(data_np[:, :, 1], axis=0)  # Average of Voltage (column 1)
            avg_ods = np.mean(data_np[:, :, 2], axis=0)       # Average of Optical Density (column 2)
            
            # This is the correct way to calculate the error bars for your horizontal (voltage) axis
            std_dev_voltages = np.std(data_np[:, :, 1], axis=0, ddof=1) # Use ddof=1 for sample stdev

            # The channels should be the same for each run
            channels = data_np[0, :, 0].tolist()

            # 2. Perform a single curve fit on the averaged data
            params, _ = curve_fit(LogFunction.log_func, avg_voltages, avg_ods)
            a, b = params
            log_fit = LogFunction(a, b)

            # 3. Compute R^2 for the fit on the averaged data
            y_pred = LogFunction.log_func(avg_voltages, a, b)
            ss_res = np.sum((avg_ods - y_pred)**2)
            ss_tot = np.sum((avg_ods - np.mean(avg_ods))**2)
            r_squared = 1 - (ss_res / ss_tot)

            # 4. Return the results
            return channels, avg_voltages.tolist(), avg_ods.tolist(), log_fit, r_squared, std_dev_voltages.tolist()