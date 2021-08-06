import graphene
import random
from graphene_django.types import DjangoObjectType
from .models import Assessment, Question, Answer, PerformanceData, KMeansData
from users.models import CustomUser
from graphql_jwt.utils import get_payload as verify_token
from statistics import mean
from pprint import pprint
import numpy as np


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
    get_answers = graphene.List(AnswerType)

    def resolve_get_assessments(self, info, username, token, variant=None):
        if Utils.authenticated_and_permitted(token, username):
            return Assessment.objects.filter(user=CustomUser.objects.get(username=username), variant=variant) if variant else Assessment.objects.filter(user=CustomUser.objects.get(username=username))

    def resolve_get_questions(self, info, username, token, assessment_id):
        if Utils.authenticated_and_permitted(token, username):
            return Question.objects.filter(assessment=Assessment.objects.get(pk=assessment_id))

    def resolve_get_answers(self, info, **kwargs):
        return Answer.objects.all()


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

            # assessment.submitted = True
            # assessment.score = len([question for question in Question.objects.filter(assessment=assessment) if question.selected_answer == question.correct_answer])

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

        most_similar = {"FCFS": [],
                        "SJF": [],
                        "Priority": [],
                        "RR": [],
                        "SRTF": [],
                        "First Fit": [],
                        "Best Fit": [],
                        "Worst Fit": []}

        all_kmeans_data = KMeansData.objects.all()

        for variant in most_similar.keys():

            for i in range(len(all_kmeans_data)):
                similarities = np.array([sum([abs(all_kmeans_data[i].output_centroids[variant][j] - output_centroids[variant][j])
                                        for j in range(k)]) for data in all_kmeans_data if data != kmeans_data])
                most_similar_10 = np.argsort(similarities)[:10]

            print(variant, most_similar_10)

        # pprint(most_similar)


class Mutation():
    set_question_answer = SetQuestionAnswerMutation.Field()
    submit_assessment = SubmitAssessmentMutation.Field()
