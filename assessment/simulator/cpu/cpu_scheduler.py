from .cpu_process import CPUProcess
from .cpu_priority_process import CPUPriorityProcess


class CPUScheduler:
    def __init__(self):
        self.job_queue = []
        self.schedule = []
        self.ready_queue = []
        # Job and Ready Queue at each time delta(index=time delta).
        self.all_ready_queues = []
        self.all_job_queues = []

    def create_process(self, name, arrival_time, burst_time, priority=None):
        if len([process for process in self.job_queue if process.name == name]) > 0:
            print(
                "You can't have two processes with the same ID. Skipping (" + name + ", " + str(arrival_time) + ", " + str(burst_time) +
                ", " if priority is None else ", " + priority + ") and continuing silently."
            )
            return

        # If process given priority, create a PriorityProcess object(left), otherwise create a standard Process object(right).
        self.job_queue.append(CPUProcess(name, arrival_time, burst_time) if priority is None else CPUPriorityProcess(name, arrival_time, burst_time, priority))

    def remove_process(self, name):
        self.job_queue = [process for process in self.job_queue if process.name != name]

    def reset(self):
        self.job_queue = []
        self.schedule = []
        self.readyQueue = []
        self.all_ready_queues = []
        self.all_job_queues = []

    def get_schedule(self):
        return self.schedule

    def get_job_queue(self, time_delta=None):
        if time_delta:
            return self.all_job_queues[time_delta]
        return self.job_queue

    def get_ready_queue(self, time_delta=None):
        if time_delta:
            return self.all_ready_queues[time_delta]
        return self.ready_queue

    def get_all_job_queues(self):
        return self.all_job_queues

    def get_all_ready_queues(self):
        return self.all_ready_queues

    """
    Extracts all processes available at the current time delta.

    @ param job_queue The job queue to filter.
    @ param time_delta The value to check availability against.
    @ returns An array of available Processes.
    """

    def get_available_processes(self, time_delta, keep_complete_processes=False):
        if keep_complete_processes:
            return [process for process in self.job_queue if process.get_arrival_time() <= time_delta]
        return [process for process in self.job_queue if process.get_arrival_time() <= time_delta and process.get_remaining_time() > 0]

    """
    Sorts the job queue by burst time as required by SJF.
    Burst times the same? - Soonest arriving first.
    Burst and arrival times the same? - Lexicographic order, ie: a > c.

    @ param job_queue The queue to sort.
    @ return An array of Processes, sorted by burst time.
    """

    def sort_processes_by_burst_time(self, job_queue):
        return sorted(job_queue,
                      key=lambda process: (process.get_burst_time(),
                                           process.get_arrival_time(),
                                           process.get_name()))

    """
    Sorts the job queue by arrival time as required by FCFS/SJF/RR.
    Arrival times the same? - Shortest burst time first.
    Arrival and Burst times the same? - Lexicographic order, ie: a > c.

    @ param job_queue The queue to sort.
    @ return An array of Processes, sorted by arrival time.
    """

    def sort_processes_by_arrival_time(self, job_queue):
        return sorted(job_queue,
                      key=lambda process: (process.get_arrival_time(),
                                           process.get_burst_time(),
                                           process.get_name()))

    """
    Sorts the job queue by priority as required by the Priority Scheduler.
    Priorities times the same? - Soonest arriving first.
    Priorities and Arrival times the same? - Shortest burst time first.
    Priorities, Arrival, and Burst times the same? - Lexicographic order, ie: a > c.

    @ param job_queue The queue to sort.
    @ return An array of Processes, sorted by priority.
    """

    def sort_processes_by_priority(self, job_queue):
        return sorted(job_queue,
                      key=lambda process: (process.get_priority(),
                                           process.get_arrival_time(),
                                           process.get_burst_time(),
                                           process.get_name()))

    """
    Sorts the job queue by arrival time as required by SRTF
    Remaining times the same? - Soonest arriving first.
    Remaining and Arrival times the same? - Shortest burst time first.
    Remaining, Arrival, and Burst times the same? - Lexicographic order, ie: a > c.

    @ param job_queue The queue to sort.
    @ return An array of Processes, sorted by remaining time.
    """

    def sort_processes_by_remaining_time(self, job_queue):
        return sorted(job_queue,
                      key=lambda process: (process.get_remaining_time(),
                                           process.get_arrival_time(),
                                           process.get_burst_time(),
                                           process.get_name()))

    """
    Outputs a graphical representation of the schedule.
    Primarily for visualization during testing.

    Example of an FCFS schedule:

    0   1   2       5     7           12       16
    | - | - | - - - | - - | - - - - - | - - - - |
    p2         p3      p1      p4         p5

    """

    def output_graphical_representation(self):
        timing_str = ""
        schedule_str = ""
        process_str = ""
        for i in range(len(self.schedule)):
            time_delta = self.schedule[i]["time_delta"]
            burst_time = self.schedule[i]["burst_time"]
            process_name = self.schedule[i]["process_name"]
            timing_str += str(time_delta)
            schedule_str += "|"
            for j in range(burst_time):
                schedule_str += " - "
                timing_str += "   "

            timing_str = timing_str[0:len(timing_str) + 1 - len(str(time_delta))]
            for j in range(burst_time * 3):
                if j == burst_time * 3 // 2:
                    if process_name == "IDLE":
                        process_str += "  "
                    else:
                        process_str += process_name
                else:
                    process_str += " "
        timing_str += str(time_delta + burst_time)
        schedule_str += "|"
        print("\n" + timing_str)
        print(schedule_str)
        print(process_str)
