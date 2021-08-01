from .cpu_process import CPUProcess


class CPUPriorityProcess(CPUProcess):
    def __init__(self, name, arrival_time, burst_time, priority):
        super(CPUPriorityProcess, self).__init__(name, arrival_time, burst_time)
        self.priority = priority

    def get_priority(self):
        return self.priority
