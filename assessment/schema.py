import graphene
from graphene_django.types import DjangoObjectType
from .models import Assessment
from .models import Question
from .models import Answer
from users.models import CustomUser
from graphql_jwt.utils import get_payload as verify_token


class AssessmentType(DjangoObjectType):
    class Meta:
        model = Assessment


class QuestionType(DjangoObjectType):
    class Meta:
        model = Question


class AnswerType(DjangoObjectType):
    class Meta:
        model = Answer


class Utils:
    @staticmethod
    def authenticated_and_permitted(token, username, allow_staff_access=False):
        verify_payload = verify_token(token)
        # User has permission? (They are the user making the request or are Staff).
        if (verify_payload["username"] == username or CustomUser.objects.get(username=verify_payload[username], is_staff=True)):
            return True
        return False


class Query():
    get_assessments = graphene.List(AssessmentType, username=graphene.String(), token=graphene.String())
    get_questions = graphene.List(QuestionType, username=graphene.String(), token=graphene.String(), assessment_id=graphene.ID())
    get_answers = graphene.List(AnswerType)

    def resolve_get_assessments(self, info, username, token):
        if Utils.authenticated_and_permitted(token, username, True):
            return Assessment.objects.filter(user=CustomUser.objects.get(username=username))

    def resolve_get_questions(self, info, username, token, assessment_id):
        if Utils.authenticated_and_permitted(token, username, True):
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
            assessment.submitted = True
            assessment.score = len([question for question in Question.objects.filter(assessment=assessment) if question.selected_answer == question.correct_answer])
            assessment.save()

            return SubmitAssessmentMutation(assessment=assessment)


class Mutation():
    set_question_answer = SetQuestionAnswerMutation.Field()
    submit_assessment = SubmitAssessmentMutation.Field()
