from .preemptive_scheduler import PreemptiveScheduler
from copy import deepcopy


class RR(PreemptiveScheduler):
    def __init__(self, time_quantum=2):
        super(RR, self).__init__()
        self.time_quantum = time_quantum

    def set_time_quantum(self, time_quantum):
        self.time_quantum = time_quantum

    """
    Generates a RR schedule for a set of input processes.

    @ param verbose Show debugging information?
    """

    def dispatch_processes(self, verbose=False):
        if verbose:
            print("\nOSSAT-RR\n-----------------------------------------")
        self.job_queue = self.sort_processes_by_arrival_time(self.job_queue)
        time_delta = 0
        i = 0

        available_processes = self.get_available_processes(time_delta)

        if (len(available_processes) > 0):
            # If processes are available from time delta 0.
            # Initialise the ready queue to hold all processes which are available at self time delta (0).
            self.ready_queue = self.get_available_processes(time_delta)
        else:
            # Otherwise, we need to idle at the first iteration, so set the first item in the ready queue to the process which arrives quickest.
            self.ready_queue.append(self.job_queue[0])

        # Clone the process so it is not affected by changes to the true process object.
        self.all_ready_queues.append(deepcopy(self.ready_queue))
        self.all_job_queues.append(deepcopy(self.job_queue))

        # Keep scheduling until all processes have no burst time left.
        while (len([process for process in self.job_queue if process.get_remaining_time() != 0]) > 0):
            p = self.ready_queue[i]
            name = p.get_name()
            arrival_time = p.get_arrival_time()
            remaining_time = p.get_remaining_time()

            # Check whether the CPU needs to idle for the next process.
            if (arrival_time > time_delta):
                if verbose:
                    print("[" + str(time_delta) + "] CPU Idle...")
                self.schedule.append({"process_name": "IDLE", "time_delta": time_delta, "arrival_time": None, "burst_time": arrival_time - time_delta, "remaining_time": None})
                # Update queues arrays in line with idle time.
                for j in range(arrival_time - time_delta):
                    self.all_ready_queues.append(deepcopy(self.ready_queue))
                    self.all_job_queues.append(deepcopy(self.job_queue))

                # Adjust time delta with respect to idle length.
                time_delta += arrival_time - time_delta

            # Track how much to adjust the time delta.
            delta_increment = 0

            # If the process has time left to execute.
            if (remaining_time > 0):
                if verbose:
                    print("[" + str(time_delta) + "] Spawned Process", name)

                if (remaining_time <= self.time_quantum):
                    # The process will run to completion quicker than a full quantum.
                    delta_increment = remaining_time
                else:
                    # A full quantum won't run the process to completion.
                    delta_increment = self.time_quantum

                # Decrement remaining time as required and update queues arrays.
                for j in range(delta_increment):
                    p.set_remaining_time(p.get_remaining_time() - 1)
                    if (j < delta_increment - 1):
                        self.all_ready_queues.append(deepcopy(self.ready_queue))
                        self.all_job_queues.append(deepcopy(self.job_queue))

                # Increment the queue head pointer.
                i += 1

                self.schedule.append({"process_name": name, "time_delta": time_delta, "arrival_time": arrival_time, "burst_time": delta_increment, "remaining_time": remaining_time - delta_increment})
                time_delta += delta_increment
                if verbose:
                    print("[" + str(time_delta) + "] Process", name, "finished executing!")

            # Find all processes which are available at self timestep (diff the arrays).
            newly_available = [process for process in self.get_available_processes(time_delta) if process not in self.get_available_processes(time_delta - delta_increment)]

            # If after self quantum there are new processes available, add the the front of the ready queue.
            if (len(newly_available) > 0):
                self.ready_queue = self.ready_queue + newly_available

            # If the process still has execution time remaining after self quantum, add it to the end of the ready queue.
            if (p.get_remaining_time() > 0):
                self.ready_queue.append(p)

            # Finally, if the readyQueue is "empty", add the process with the nearest arrival time which has execution time remaining.
            if (len(self.ready_queue) - 1 < i):
                sorted_by_arrival = self.sort_processes_by_arrival_time([process for process in self.job_queue if process.remaining_time > 0])
                if len(sorted_by_arrival) > 0:
                    self.ready_queue.append(sorted_by_arrival[0])

            self.all_ready_queues.append(deepcopy(self.ready_queue))
            self.all_job_queues.append(deepcopy(self.job_queue))


# Syntax for use on frontend.

# test_rr = RR(3)

# test_rr.create_process("p1", 1, 8)
# test_rr.create_process("p2", 5, 2)
# test_rr.create_process("p3", 1, 7)
# test_rr.create_process("p4", 6, 3)
# test_rr.create_process("p5", 8, 5)

# test_rr.dispatch_processes(True)
# test_rr.output_graphical_representation()
