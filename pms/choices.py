from django.db import models

class TaskStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"

class TaskPriority(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"

class ProjectStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    
class ProjectPriority(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"

class ProjectRole(models.TextChoices):
    UI_UX = "UI_UX", "UI/UX"
    DEVELOPER = "DEVELOPER", "Developer"
    TESTER = "TESTER", "Tester"
    
class ProjectUpdateStatus(models.TextChoices):
    INITIATE = "INITIATE", "Initiate"
    ONGOING = "ONGOING", "Ongoing"
    ONHOLD = "ONHOLD", "On-Hold"
    COMPLETE = "COMPLETE", "Complete"

class ProjectUpdateIntent(models.TextChoices):
    INFO = "INFO", "Info"
    QUERY = "QUERY", "Query"
    ISSUE = "ISSUE", "Issue"
    APPROVAL = "APPROVAL", "Approval"

class WorkStatus(models.TextChoices):
    INCOMPLETE = "INCOMPLETE", "Incomplete"
    PARTIALLY_DONE = "PARTIALLY_DONE", "Partially Done"
    COMPLETE = "COMPLETE", "Complete"

class IssueSubject(models.TextChoices):
    LEAVE = "LEAVE", "Leave Request"
    WORK_FROM_HOME = "WFH", "Work From Home"
    PROJECT_ISSUE = "PROJECT_ISSUE", "Project Issue"
    HARRASSMENT = "HARRASSMENT", "Harrassment"
    TECHNICAL_ISSUE = "TECHNICAL_ISSUE", "Technical Issue"
    PAYROLL = "PAYROLL", "Payroll Issue"
    OTHER = "OTHER", "Other"

class IssueStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    DECLINED = "DECLINED", "Declined"
    WFH_APPROVED = "WFH_APPROVED", "Work From Home Approved"