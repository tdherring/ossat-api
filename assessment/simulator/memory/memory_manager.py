from .memory_block import MemoryBlock
from .memory_process import MemoryProcess


class MemoryManager:
    def __init__(self):
        self.job_queue = []
        self.blocks = []
        self.allocated = {}

    def create_block(self, name, size):
        self.blocks.append(MemoryBlock(name, size))

    def create_process(self, name, size):
        if len([process for process in self.job_queue if process.name == name]) > 0:

            print("You can't have two processes with the same ID. Skipping (" + name + ", " + str(size) + ") and continuing silently.")
            return

        self.job_queue.append(MemoryProcess(name, size))

    def reset(self):
        self.job_queue = []
        self.blocks = []
        self.allocated = {}

    def get_job_queue(self):
        return self.job_queue

    def get_blocks(self):
        return self.blocks

    def get_allocated(self):
        return self.allocated

    def get_process_by_name(self, name):
        return [process for process in self.job_queue if process.name == name][0]
