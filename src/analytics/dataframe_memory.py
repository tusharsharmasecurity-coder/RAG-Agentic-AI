import pandas as pd


class DataFrameMemory:

    def __init__(self):
        self.df = None

    def save(self, dataframe: pd.DataFrame):
        self.df = dataframe

    def get(self):
        return self.df

    def clear(self):
        self.df = None


# Global instance
dataframe_memory = DataFrameMemory()
