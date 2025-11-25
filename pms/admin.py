from django.contrib import admin
from .models import (
    Project, ProjectMember, ProjectUpdate, Notification, 
    ProjectDocument, TaskPage, WorkUpdate, DailyUpdate, Issue,
    ProjectUpdateAttachment, DailyUpdateLineItem
)

# Register models
admin.site.register(Project)
admin.site.register(ProjectMember)
admin.site.register(ProjectUpdate)
admin.site.register(Notification)
admin.site.register(ProjectDocument)
admin.site.register(TaskPage)
admin.site.register(WorkUpdate)
admin.site.register(DailyUpdate)
admin.site.register(Issue)
admin.site.register(ProjectUpdateAttachment)
admin.site.register(DailyUpdateLineItem)