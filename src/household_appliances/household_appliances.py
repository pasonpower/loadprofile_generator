import abc
import pandas as pd
import os
import numpy as np

# TODO: use general path relative to current path
PROJECT_PATH = "/home/jielian/projects/loadprofile_generator"
data_file_name = os.path.join(PROJECT_PATH, "open_ei_residential_ev", "loadprofile_ev_l1.csv")


class HouseholdAppliance(object):
    """
    Base class representing a household appliance that output load profile give a time range
    """

    @abc.abstractmethod
    def get_load(self, start_time, end_time):
        pass

    @abc.abstractmethod
    def fetch_load_from_file(self):
        pass


class EVCharger(HouseholdAppliance):
    def __init__(self, number_ev=1, level=1):
        self.load = None
        self.number_ev = str(number_ev)
        self.load_file_path = os.path.join(PROJECT_PATH, "data/open_ei_residential_ev", f"ev_charger_l{level}.csv")
        self.fetch_load()

    def fetch_load(self):
        self.load = pd.read_csv(self.load_file_path)
        self.load["date_time"] = pd.to_datetime(self.load["date_time"])
        self.load = self.load.set_index("date_time")

    def get_load(self, start_time, end_time):
        start_time = start_time.replace(year=2010)
        end_time = end_time.replace(year=2010)
        data = self.load.loc[start_time:end_time, self.number_ev].resample("15T").mean()
        mask = data == 0
        noise = np.random.randint(0, 50, size=len(data))
        data = data + noise
        data[mask] = 0
        return data
