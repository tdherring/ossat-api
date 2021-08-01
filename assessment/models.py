from django.db import models
from users.models import CustomUser
from graphql_auth.signals import user_verified
from django.dispatch import receiver
from .simulator.cpu.non_preemptive.fcfs import FCFS
from .simulator.cpu.non_preemptive.sjf import SJF
from .simulator.cpu.non_preemptive.priority import Priority
from .simulator.cpu.preemptive.rr import RR
from .simulator.cpu.preemptive.srtf import SRTF
from .simulator.memory.contiguous.first_fit import FirstFit
from .simulator.memory.contiguous.best_fit import BestFit
from .simulator.memory.contiguous.worst_fit import WorstFit
import random
import json


class Assessment(models.Model):
    GENERAL_QUIZZES = ["FCFS", "SJF", "Priority", "RR", "SRTF", "First Fit", "Best Fit", "Worst Fit"]

    VARIANT_CHOICES = (("Generated Assessment", "Generated Assessment"),
                       ("Initial Assessment", "Initial Assessment"))

    for i in range(len(GENERAL_QUIZZES)):
        for j in range(1, 4):
            quiz = GENERAL_QUIZZES[i] + " " + ("I" * j)
            VARIANT_CHOICES += ((quiz, quiz),)

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    variant = models.CharField(max_length=100, default="generated", choices=VARIANT_CHOICES)
    submitted = models.BooleanField(default=False)
    score = models.IntegerField(default=None, blank=True, null=True)

    """
    Generates the general assessments for the user when their account is verified successfully.
    """
    @receiver(user_verified)
    def generate_general_assessmente(sender, user, **kwargs):
        VARIANT_MAPPINGS = {
            "CPU": {
                "FCFS": FCFS(),
                "SJF": SJF(),
                "Priority": Priority(),
                "RR": RR(),
                "SRTF": SRTF()
            },
            "Memory": {
                "First Fit": FirstFit(),
                "Best Fit": BestFit(),
                "Worst Fit": WorstFit()
            }
        }

        print(user.get_username(), "verified account! Generating assessments...")

        for variant_tuple in Assessment.VARIANT_CHOICES[2:]:
            print(variant_tuple[0])

            split_tuple = variant_tuple[0].split(" ")

            variant_name = " ".join(split_tuple[0:len(split_tuple) - 1])
            difficulty = split_tuple[len(split_tuple) - 1]

            assessment = Assessment(user=user, variant=variant_tuple[0], submitted=False, score=None)
            assessment.save()

            for question_num in range(10):
                cpu_num_processes_lo_hi = [3, 5] if difficulty == "I" else [5, 7] if difficulty == "II" else [7, 9]
                cpu_max_burst_time = 5 if difficulty == "I" else 9 if difficulty == "II" else 13
                cpu_max_arrival_time = 10 if difficulty == "I" else 15 if difficulty == "II" else 20
                cpu_max_priority = 6 if difficulty == "I" else 8 if difficulty == "II" else 10
                cpu_max_time_quantum = 4 if difficulty == "I" else 7 if difficulty == "II" else 9

                mem_process_block_size_lo_hi = [50, 200] if difficulty == "I" else [50, 500] if difficulty == "II" else [50, 800]
                mem_num_blocks_lo_hi = [2, 5] if difficulty == "I" else [4, 7] if difficulty == "II" else [5, 9]

                for process_num in range(random.randint(cpu_num_processes_lo_hi[0], cpu_num_processes_lo_hi[1])):
                    if variant_name in VARIANT_MAPPINGS["CPU"]:
                        variant = VARIANT_MAPPINGS["CPU"][variant_name]
                        if variant_name == "RR":
                            variant.set_time_quantum(random.randint(1, cpu_max_time_quantum))
                        variant.create_process("p" + str(process_num), random.randint(0, cpu_max_arrival_time), random.randint(1, cpu_max_burst_time),
                                               random.randint(0, cpu_max_priority) if variant_name == "Priority" else None)
                    else:
                        variant = VARIANT_MAPPINGS["Memory"][variant_name]
                        variant.create_process("p" + str(process_num), random.randint(mem_process_block_size_lo_hi[0], mem_process_block_size_lo_hi[1]))

                if variant_name in VARIANT_MAPPINGS["Memory"]:
                    for block_num in range(random.randint(mem_num_blocks_lo_hi[0], mem_num_blocks_lo_hi[1])):
                        variant.create_block("b" + str(block_num), random.randint(mem_process_block_size_lo_hi[0], mem_process_block_size_lo_hi[1]))

                job_queue = variant.get_job_queue(0) if variant_name in VARIANT_MAPPINGS["CPU"] else variant.get_job_queue()
                blocks = None
                allocated = None
                generated_answers = []

                if variant_name in VARIANT_MAPPINGS["CPU"]:
                    variant.dispatch_processes()
                    schedule = variant.get_schedule()

                    generated_schedule = []

                    for process in schedule:
                        for _ in range(process["burst_time"]):
                            generated_schedule.append(process)

                    schedule_length = generated_schedule[len(generated_schedule) - 1]["time_delta"]

                    answer_time_delta = random.randint(0, schedule_length)
                    answer = {"name": generated_schedule[answer_time_delta]["process_name"],
                              "arrival_time": generated_schedule[answer_time_delta]["arrival_time"],
                              "burst_time": generated_schedule[answer_time_delta]["burst_time"],
                              "priority": (generated_schedule[answer_time_delta]["priority"] if variant_name == "Priority" else None)}

                    for _ in range(4):
                        if len(job_queue) <= 5:
                            generated_answers = [{"name": process.get_name(),
                                                  "arrival_time": process.get_arrival_time(),
                                                  "burst_time": process.get_burst_time(),
                                                  "priority": (process.get_priority() if variant_name == "Priority" else None)}
                                                 for process in job_queue]
                        else:
                            generated_answers = random.sample(job_queue, 4)
                            generated_answers = [{"name": answer.get_name(),
                                                  "arrival_time": answer.get_arrival_time(),
                                                  "burst_time": answer.get_burst_time(),
                                                  "priority": (answer.get_priority() if variant_name == "Priority" else None)}
                                                 for answer in generated_answers]

                    if answer not in generated_answers:
                        generated_answers.append(answer)

                    random.shuffle(generated_answers)

                    question_text = "Using the " + str(variant_name) + " scheduling algorithm, and based on the processes below, which one is executing at time delta " + str(answer_time_delta) + "?"

                else:
                    variant.allocate_processes()

                    q_process = random.choice([process for process in job_queue if process != None])
                    blocks = variant.get_blocks()
                    allocated = variant.get_allocated()
                    answer = {"name": "None", "size": "N/A"} if not allocated[q_process.get_name()] else {"name": allocated[q_process.get_name()].get_name(),
                                                                                                          "size": allocated[q_process.get_name()].get_size()}

                    for _ in range(4):
                        if len(blocks) <= 5:
                            generated_answers = [{"name": block.get_name(),
                                                  "size": block.get_size()}
                                                 for block in blocks]
                        else:
                            generated_answers = random.sample(blocks, 4)
                            generated_answers = [{"name": answer.get_name(),
                                                  "size": answer.get_size()}
                                                 for answer in generated_answers]

                    if answer not in generated_answers:
                        generated_answers.append(answer)

                    random.shuffle(generated_answers)

                    question_text = "Using the " + str(variant_name) + " memory allocation technique, and based on the blocks below, which one does process " + \
                        str(q_process.get_name()) + " get placed in?"

                processArray = [{"name": process.get_name(),
                                "arrival_time": process.get_arrival_time(),
                                 "burst_time": process.get_burst_time(),
                                 "priority": (process.get_priority() if variant_name == "Priority" else None)}
                                for process in job_queue] if variant_name in VARIANT_MAPPINGS["CPU"] else [{"name": process.get_name(),
                                                                                                            "size": process.get_size()} for process in job_queue]

                blocksArray = [{"name": block.get_name(),
                                "size": block.get_size()}
                               for block in blocks] if variant_name in VARIANT_MAPPINGS["Memory"] else None

                question = Question(assessment=assessment, question_text=question_text, correct_answer=answer, selected_answer=None, processes=processArray, blocks=blocksArray)
                question.save()

                answer = Answer(question=question, answers=generated_answers)
                answer.save()

                VARIANT_MAPPINGS = {
                    "CPU": {
                        "FCFS": FCFS(),
                        "SJF": SJF(),
                        "Priority": Priority(),
                        "RR": RR(),
                        "SRTF": SRTF()
                    },
                    "Memory": {
                        "First Fit": FirstFit(),
                        "Best Fit": BestFit(),
                        "Worst Fit": WorstFit()
                    }
                }

        print("Successfully generated assessments for", user.get_username() + "!")


class Question(models.Model):
    id = models.AutoField(primary_key=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    question_text = models.CharField(max_length=1000)
    processes = models.JSONField()
    blocks = models.JSONField(blank=True, null=True)
    selected_answer = models.JSONField(blank=True, null=True)
    correct_answer = models.JSONField()


class Answer(models.Model):
    id = models.AutoField(primary_key=True)
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    answers = models.JSONField()
