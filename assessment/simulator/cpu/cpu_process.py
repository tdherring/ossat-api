import time


class CPUProcess:
    def __init__(self, name, arrival_time, burst_time):
        self.name = name
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.time_added = time.time()

    def get_name(self):
        return self.name

    def get_arrival_time(self):
        return self.arrival_time

    def get_burst_time(self):
        return self.burst_time

    def get_remaining_time(self):
        return self.remaining_time

    def set_burst_time(self, burst_time):
        self.burst_time = burst_time

    def set_remaining_time(self, remaining_time):
        self.remaining_time = remaining_time
