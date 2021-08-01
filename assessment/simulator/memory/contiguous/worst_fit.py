from ..memory_manager import MemoryManager


class WorstFit(MemoryManager):
    def allocate_processes(self, verbose=False):
        if verbose:
            print("\nOSSAT-WorstFit\n-----------------------------------------")

        # Set all process to be unallocated(None).
        for i in range(len(self.job_queue)):
            self.allocated[self.job_queue[i].get_name()] = None

        for process in self.job_queue:
            block_counter = 0
            best_block_counter = 0
            best_block = None
            for block in self.blocks:
                # If the process fits in the block and it hasn't been allocated yet, and the next block is a worse fit.
                if (not block in self.allocated.values() and process.get_size() <= block.get_size() and (best_block == None or block.get_size() > best_block.get_size())):
                    best_block = block
                    best_block_counter = block_counter

                block_counter += 1

            self.allocated[process.get_name()] = best_block
            if (verbose and self.allocated[process.get_name()]):
                print("Process " + process.get_name() + " (" + str(process.get_size()) + ") allocated to Block " + str(best_block_counter) + " (" + str(best_block.get_size()) + ")")


# Syntax for use on frontend.

# test_worst_fit = WorstFit();

# # Create the blocks.

# test_worst_fit.create_block("b1",100);
# test_worst_fit.create_block("b2",500);
# test_worst_fit.create_block("b3",200);
# test_worst_fit.create_block("b4",300);
# test_worst_fit.create_block("b5",600);

# # Create the processes.

# test_worst_fit.create_process("p1", 212);
# test_worst_fit.create_process("p2", 417);
# test_worst_fit.create_process("p3", 112);
# test_worst_fit.create_process("p4", 426);
# test_worst_fit.allocate_processes(True);
