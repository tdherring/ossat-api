import graphene
from graphene_django.types import DjangoObjectType
from graphene.types.generic import GenericScalar
from .models import Organisation
from users.models import CustomUser
from graphql_jwt.utils import get_payload
import string
import random


class OrganisationType(DjangoObjectType):
    class Meta:
        model = Organisation


class CustomUserType(DjangoObjectType):
    class Meta:
        model = CustomUser


class Utils:
    @staticmethod
    def has_org_management_permission(token):
        # User has permission? (They are the user making the request or are Staff).
        if CustomUser.objects.get(username=get_payload(token)["username"]).is_org_manager:
            return True
        return False


class Query():
    get_organisations = graphene.List(OrganisationType, token=graphene.String(), name=graphene.String(required=False))

    def resolve_get_organisations(self, info, token, name=None):
        org_manager = Utils.has_org_management_permission(token)
        user = CustomUser.objects.get(username=get_payload(token)["username"])
        if org_manager:
            return Organisation.objects.filter(owner=user) if not name else Organisation.objects.get(name=name, owner=user)
        return Organisation.objects.filter(members=user)


class CreateOrganisationMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String()
        token = graphene.String()

    organisation = graphene.Field(OrganisationType)
    success = graphene.Boolean()
    errors = GenericScalar()

    @classmethod
    def mutate(cls, root, info, name, token):
        if Utils.has_org_management_permission(token):
            if len(Organisation.objects.filter(name=name)) > 0:
                return CreateOrganisationMutation(success=False, errors={"name": [{"message": "An Organisation with that name already exists.", "code": "org_already_exists"}]})
            elif len(name) > 200:
                return CreateOrganisationMutation(success=False, errors={"name": [{"message": "Organisation name too long.", "code": "name_too_long"}]})
            new_org = Organisation(name=name, invite_code="".join(random.choice(string.ascii_uppercase) for _ in range(10)), owner=CustomUser.objects.get(username=get_payload(token)["username"]))
            new_org.save()
            return CreateOrganisationMutation(organisation=new_org, success=True)

        return CreateOrganisationMutation(success=False, errors={"nonFieldErrors": [{"message": "User does not have permission to manage Organisations.", "code": "no_permission"}]})


class DeleteOrganisationMutation(graphene.Mutation):
    class Arguments:
        name = graphene.String()
        token = graphene.String()

    success = graphene.Boolean()
    errors = GenericScalar()

    @classmethod
    def mutate(cls, root, info, name, token):
        if Utils.has_org_management_permission(token):
            if len(Organisation.objects.filter(name=name)) > 0:
                if Organisation.objects.get(name=name).owner == CustomUser.objects.get(username=get_payload(token)["username"]):
                    Organisation.objects.get(name=name).delete()
                    return DeleteOrganisationMutation(success=True)
                else:
                    return DeleteOrganisationMutation(success=False, errors={"nonFieldErrors": [{"message": "Only the Organisation owner can delete the Organisation.", "code": "not_owner"}]})
            else:
                return DeleteOrganisationMutation(success=False, errors={"name": [{"message": "An Organisation with that name doesn't exist.", "code": "org_does_not_exist"}]})

        return DeleteOrganisationMutation(success=False, errors={"nonFieldErrors": [{"message": "User does not have permission to manage Organisations.", "code": "no_permission"}]})


class KickOrganisationMemberMutation(graphene.Mutation):
    class Arguments:
        org_name = graphene.String()
        username = graphene.String()
        token = graphene.String()

    organisation = graphene.Field(OrganisationType)
    success = graphene.Boolean()
    errors = GenericScalar()

    @classmethod
    def mutate(cls, root, info, org_name, username, token):
        if Utils.has_org_management_permission(token):
            if len(Organisation.objects.filter(name=org_name)) > 0:
                if Organisation.objects.get(name=org_name).owner == CustomUser.objects.get(username=get_payload(token)["username"]):
                    if len(CustomUser.objects.filter(username=username)) > 0:
                        org = Organisation.objects.get(name=org_name)
                        user = CustomUser.objects.get(username=username)
                        org.members.remove(user)
                        return KickOrganisationMemberMutation(success=True, organisation=org)
                    else:
                        return KickOrganisationMemberMutation(success=False, errors={"username": [{"message": "A user with the provided name does not exist.", "code": "user_does_not_exist"}]})
                else:
                    return KickOrganisationMemberMutation(success=False, errors={"nonFieldErrors": [{"message": "Only the Organisation owner can remove members.", "code": "not_owner"}]})
            else:
                return KickOrganisationMemberMutation(success=False, errors={"org_name": [{"message": "An Organisation with that name doesn't exist.", "code": "org_does_not_exist"}]})

        return KickOrganisationMemberMutation(success=False, errors={"nonFieldErrors": [{"message": "User does not have permission to manage Organisations.", "code": "no_permission"}]})


class PromoteOrganisationMemberMutation(graphene.Mutation):
    class Arguments:
        org_name = graphene.String()
        username = graphene.String()
        token = graphene.String()

    organisation = graphene.Field(OrganisationType)
    success = graphene.Boolean()
    errors = GenericScalar()

    @classmethod
    def mutate(cls, root, info, org_name, username, token):
        if Utils.has_org_management_permission(token):
            if len(Organisation.objects.filter(name=org_name)) > 0:
                if Organisation.objects.get(name=org_name).owner == CustomUser.objects.get(username=get_payload(token)["username"]):
                    if len(CustomUser.objects.filter(username=username)) > 0:
                        org = Organisation.objects.get(name=org_name)
                        user = CustomUser.objects.get(username=username)
                        org.members.remove(user)
                        org.managers.add(user)
                        return PromoteOrganisationMemberMutation(success=True, organisation=org)
                    else:
                        return PromoteOrganisationMemberMutation(success=False, errors={"username": [{"message": "A user with the provided name does not exist.", "code": "user_does_not_exist"}]})
                else:
                    return PromoteOrganisationMemberMutation(success=False, errors={"nonFieldErrors": [{"message": "Only the Organisation owner can promote members.", "code": "not_owner"}]})
            else:
                return PromoteOrganisationMemberMutation(success=False, errors={"org_name": [{"message": "An Organisation with that name doesn't exist.", "code": "org_does_not_exist"}]})

        return PromoteOrganisationMemberMutation(success=False, errors={"nonFieldErrors": [{"message": "User does not have permission to manage Organisations.", "code": "no_permission"}]})


class DemoteOrganisationManagerMutation(graphene.Mutation):
    class Arguments:
        org_name = graphene.String()
        username = graphene.String()
        token = graphene.String()

    organisation = graphene.Field(OrganisationType)
    success = graphene.Boolean()
    errors = GenericScalar()

    @classmethod
    def mutate(cls, root, info, org_name, username, token):
        if Utils.has_org_management_permission(token):
            if len(Organisation.objects.filter(name=org_name)) > 0:
                if Organisation.objects.get(name=org_name).owner == CustomUser.objects.get(username=get_payload(token)["username"]):
                    if len(CustomUser.objects.filter(username=username)) > 0:
                        org = Organisation.objects.get(name=org_name)
                        user = CustomUser.objects.get(username=username)
                        org.managers.remove(user)
                        org.members.add(user)
                        return DemoteOrganisationManagerMutation(success=True, organisation=org)
                    else:
                        return DemoteOrganisationManagerMutation(success=False, errors={"username": [{"message": "A user with the provided name does not exist.", "code": "user_does_not_exist"}]})
                else:
                    return DemoteOrganisationManagerMutation(success=False, errors={"nonFieldErrors": [{"message": "Only the Organisation owner can demote managers.", "code": "not_owner"}]})
            else:
                return DemoteOrganisationManagerMutation(success=False, errors={"org_name": [{"message": "An Organisation with that name doesn't exist.", "code": "org_does_not_exist"}]})

        return DemoteOrganisationManagerMutation(success=False, errors={"nonFieldErrors": [{"message": "User does not have permission to manage Organisations.", "code": "no_permission"}]})


class JoinOrganisationMutation(graphene.Mutation):
    class Arguments:
        token = graphene.String()
        invite_code = graphene.String()

    organisation = graphene.Field(OrganisationType)
    success = graphene.Boolean()
    errors = GenericScalar()

    @classmethod
    def mutate(cls, root, info, token, invite_code):
        if not Utils.has_org_management_permission(token):
            if len(Organisation.objects.filter(invite_code=invite_code)) > 0:
                org = Organisation.objects.get(invite_code=invite_code)
                user = CustomUser.objects.get(username=get_payload(token)["username"])
                print(user.member_of.exists())
                if not user.member_of.exists():
                    org.members.add(user)
                    return JoinOrganisationMutation(success=True, organisation=org)
                else:
                    return JoinOrganisationMutation(success=False, errors={"nonFieldErrors": [{"message": "User is already a member of an organisation.", "code": "already_member"}]})
            else:
                return JoinOrganisationMutation(success=False, errors={"token": [{"message": "Invalid invite code.", "code": "invalid_invite_code"}]})

        return JoinOrganisationMutation(success=False, errors={"nonFieldErrors": [{"message": "Organisation managers cannot join Organisations.", "code": "no_managers"}]})


class Mutation():
    create_organisation = CreateOrganisationMutation.Field()
    delete_organisation = DeleteOrganisationMutation.Field()
    kick_organisation_member = KickOrganisationMemberMutation.Field()
    promote_organisation_member = PromoteOrganisationMemberMutation.Field()
    demote_organisation_manager = DemoteOrganisationManagerMutation.Field()
    join_organisation = JoinOrganisationMutation.Field()
