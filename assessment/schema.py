import graphene
import random
from graphene_django.types import DjangoObjectType
from numpy.core.fromnumeric import var
from .models import Assessment, Question, Answer, PerformanceData, KMeansData
from users.models import CustomUser
from graphql_jwt.utils import get_payload as verify_token
from statistics import mean
from pprint import pprint
import numpy as np
from .simulator.cpu.non_preemptive.fcfs import FCFS
from .simulator.cpu.non_preemptive.sjf import SJF
from .simulator.cpu.non_preemptive.priority import Priority
from .simulator.cpu.preemptive.rr import RR
from .simulator.cpu.preemptive.srtf import SRTF
from .simulator.memory.contiguous.first_fit import FirstFit
from .simulator.memory.contiguous.best_fit import BestFit
from .simulator.memory.contiguous.worst_fit import WorstFit


class AssessmentType(DjangoObjectType):
    class Meta:
        model = Assessment
        fields = "__all__"
        convert_choices_to_enum = False


class QuestionType(DjangoObjectType):
    class Meta:
        model = Question


class AnswerType(DjangoObjectType):
    class Meta:
        model = Answer


class Utils:
    @staticmethod
    def authenticated_and_permitted(token, username):
        verify_payload = verify_token(token)
        # User has permission? (They are the user making the request or are Staff).
        if (verify_payload["username"] == username or CustomUser.objects.get(username=verify_payload[username], is_staff=True)):
            return True
        return False


class Query():
    get_assessments = graphene.List(AssessmentType, username=graphene.String(), token=graphene.String(), variant=graphene.String(required=False))
    get_questions = graphene.List(QuestionType, username=graphene.String(), token=graphene.String(), assessment_id=graphene.ID())

    def resolve_get_assessments(self, info, username, token, variant=None):
        if Utils.authenticated_and_permitted(token, username):
            return Assessment.objects.filter(user=CustomUser.objects.get(username=username), variant=variant) if variant else Assessment.objects.filter(user=CustomUser.objects.get(username=username))

    def resolve_get_questions(self, info, username, token, assessment_id):
        if Utils.authenticated_and_permitted(token, username):
            assessment = Assessment.objects.get(pk=assessment_id)

            assessment_object = Question.objects.filter(assessment=assessment)

            if not assessment.submitted:
                for instance in assessment_object:
                    instance.correct_answer = None

            return assessment_object


class SetQuestionAnswerMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        answer = graphene.JSONString()
        username = graphene.String()
        token = graphene.String()

    question = graphene.Field(QuestionType)

    @classmethod
    def mutate(cls, root, info, id, answer, username, token):
        if Utils.authenticated_and_permitted(token, username):
            question = Question.objects.get(id=id)
            # Only allow modification if quiz not submitted.
            if not question.assessment.submitted:
                question.selected_answer = answer
                question.save()

            return SetQuestionAnswerMutation(question=question)


class SubmitAssessmentMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        username = graphene.String()
        token = graphene.String()

    assessment = graphene.Field(AssessmentType)

    @classmethod
    def mutate(cls, root, info, id, username, token):
        if Utils.authenticated_and_permitted(token, username):
            assessment = Assessment.objects.get(id=id)
            # Only allow modification if quiz not submitted.

            #! DISABLED FOR TESTING

            assessment.submitted = True
            assessment.score = len([question for question in Question.objects.filter(assessment=assessment) if question.selected_answer == question.correct_answer])

            assessment.save()

            if assessment.variant == "Initial Assessment":
                cls.generate_assessment_kmeans(assessment, username)

            return SubmitAssessmentMutation(assessment=assessment)

    def generate_assessment_kmeans(assessment, username, k=3):
        variant_performance = {"FCFS": None,
                               "SJF": None,
                               "Priority": None,
                               "RR": None,
                               "SRTF": None,
                               "First Fit": None,
                               "Best Fit": None,
                               "Worst Fit": None}

        questions = Question.objects.filter(assessment=assessment)

        # Count the performance of the student on each question.
        for variant in variant_performance.keys():
            matched_questions = questions.filter(question_text__contains=variant)
            correct, total = 0, 0
            for matched_q in matched_questions:
                total += 1
                if matched_q.selected_answer == matched_q.correct_answer:
                    correct += 1
            variant_performance[variant] = [correct, total]

        performance_data = PerformanceData(per_question_variant_score=variant_performance)
        performance_data.save()

        assessment.performance_data = performance_data
        assessment.save()

        # Get performance data for all initial assessments.
        initial_assessments = Assessment.objects.filter(variant="Initial Assessment").only("performance_data", "id")

        output_centroids = {}
        closest_centroids = {}

        for variant in variant_performance.keys():
            centroids = KMeansData.objects.last().output_centroids[variant] if len(KMeansData.objects.all()) > 0 else [random.uniform(0.0, 3.0) for _ in range(k)]
            closest_centroid = {i: [] for i in range(k)}

            for initial in initial_assessments:
                converged = [False for _ in range(k)]

                if initial.performance_data:

                    variant_score = initial.performance_data.per_question_variant_score[variant][0]
                    while not all(converged):
                        old_centroids = []
                        closest_centroid[min(range(k), key=lambda i: abs(centroids[i]-variant_score))].append(variant_score)
                        old_centroids.extend(centroids)
                        centroids = [mean(closest_centroid[i]) if len(closest_centroid[i]) > 0 else centroids[i] for i in range(k)]
                        converged = [True if abs(centroids[i] - old_centroids[i]) < 0.001 else False for i in range(k)]

            output_centroids[variant] = centroids
            closest_centroids[variant] = min(range(k), key=lambda i: abs(centroids[i]-variant_score))

        kmeans_data = KMeansData(user=CustomUser.objects.get(username=username), output_centroids=output_centroids, closest_centroids=closest_centroids)
        kmeans_data.save()

        all_kmeans_data = KMeansData.objects.all()

        all_similarities = []

        most_similar = {"FCFS": {},
                        "SJF": {},
                        "Priority": {},
                        "RR": {},
                        "SRTF": {},
                        "First Fit": {},
                        "Best Fit": {},
                        "Worst Fit": {}}

        for data in all_kmeans_data:
            if data.output_centroids != output_centroids:
                similarities = {variant: [abs(data.output_centroids[variant][i] - output_centroids[variant][i]) for i in range(k)] for variant in most_similar.keys()}
                all_similarities.append({"similarities": similarities,
                                         "data_object": data})

        for instance in all_similarities:
            kmeans_obj = instance["data_object"]
            sim = instance["similarities"]

            for variant in most_similar.keys():
                if len(most_similar[variant]) == 0 or sum(sim[variant]) < sum(most_similar[variant]["values"]):
                    most_similar[variant] = {"user": kmeans_obj.user.username, "values": sim[variant]}

                print(sum(sim[variant]), sum(most_similar[variant]["values"]))

        generation_data = []

        for variant in most_similar.keys():
            user = CustomUser.objects.get(username=most_similar[variant]["user"])

            user_init_assessment = Assessment.objects.get(user=user, variant="Initial Assessment")

            performance_data = user_init_assessment.performance_data.per_question_variant_score

            generation_data.append(performance_data)

        generated_assessment = Assessment(user=CustomUser.objects.get(username=username), variant="Generated Assessment", submitted=False, score=None)
        generated_assessment.save()

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

        generated_qs = 0
        observing_score = 0

        while generated_qs < 24:

            cpu_num_processes_lo_hi = [3, 5] if observing_score == 0 or 1 else [5, 7] if observing_score == 2 else [7, 9]
            cpu_max_burst_time = 5 if observing_score == 0 or 1 else 9 if observing_score == 2 else 13
            cpu_max_arrival_time = 10 if observing_score == 0 or 1 else 15 if observing_score == 2 else 20
            cpu_max_priority = 6 if observing_score == 0 or 1 else 8 if observing_score == 2 else 10
            cpu_max_time_quantum = 4 if observing_score == 0 or 1 else 7 if observing_score == 2 else 9

            mem_process_block_size_lo_hi = [50, 200] if observing_score == 0 or 1 else [50, 500] if observing_score == 2 else [50, 800]
            mem_num_blocks_lo_hi = [2, 5] if observing_score == 0 or 1 else [4, 7] if observing_score == 2 else [5, 9]

            for data in generation_data:
                for variant_name in data.keys():
                    if data[variant_name] is not None:
                        if data[variant_name][0] == observing_score:
                            pass
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

                                question_text = "Using the " + str(variant_name) + \
                                    " scheduling algorithm, and based on the processes below, which one is executing at time delta " + str(answer_time_delta) + "?"

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

                            question = Question(assessment=generated_assessment, question_text=question_text, correct_answer=answer,
                                                selected_answer=None, processes=processArray, blocks=blocksArray)
                            question.save()

                            answer = Answer(question=question, answers=generated_answers)
                            answer.save()

                            generated_qs += 1

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

                            if generated_qs >= 24:
                                return

            if observing_score < 3:
                observing_score += 1


class Mutation():
    set_question_answer = SetQuestionAnswerMutation.Field()
    submit_assessment = SubmitAssessmentMutation.Field()
