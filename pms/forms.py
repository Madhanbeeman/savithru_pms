from django import forms
from django.forms import formset_factory, modelformset_factory, inlineformset_factory # <-- Added inlineformset_factory
from .models import (
    Project, TaskPage, ProjectUpdate, ProjectMember, WorkUpdate, 
    Issue, DailyUpdate, ProjectDocument, ProjectUpdateAttachment,
    DailyUpdateLineItem
)
from users.models import User
from .choices import (
    ProjectUpdateStatus, ProjectUpdateIntent, ProjectRole, WorkStatus,
    IssueSubject, IssueStatus, ProjectPriority
)

class ProjectForm(forms.ModelForm):
    team_head = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.EMPLOYEE),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Assign Project Manager (Team Head)"
    )
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'priority', 
            'client_name', 'start_date', 'end_date',
            'team_head', 'project_logo','google_meet_link'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'project_logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'google_meet_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://meet.google.com/...'}),
        }
        labels = { 'project_logo': 'Project Logo','google_meet_link': 'Google Meet Link' }

class ProjectDocumentForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional: Document description'}),
        required=False
    )
    document = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=True
    )
    class Meta:
        model = ProjectDocument
        fields = ['description', 'document']

ProjectDocumentFormSet = formset_factory(ProjectDocumentForm, extra=1, can_delete=True)

class TaskPageForm(forms.ModelForm):
    page_name = forms.CharField(
        label="Task Page Name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    class Meta:
        model = TaskPage
        fields = ['page_name']

TaskPageFormSet = formset_factory(TaskPageForm, extra=1, can_delete=True)


class ProjectChatForm(forms.ModelForm):
    remarks = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Type a message...',
            'autocomplete': 'off'
        }),
        label=False,
        required=False 
    )
    image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'style': 'display: none;', 'id': 'chat-image-input'}),
        required=False
    )
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'style': 'display: none;', 'id': 'chat-file-input'}),
        required=False
    )
    class Meta:
        model = ProjectUpdate
        fields = ['remarks', 'image', 'file']


# --- 1. FORM FOR UPDATES PAGE (Priority, Title, Desc) ---
class ProjectUpdateForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Title", required=True
    )
    priority = forms.ChoiceField(
        choices=ProjectPriority.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Priority"
    )
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        label="Description", required=True
    )
    class Meta:
        model = ProjectUpdate
        fields = ['title', 'priority', 'remarks']

# --- 2. FORM FOR VIEW PAGE (End Date, Title, Desc) ---
class ProjectRecommendationForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Title", required=True
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="End Date", required=True
    )
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        label="Description", required=True
    )
    class Meta:
        model = ProjectUpdate
        fields = ['title', 'end_date', 'remarks']

# --- ATTACHMENT FORMSET (Used by both) ---
class ProjectUpdateAttachmentForm(forms.ModelForm):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=True,
        label=False
    )
    class Meta:
        model = ProjectUpdateAttachment
        fields = ['file']

ProjectUpdateAttachmentFormSet = modelformset_factory(
    ProjectUpdateAttachment, 
    form=ProjectUpdateAttachmentForm, 
    extra=1, 
    can_delete=True
)


class StructuredUpdateForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Title",
        required=True
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="End Date",
        required=False
    )
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        label="Description",
        required=True
    )
    # We removed Priority/Subject from required fields based on your request
    # Files are handled by the FormSet
    
    class Meta:
        model = ProjectUpdate
        fields = ['title', 'end_date', 'remarks']


class ProjectUpdateAttachmentForm(forms.ModelForm):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=True,
        label=False
    )
    class Meta:
        model = ProjectUpdateAttachment
        fields = ['file']

ProjectUpdateAttachmentFormSet = modelformset_factory(
    ProjectUpdateAttachment, 
    form=ProjectUpdateAttachmentForm, 
    extra=1, 
    can_delete=True
)


class ProjectMemberForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.EMPLOYEE),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    role = forms.ChoiceField(
        choices=ProjectRole.choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = ProjectMember
        fields = ['user', 'role']

class WorkUpdateForm(forms.ModelForm):
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label="Description (Optional)"
    )
    status = forms.ChoiceField(
        choices=WorkStatus.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="My Work Status"
    )
    class Meta:
        model = WorkUpdate
        fields = ['status', 'remarks']

class ProjectStatusUpdateForm(forms.ModelForm):
    project_status_description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label="Description (Optional)"
    )
    project_status_update = forms.ChoiceField(
        choices=WorkStatus.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Overall Project Status"
    )
    class Meta:
        model = Project
        fields = ['project_status_update', 'project_status_description']

# --- UPDATED: Daily Update Parent Form ---
class DailyUpdateForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'General remarks for the day...'}),
        required=False
    )
    class Meta:
        model = DailyUpdate
        fields = ['description']

# --- NEW: Line Item Form ---
class DailyUpdateLineItemForm(forms.ModelForm):
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select project-select'}),
    )
    task_page = forms.ModelChoiceField(
        queryset=TaskPage.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select task-select'}),
    )
    # Simple Text Input (No Clock)
    time_spent = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'e.g. 2.5 or 2:30'
        }),
        label="Time Taken"
    )

    class Meta:
        model = DailyUpdateLineItem
        fields = ['project', 'task_page', 'time_spent']

# --- FormSet Factory (THIS WAS MISSING) ---
DailyUpdateLineItemFormSet = inlineformset_factory(
    DailyUpdate,
    DailyUpdateLineItem,
    form=DailyUpdateLineItemForm,
    extra=1,
    can_delete=True
)

class IssueForm(forms.ModelForm):
    subject = forms.ChoiceField(
        choices=IssueSubject.choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        label="Description"
    )
    attachment = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=False
    )
    class Meta:
        model = Issue
        fields = ['subject', 'description', 'attachment']

class ProjectMeetingForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['google_meet_link']
        widgets = {
            'google_meet_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://meet.google.com/abc-defg-hij'}),
        }
        labels = {
            'google_meet_link': 'Google Meet URL'
        }