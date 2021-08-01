import time


class MemoryProcess:
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.time_added = time.time()

    def get_name(self):
        return self.name

    def get_size(self):
        return self.size

    def get_time_added(self):
        return self.time_added
