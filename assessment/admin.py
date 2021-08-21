from django.contrib import admin
from .models import Assessment, Question, Answer, PerformanceData, KMeansData

# Register your models here.


class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "variant")


admin.site.register(Assessment, AssessmentAdmin)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(PerformanceData)
admin.site.register(KMeansData)
