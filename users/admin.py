from django.contrib import admin
from django.contrib.auth import get_user_model
from assessment.models import Assessment
User = get_user_model()

# Register your models here.


def generate_assessments(modeladmin, request, queryset):
    for user in queryset:
        Assessment.generate_assessments(sender=None, user=user)


class GenerateAssessmentAdmin(admin.ModelAdmin):
    list_display = ("username", "first_name", "last_name", "is_staff", "is_superuser", "is_org_creator")
    actions = [generate_assessments]


admin.site.register(User, GenerateAssessmentAdmin)
