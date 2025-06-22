import math

class LogarithmicCalibrationCurve:
    @staticmethod
    def init(self, a: float, b: float):
        self.a = a
        self.b = b

    @staticmethod
    def evaluate(self, x: float) -> float:
        return self.a * math.log10(x) + self.b