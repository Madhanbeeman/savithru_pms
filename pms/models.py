from django.db import models
from users.models import User
from django.utils import timezone
from .choices import (
    TaskStatus, TaskPriority, ProjectStatus, ProjectPriority,
    ProjectRole, ProjectUpdateStatus, ProjectUpdateIntent, WorkStatus,
    IssueSubject, IssueStatus
)

class ProjectMember(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name="project_members")
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': User.Role.EMPLOYEE}
    )
    role = models.CharField(max_length=50, choices=ProjectRole.choices)

    class Meta:
        unique_together = ('project', 'user', 'role') 

    def __str__(self):
        return f"{self.user.username} as {self.get_role_display()} on {self.project.name}"

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.PENDING)
    priority = models.CharField(max_length=20, choices=ProjectPriority.choices, default=ProjectPriority.MEDIUM)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    google_meet_link = models.URLField(max_length=200, blank=True, null=True, help_text="e.g., https://meet.google.com/abc-xyz-123")
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="managed_projects", 
        limit_choices_to={'role': User.Role.MANAGEMENT}
    )

    team_head = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_projects",
        limit_choices_to={'role': User.Role.EMPLOYEE}
    )

    client_name = models.CharField(max_length=200, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    project_logo = models.ImageField(upload_to='project_logos/', blank=True, null=True)

    members = models.ManyToManyField(
        User,
        through='ProjectMember',
        related_name="projects"
    )
    
    project_status_update = models.CharField(
        max_length=20, 
        choices=WorkStatus.choices, 
        default=WorkStatus.INCOMPLETE,
        blank=True
    )
    project_status_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class ProjectDocument(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="documents")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    document = models.FileField(upload_to='project_documents/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.document.name} for {self.project.name}"

class TaskPage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="task_pages")
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_pages")
    page_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.page_name} for {self.project.name}"


# --- UPDATED PROJECT UPDATE MODEL ---
class ProjectUpdate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="updates")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="project_updates")
    
    # --- NEW CATEGORY FIELD ---
    CATEGORY_CHOICES = [
        ('UPDATE', 'Update/Report'),
        ('RECOMMENDATION', 'Recommendation'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='UPDATE')
    # --------------------------

    title = models.CharField(max_length=255, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True) 
    
    # Fields specific to certain types
    end_date = models.DateField(null=True, blank=True) # Used for Recommendations
    priority = models.CharField(max_length=20, choices=ProjectPriority.choices, default=ProjectPriority.MEDIUM, null=True, blank=True) # Used for Updates
    
    # (Subject field is removed/deprecated as we use Category now, but keep if you want to avoid migration issues, otherwise delete)
    subject = models.CharField(max_length=10, choices=ProjectUpdateIntent.choices, null=True, blank=True)
    
    # Legacy/Chat fields (keep to prevent errors)
    image = models.ImageField(upload_to='project_chat_images/', blank=True, null=True)
    file = models.FileField(upload_to='project_chat_files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_status = models.CharField(max_length=20, choices=ProjectUpdateStatus.choices, blank=True, null=True)
    voice_note = models.FileField(upload_to='project_voice_notes/', blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category} on {self.project.name}"

# --- NEW MODEL FOR ATTACHMENTS ---
class ProjectUpdateAttachment(models.Model):
    project_update = models.ForeignKey(ProjectUpdate, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to='project_updates/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name


class WorkUpdate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="work_updates")
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name="work_updates")
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=WorkStatus.choices, default=WorkStatus.INCOMPLETE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Update from {self.member.username} on {self.project.name}"

class DailyUpdate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_updates")
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True, null=True) # General description
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        # REMOVED unique_together so you can submit multiple times per day

    def __str__(self):
        return f"Update from {self.user.username} on {self.date}"

# --- NEW: Daily Update Line Item (Child) ---
class DailyUpdateLineItem(models.Model):
    daily_update = models.ForeignKey(DailyUpdate, on_delete=models.CASCADE, related_name="line_items")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    task_page = models.ForeignKey(TaskPage, on_delete=models.CASCADE)
    
    # --- CHANGED: Simple Text Field for Duration ---
    time_spent = models.CharField(max_length=50, help_text="e.g. 2:30 or 2 hrs") 

    def __str__(self):
        return f"{self.project.name} - {self.task_page.page_name}"

class Issue(models.Model):
    subject = models.CharField(max_length=50, choices=IssueSubject.choices)
    description = models.TextField()
    attachment = models.FileField(upload_to='issue_attachments/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=IssueStatus.choices, default=IssueStatus.PENDING)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="issues_sent")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Issue: {self.get_subject_display()} from {self.user.username}"
        
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']