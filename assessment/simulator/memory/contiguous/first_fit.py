from ..memory_manager import MemoryManager


class FirstFit(MemoryManager):
    def allocate_processes(self, verbose=False):
        if verbose:
            print("\nOSSAT-FirstFit\n-----------------------------------------")

        # Set all process to be unallocated (null).
        for i in range(len(self.job_queue)):
            self.allocated[self.job_queue[i].get_name()] = None

        for process in self.job_queue:
            block_counter = 0
            for block in self.blocks:
                if (not block in self.allocated.values() and process.get_size() <= block.get_size()):
                    self.allocated[process.get_name()] = block
                    break

                block_counter += 1

            if verbose and self.allocated[process.get_name()]:
                print("Process " + process.get_name() + " (" + str(process.get_size()) + ") allocated to Block " + str(block_counter) + " (" + str(self.allocated[process.get_name()].get_size()) + ")")


# Syntax for use on frontend.

# test_first_fit = FirstFit()

# # Create the blocks.

# test_first_fit.create_block("b1", 100)
# test_first_fit.create_block("b2", 500)
# test_first_fit.create_block("b3", 200)
# test_first_fit.create_block("b4", 300)
# test_first_fit.create_block("b5", 600)

# # Create the processes.

# test_first_fit.create_process("p1", 212)
# test_first_fit.create_process("p2", 417)
# test_first_fit.create_process("p3", 112)
# test_first_fit.create_process("p4", 426)
# test_first_fit.allocate_processes(True)
