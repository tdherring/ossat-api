from .non_preepmtive_scheduler import NonPreemptiveScheduler
from copy import deepcopy


class SJF(NonPreemptiveScheduler):

    """
    Generates a SJF schedule for a set of input processes.

    @param verbose Show debugging information?
    """

    def dispatch_processes(self, verbose=False):
        if verbose:
            print("\nOSSAT-SJF\n-----------------------------------------")
        self.job_queue = self.sort_processes_by_burst_time(self.job_queue)
        time_delta = 0
        i = 0
        last_p, p, name, arrival_time, remaining_time = None, None, None, None, None

        # Keep scheduling until all processes have no remaining execution time.
        while (len([process for process in self.job_queue if process.get_remaining_time() != 0]) > 0):
            self.update_ready_queue(time_delta, remaining_time)
            # Clone the process so it is not affected by changes to the true process object.
            self.all_ready_queues.append(deepcopy(self.ready_queue))
            self.all_job_queues.append(deepcopy(self.job_queue))

            # If the ready queue has no processes, we need to wait until one becomes available.
            if (len(self.get_available_processes(time_delta)) == 0):
                if verbose:
                    print("[" + str(time_delta) + "] CPU Idle...")
                self.schedule.append({"process_name": "IDLE", "time_delta": time_delta, "arrival_time": None, "burst_time": 0, "remaining_time": None})
                while True:
                    self.update_ready_queue(time_delta, remaining_time)
                    if (len(self.get_available_processes(time_delta)) > 0):
                        break
                    # Don't increment the burst time / time delta if the ready queue now has something in it.
                    self.schedule[len(self.schedule) - 1]["burst_time"] += 1
                    time_delta += 1
                    self.all_ready_queues.append(deepcopy(self.ready_queue))
                    self.all_job_queues.append(deepcopy(self.job_queue))

            if not remaining_time or remaining_time == 1:
                p = self.ready_queue[i]
                name = p.get_name()
                arrival_time = p.get_arrival_time()

            remaining_time = p.get_remaining_time()

            # If the process has changed since the last iteration, the previous process has ran to completion.
            if last_p != p or last_p == None:
                # Inform the user of the newly spawned process.
                if verbose:
                    print("[" + str(time_delta) + "] Spawned Process", name)
                # Add it to the schedule.
                self.schedule.append({"process_name": name, "time_delta": time_delta, "arrival_time": arrival_time, "burst_time": 0, "remaining_time": remaining_time})

            # Continue to increment the burst time of self process as long as it has execution time remaining.
            if remaining_time > 0:
                p.set_remaining_time(remaining_time - 1)
                self.schedule[len(self.schedule) - 1]["burst_time"] += 1
                self.schedule[len(self.schedule) - 1]["remaining_time"] -= 1

            last_p = p
            # Increment time delta to track execution progress.
            time_delta += 1

            # If the burst time is 0 the process has finished executing.
            if p.get_remaining_time() == 0:
                if verbose:
                    print("[" + str(time_delta) + "] Process", name, "finished executing!")
                i += 1

            # Add the final job and ready queue states.
            if len([process for process in self.job_queue if process.get_remaining_time() != 0]) == 0:
                self.all_ready_queues.append(deepcopy(self.ready_queue))
                self.all_job_queues.append(deepcopy(self.job_queue))

    """
    Updates the ready queue to be in the correct order for SJF.
    
    @param timeDelta Time point in execution.
    @param remainingTime Execution time remaining for current process.
    """

    def update_ready_queue(self, time_delta, remaining_time):
        available_processes = self.get_available_processes(time_delta, True)
        for j in range(len(available_processes)):
            if not any(process.get_name() == available_processes[j].get_name() for process in self.ready_queue) and (not remaining_time or remaining_time == 1):
                self.ready_queue.append(available_processes[j])
                break


# Syntax for use on frontend.
# test_sjf = SJF()

# test_sjf.create_process("p1", 2, 1)
# test_sjf.create_process("p2", 1, 5)
# test_sjf.create_process("p3", 4, 1)
# test_sjf.create_process("p4", 1, 6)
# test_sjf.create_process("p5", 2, 3)

# test_sjf.dispatch_processes(True)
# test_sjf.output_graphical_representation()
