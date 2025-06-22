import pandas as pd

class ReactionData:
    def __init__(self, channelNumber):
        
        self.channelNumber = channelNumber
        self.data = pd.DataFrame(columns=['time', 'optical_density', 'temperature'])

    def add_entry(self, time, optical_density, temperature):
        new_entry = pd.DataFrame([{
            'time': time,
            'optical_density': optical_density,
            'temperature': temperature
        }])
        self.data = pd.concat([self.data, new_entry], ignore_index=True)

    def get_all(self):
        return self.data.copy()

    def get_latest(self):
        if not self.data.empty:
            return self.data.iloc[-1].to_dict()
        return None

    def clear(self):
        self.data = pd.DataFrame(columns=['time', 'optical_density', 'temperature'])

    def export_csv(self, filepath):
        self.data.to_csv(filepath, index=False)