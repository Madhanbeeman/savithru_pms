from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Prefetch, OuterRef, Subquery, Value, Count, Case, When, BooleanField
from django.db.models.functions import Coalesce
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
import datetime
import calendar
import json
import os

# Import Models
from users.models import User
from .models import (
    Project, TaskPage, ProjectUpdate, Notification,
    ProjectMember, WorkUpdate, DailyUpdate, Issue, ProjectDocument,
    ProjectUpdateAttachment, DailyUpdateLineItem
)
from .choices import (
    TaskStatus, ProjectRole, ProjectStatus, WorkStatus, IssueStatus,
    ProjectUpdateStatus, ProjectUpdateIntent, ProjectPriority
)

# Import Forms
from users.forms import EmployeeCreationForm
from .forms import (
    ProjectForm, 
    ProjectChatForm, 
    ProjectUpdateForm,
    ProjectRecommendationForm,
    ProjectMeetingForm,
    ProjectMemberForm,
    WorkUpdateForm,
    DailyUpdateForm,
    DailyUpdateLineItemFormSet,
    IssueForm,
    ProjectDocumentFormSet,
    ProjectStatusUpdateForm,
    TaskPageFormSet,
    ProjectDocumentForm,
    ProjectUpdateAttachmentFormSet
)

# --- HELPER FUNCTIONS ---
def user_is_project_admin_or_manager(user, project=None):
    if not user.is_authenticated: return False
    if user.role == User.Role.MANAGEMENT: return True
    if project: return user == project.team_head
    if Project.objects.filter(team_head=user).exists(): return True
    return False

def get_base_template(user):
    if user.role == User.Role.MANAGEMENT:
        return 'base_management.html'
    return 'base_employee.html'

# --- PERMISSION DECORATORS ---
def management_only_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.role == User.Role.MANAGEMENT):
            messages.warning(request, "Permission denied.")
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def team_head_only_required(view_func):
    def _wrapped_view(request, project_id, *args, **kwargs):
        project = get_object_or_404(Project, id=project_id)
        if not (request.user == project.team_head):
            messages.error(request, "Permission denied.")
            return redirect('project_list')
        kwargs['project'] = project
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# --- MAIN VIEWS ---
@login_required
def index_view(request):
    if user_is_project_admin_or_manager(request.user): return redirect('management_dashboard')
    elif request.user.role == User.Role.EMPLOYEE: return redirect('project_list')
    else: return redirect('login')

@login_required
def placeholder_view(request):
    base = get_base_template(request.user)
    return render(request, 'placeholder.html', {'base_template': base})

@login_required
def management_dashboard(request):
    if not user_is_project_admin_or_manager(request.user): return redirect('project_list')
    
    total_projects = Project.objects.count()
    total_employees = User.objects.filter(role=User.Role.EMPLOYEE).count()
    pending_tasks_count = TaskPage.objects.count() 
    
    today = datetime.date.today()
    threshold_date = today + datetime.timedelta(days=5)

    all_projects = Project.objects.annotate(
        is_urgent=Case(
            When(
                end_date__lte=threshold_date,
                project_status_update__in=['PENDING', 'PARTIALLY_DONE', 'INCOMPLETE'],
                then=Value(True)
            ),
            default=Value(False),
            output_field=BooleanField()
        )
    ).order_by('-is_urgent', 'end_date')
    
    recent_projects = all_projects[:6]
    key_tasks = TaskPage.objects.all().select_related('project', 'assigned_to').order_by('created_at')[:7]
    employees = User.objects.filter(role=User.Role.EMPLOYEE).order_by('username')[:6]
    
    cal = calendar.Calendar()
    month_weeks = cal.monthdayscalendar(today.year, today.month)
    month_name = today.strftime('%B %Y')
    day_names = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    
    context = {
        'total_projects': total_projects, 
        'total_employees': total_employees,
        'pending_tasks_count': pending_tasks_count, 
        'recent_projects': recent_projects, 
        'projects': all_projects, 
        'key_tasks': key_tasks, 
        'employees': employees, 
        'today_num': today.day,
        'month_name': month_name, 
        'month_weeks': month_weeks, 
        'day_names': day_names,
        'base_template': 'base_management.html',
    }
    return render(request, 'management/dashboard.html', context)

@login_required
def employee_dashboard(request):
    if request.user.role == User.Role.MANAGEMENT:
        return redirect('management_dashboard')

    today = datetime.date.today()
    threshold_date = today + datetime.timedelta(days=5)

    my_projects = Project.objects.filter(
        Q(members=request.user) | Q(team_head=request.user)
    ).distinct().annotate(
        is_urgent=Case(
            When(
                end_date__lte=threshold_date,
                project_status_update__in=['PENDING', 'PARTIALLY_DONE', 'INCOMPLETE'],
                then=Value(True)
            ),
            default=Value(False),
            output_field=BooleanField()
        )
    ).order_by('-is_urgent', 'end_date')

    my_tasks = TaskPage.objects.filter(
        assigned_to=request.user, 
        is_complete=False
    ).select_related('project')
    
    base_template = get_base_template(request.user)

    context = {
        'projects': my_projects,
        'my_tasks': my_tasks,
        'base_template': base_template
    }
    return render(request, 'employee/dashboard.html', context)

# --- PROJECT VIEWS ---
@login_required
def project_list_view(request):
    work_update_form = WorkUpdateForm()
    project_status_update_form = ProjectStatusUpdateForm()
    is_manager = request.user.role == User.Role.MANAGEMENT
    is_team_head = user_is_project_admin_or_manager(request.user) and not is_manager

    if is_manager: project_list_base = Project.objects.all()
    else: project_list_base = (Project.objects.filter(members=request.user) | Project.objects.filter(task_pages__assigned_to=request.user) | Project.objects.filter(team_head=request.user)).distinct()

    today = datetime.date.today()
    threshold = today + datetime.timedelta(days=5)
    project_list_base = project_list_base.annotate(
        is_urgent=Case(
            When(end_date__lte=threshold, project_status_update__in=['PENDING','PARTIALLY_DONE','INCOMPLETE'], then=Value(True)),
            default=Value(False), output_field=BooleanField()
        )
    ).order_by('-is_urgent', '-created_at')

    if is_manager:
        template_name = 'pms/project_list.html'
        project_list = project_list_base.annotate(total_tasks=Count('task_pages'), completed_tasks=Value(0))
    elif is_team_head: 
        template_name = 'pms/project_list.html'
        latest = WorkUpdate.objects.filter(project=OuterRef('project'), member=OuterRef('user')).order_by('-created_at').values('status')[:1]
        project_list = project_list_base.prefetch_related(
            Prefetch('project_members', queryset=ProjectMember.objects.select_related('user').annotate(latest_status=Coalesce(Subquery(latest), Value(WorkStatus.INCOMPLETE)))),
            Prefetch('task_pages', queryset=TaskPage.objects.filter(assigned_to=request.user, is_complete=False), to_attr='user_task_pages')
        )
    else:
        template_name = 'pms/project_list.html'
        latest = WorkUpdate.objects.filter(project=OuterRef('pk'), member=request.user).order_by('-created_at').values('status')[:1]
        project_list = project_list_base.annotate(work_status=Coalesce(Subquery(latest), Value(WorkStatus.INCOMPLETE))).prefetch_related(
            Prefetch('task_pages', queryset=TaskPage.objects.filter(assigned_to=request.user, is_complete=False), to_attr='user_task_pages')
        )

    paginator = Paginator(project_list, 9)
    projects_page = paginator.get_page(request.GET.get('page'))
    
    base_template = get_base_template(request.user)
    context = {
        'projects_page': projects_page, 'work_update_form': work_update_form,
        'project_status_update_form': project_status_update_form,
        'is_manager': is_manager, 'is_team_head': is_team_head, 'base_template': base_template
    }
    return render(request, template_name, context)

@login_required
@management_only_required
def add_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        doc_formset = ProjectDocumentFormSet(request.POST, request.FILES, prefix='documents')
        if form.is_valid() and doc_formset.is_valid():
            with transaction.atomic():
                p = form.save(commit=False); p.created_by = request.user; p.save()
                if p.team_head: ProjectMember.objects.get_or_create(project=p, user=p.team_head, defaults={'role': ProjectRole.DEVELOPER})
                for f in doc_formset: 
                    if f.cleaned_data and f.cleaned_data.get('document'): 
                        d=f.save(commit=False); d.project=p; d.uploaded_by=request.user; d.save()
            messages.success(request, "Project Created"); return redirect('project_list')
    else: form = ProjectForm(); doc_formset = ProjectDocumentFormSet(prefix='documents')
    return render(request, 'management/add_project.html', {'form': form, 'doc_formset': doc_formset})

@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    is_manager = request.user.role == User.Role.MANAGEMENT
    is_team_head = (request.user == project.team_head)
    
    if not (is_manager or is_team_head):
        messages.error(request, "Permission denied.")
        return redirect('project_list')

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid(): form.save(); messages.success(request, "Project Updated"); return redirect('project_list')
    else: form = ProjectForm(instance=project)
    return render(request, 'management/edit_project.html', {'form': form, 'project': project})

# --- PROJECT DETAIL VIEW ---
@login_required
def project_detail_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    is_mgmt = request.user.role == User.Role.MANAGEMENT; is_head = (request.user == project.team_head); is_mem = project.members.filter(id=request.user.id).exists()
    if not (is_mgmt or is_mem or is_head): return redirect('index')
    
    team = ProjectMember.objects.filter(project=project).select_related('user')
    
    # Calculate Total Time
    all_project_entries = DailyUpdateLineItem.objects.filter(project=project).values_list('time_spent', flat=True)
    grand_total_minutes = 0
    for t_str in all_project_entries:
        if not t_str: continue
        t_str = str(t_str).strip()
        try:
            if ':' in t_str:
                parts = t_str.split(':')
                grand_total_minutes += (int(parts[0]) * 60) + int(parts[1])
            else:
                grand_total_minutes += float(t_str) * 60
        except ValueError: pass
    gh = int(grand_total_minutes // 60); gm = int(grand_total_minutes % 60)
    project_total_time_str = f"{gh}h {gm}m"

    for member in team:
        member_entries = DailyUpdateLineItem.objects.filter(daily_update__user=member.user, project=project).values_list('time_spent', flat=True)
        total_minutes = 0
        for t_str in member_entries:
            if not t_str: continue
            t_str = str(t_str).strip()
            try:
                if ':' in t_str:
                    parts = t_str.split(':')
                    total_minutes += (int(parts[0]) * 60) + int(parts[1])
                else:
                    total_minutes += float(t_str) * 60
            except ValueError: pass
        h = int(total_minutes // 60); m = int(total_minutes % 60)
        member.total_time_calculated = f"{h}h {m}m"
        member.time_logs = DailyUpdateLineItem.objects.filter(daily_update__user=member.user, project=project).select_related('task_page', 'daily_update').order_by('-daily_update__date')

    docs = project.documents.select_related('uploaded_by').all()
    recommendations = project.updates.filter(category='RECOMMENDATION').select_related('user').prefetch_related('attachments').order_by('-created_at')

    doc_form = ProjectDocumentForm()
    rec_form = ProjectRecommendationForm()
    meet_form = ProjectMeetingForm(instance=project)
    attachment_formset = ProjectUpdateAttachmentFormSet(queryset=ProjectUpdateAttachment.objects.none(), prefix='attachments')

    if request.method == 'POST':
        if 'submit_document' in request.POST:
            doc_form = ProjectDocumentForm(request.POST, request.FILES)
            if doc_form.is_valid(): d=doc_form.save(commit=False); d.project=project; d.uploaded_by=request.user; d.save(); messages.success(request, "Doc Added"); return redirect('project_detail', project_id=project.id)
        
        elif 'submit_recommendation' in request.POST:
            if not is_mgmt: messages.error(request, "Permission denied"); return redirect('project_detail', project_id=project.id)
            rec_form = ProjectRecommendationForm(request.POST)
            attachment_formset = ProjectUpdateAttachmentFormSet(request.POST, request.FILES, prefix='attachments')
            if rec_form.is_valid() and attachment_formset.is_valid():
                with transaction.atomic():
                    u = rec_form.save(commit=False); u.project=project; u.user=request.user; u.category = 'RECOMMENDATION'; u.save()
                    for f in attachment_formset:
                         if f.cleaned_data and f.cleaned_data.get('file'): a=f.save(commit=False); a.project_update=u; a.save()
                messages.success(request, "Recommendation Posted"); return redirect('project_detail', project_id=project.id)

        elif 'submit_meet_link' in request.POST:
            if not (is_mgmt or is_head): 
                messages.error(request, "Permission denied"); 
                return redirect('project_detail', project_id=project.id)
            
            meet_form = ProjectMeetingForm(request.POST, instance=project)
            if meet_form.is_valid():
                meet_form.save()
                
                # --- NOTIFICATION LOGIC FIX ---
                users_to_notify = set()
                
                # 1. Add all team members (these are already User objects)
                for user_obj in project.members.all():
                    users_to_notify.add(user_obj)
                
                # 2. Add the Team Head if they exist and aren't me
                if project.team_head and project.team_head != request.user:
                    users_to_notify.add(project.team_head)
                
                email_recipients = []
                
                for u_notify in users_to_notify:
                    if u_notify != request.user: 
                        # Create Notification
                        Notification.objects.get_or_create(
                            user=u_notify, 
                            message=f"Meeting Link Added: {project.name}", 
                            link=project.google_meet_link, 
                            is_read=False
                        )
                        # Add to Email List
                        if u_notify.email: 
                            email_recipients.append(u_notify.email)
                
                # Send Emails
                if email_recipients:
                    try:
                        send_mail(
                            f"Meeting Invite: {project.name}", 
                            f"Join here: {project.google_meet_link}\n\n- Savithru PMS", 
                            settings.DEFAULT_FROM_EMAIL, 
                            email_recipients, 
                            fail_silently=True
                        )
                    except Exception as e:
                        print(f"Email Error: {e}")

                messages.success(request, "Link Updated & Notifications Sent")
                return redirect('project_detail', project_id=project.id)

    base = get_base_template(request.user)

    return render(request, 'pms/project_detail.html', {
        'project': project, 'team_members': team, 'documents': docs, 
        'recommendations': recommendations, 
        'doc_form': doc_form, 'rec_form': rec_form, 'meet_form': meet_form, 'attachment_formset': attachment_formset,
        'is_manager': is_mgmt, 'is_team_head': is_head, 'base_template': base,
        'project_total_time': project_total_time_str
    })

# --- THIS IS THE VIEW THAT WAS MISSING ---
@login_required
def project_meeting_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not (request.user.role == User.Role.MANAGEMENT or request.user == project.team_head or project.members.filter(id=request.user.id).exists()):
        return redirect('index')
    base = get_base_template(request.user)
    room = f"savithru-pms-{project.id}"
    return render(request, 'pms/project_meeting.html', {'project': project, 'jitsi_room_name': room, 'base_template': base})
# -----------------------------------------

@login_required
def end_project_meeting(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not (request.user.role == User.Role.MANAGEMENT or request.user == project.team_head):
        messages.error(request, "Permission denied.")
        return redirect('project_detail', project_id=project.id)
    
    if request.method == 'POST':
        project.google_meet_link = None
        project.save()
        messages.success(request, "Meeting Ended")
    return redirect('project_detail', project_id=project.id)

# --- CHAT & UPDATES ---
@login_required
def project_chat_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    is_mgmt = request.user.role == User.Role.MANAGEMENT; is_head = (request.user == project.team_head); is_mem = project.members.filter(id=request.user.id).exists()
    if not (is_mgmt or is_mem or is_head): return redirect('index')
    
    updates = project.updates.filter(Q(title__isnull=True) | Q(title='')).select_related('user').order_by('created_at')
    chat_form = ProjectChatForm()
    if request.method == 'POST':
        chat_form = ProjectChatForm(request.POST, request.FILES)
        if chat_form.is_valid():
            u = chat_form.save(commit=False); u.project=project; u.user=request.user; u.category = 'UPDATE'; u.save()
            users = {project.created_by, project.team_head}; 
            for m in project.members.all(): users.add(m.user)
            for u_notify in users:
                if u_notify and u_notify != request.user:
                     Notification.objects.get_or_create(user=u_notify, message=f"Chat from {request.user.username}", link=reverse('project_chat', args=[project.id]), is_read=False)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest': return JsonResponse({'status': 'success'}, status=200)
            return redirect('project_chat', project_id=project.id)
    
    base = get_base_template(request.user)
    return render(request, 'pms/project_chat.html', {'project': project, 'updates': updates, 'chat_form': chat_form, 'base_template': base})

@login_required
def project_updates_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    is_mgmt = request.user.role == User.Role.MANAGEMENT; is_head = (request.user == project.team_head); is_mem = project.members.filter(id=request.user.id).exists()
    if not (is_mgmt or is_mem or is_head): return redirect('index')

    # Filter: Only Updates
    updates = project.updates.filter(category='UPDATE').exclude(Q(title__isnull=True) | Q(title='')).select_related('user').prefetch_related('attachments').order_by('-created_at')
    
    can_post = (is_mgmt or is_head)
    update_form = ProjectUpdateForm() if can_post else None
    attachment_formset = ProjectUpdateAttachmentFormSet(queryset=ProjectUpdateAttachment.objects.none(), prefix='attachments') if can_post else None

    if request.method == 'POST' and can_post:
        update_form = ProjectUpdateForm(request.POST)
        attachment_formset = ProjectUpdateAttachmentFormSet(request.POST, request.FILES, prefix='attachments')
        if update_form.is_valid() and attachment_formset.is_valid():
            with transaction.atomic():
                u = update_form.save(commit=False); u.project=project; u.user=request.user
                u.category = 'UPDATE'
                u.save()
                for f in attachment_formset:
                    if f.cleaned_data and f.cleaned_data.get('file'): a=f.save(commit=False); a.project_update=u; a.save()
            users = {project.created_by, project.team_head}; 
            for m in project.members.all(): users.add(m.user)
            for u_notify in users:
                if u_notify and u_notify != request.user:
                     Notification.objects.get_or_create(user=u_notify, message=f"Update: {u.title}", link=reverse('project_updates', args=[project.id]), is_read=False)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html = render_to_string('pms/partials/timeline_item.html', {'update': u, 'request': request})
                return JsonResponse({'status': 'success', 'html': html})
            return redirect('project_updates', project_id=project.id)

    base = get_base_template(request.user)
    return render(request, 'pms/project_updates.html', {'project': project, 'updates': updates, 'update_form': update_form, 'attachment_formset': attachment_formset, 'can_post_update': can_post, 'is_manager': is_mgmt, 'base_template': base})

# --- TASK & TEAM VIEWS ---
@login_required
@team_head_only_required
def assign_project_pages_view(request, project, user_id, **kwargs):
    member_user = get_object_or_404(User, id=user_id)
    existing = TaskPage.objects.filter(project=project, assigned_to=member_user)
    if request.method == 'POST':
        formset = TaskPageFormSet(request.POST, prefix='tasks')
        if formset.is_valid():
            with transaction.atomic():
                existing.delete()
                for f in formset:
                    if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('page_name'):
                        TaskPage.objects.create(project=project, assigned_to=member_user, page_name=f.cleaned_data['page_name'])
            return redirect('manage_project_team', project_id=project.id)
    else:
        data = [{'page_name': t.page_name} for t in existing] or [{}]
        formset = TaskPageFormSet(prefix='tasks', initial=data)
    return render(request, 'management/assign_project.html', {'formset': formset, 'project': project, 'member': member_user})

@login_required
def employee_task_list(request):
    return redirect('project_list')

@login_required
@require_POST
def complete_task_page_view(request, task_id):
    t = get_object_or_404(TaskPage, id=task_id, assigned_to=request.user)
    t.is_complete = True; t.save(); messages.success(request, "Task Complete")
    return redirect('project_list')

@login_required
@require_POST
def employee_work_update_view(request, project_id):
    p = get_object_or_404(Project, id=project_id)
    f = WorkUpdateForm(request.POST)
    if f.is_valid():
        WorkUpdate.objects.update_or_create(project=p, member=request.user, defaults={'status': f.cleaned_data['status'], 'remarks': f.cleaned_data['remarks']})
    return redirect('project_list')

@login_required
@team_head_only_required
@require_POST
def team_head_project_update_view(request, project, **kwargs):
    f = ProjectStatusUpdateForm(request.POST, instance=project)
    if f.is_valid(): f.save()
    return redirect('project_list')

@login_required
@team_head_only_required
def pm_toggle_task_status(request, task_id, project=None):
    task = get_object_or_404(TaskPage, id=task_id, project=project)
    task.is_complete = not task.is_complete
    task.save()
    status = "Complete" if task.is_complete else "Incomplete"
    if task.assigned_to != request.user:
        Notification.objects.create(user=task.assigned_to, message=f"Task '{task.page_name}' marked {status}", link=reverse('project_list'))
    messages.success(request, f"Task marked {status}")
    return redirect('manage_project_team', project_id=project.id)

@login_required
@team_head_only_required
def manage_project_team(request, project, **kwargs):
    tasks_prefetch = Prefetch('user__task_pages', queryset=TaskPage.objects.filter(project=project), to_attr='project_tasks')
    members = ProjectMember.objects.filter(project=project).select_related('user').prefetch_related(tasks_prefetch).exclude(user=project.team_head)
    
    form = ProjectMemberForm()

    if request.method == 'POST':
        if 'delete_member' in request.POST:
            try:
                member = ProjectMember.objects.get(id=request.POST['delete_member'], project=project)
                member.delete()
                messages.success(request, "Member removed.")
            except ProjectMember.DoesNotExist:
                messages.error(request, "Failed to remove member.")
            return redirect('manage_project_team', project_id=project.id)
        
        form = ProjectMemberForm(request.POST)
        if form.is_valid(): 
            user_to_add = form.cleaned_data['user']
            if user_to_add == project.team_head:
                messages.error(request, "User is already Team Head.")
            elif ProjectMember.objects.filter(project=project, user=user_to_add).exists():
                 messages.warning(request, "User already in team.")
            else:
                ProjectMember.objects.create(project=project, user=user_to_add, role=form.cleaned_data['role'])
                messages.success(request, "Member added.")
            return redirect('manage_project_team', project_id=project.id)
    
    return render(request, 'management/manage_team.html', {'project': project, 'current_members': members, 'form': form})

# --- DAILY & MISC VIEWS ---
@login_required
def add_daily_update_view(request):
    today = datetime.date.today()
    if request.method == 'POST':
        form = DailyUpdateForm(request.POST); formset = DailyUpdateLineItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            d = form.save(commit=False); d.user = request.user; d.date = today; d.save()
            formset.instance = d; formset.save(); return redirect('calendar_view')
    else: form = DailyUpdateForm(); formset = DailyUpdateLineItemFormSet()
    
    projs = Project.objects.filter(Q(members=request.user) | Q(team_head=request.user)).distinct()
    tasks = TaskPage.objects.filter(assigned_to=request.user)
    for f in formset: f.fields['project'].queryset = projs; f.fields['task_page'].queryset = tasks
    formset.empty_form.fields['project'].queryset = projs
    formset.empty_form.fields['task_page'].queryset = tasks

    base = get_base_template(request.user)
    return render(request, 'pms/add_daily_update.html', {'form': form, 'formset': formset, 'base_template': base})

@login_required
def daily_update_calendar_view(request, year=None, month=None):
    today = datetime.date.today()
    if not year: year, month = today.year, today.month
    current_date = datetime.date(year, month, 1)
    next_month = (current_date + datetime.timedelta(days=32)).replace(day=1)
    prev_month = (current_date - datetime.timedelta(days=1)).replace(day=1)
    
    updates = DailyUpdate.objects.filter(user=request.user, date__year=year, date__month=month).prefetch_related('line_items__project', 'line_items__task_page')
    cal = calendar.Calendar(); month_days = cal.monthdayscalendar(year, month)
    
    updates_dict = {}
    for u in updates:
        day = u.date.day
        if day not in updates_dict:
            updates_dict[day] = []
        updates_dict[day].append(u)
    
    base = get_base_template(request.user)
    return render(request, 'pms/daily_update_calendar.html', {
        'month_name': current_date.strftime('%B'), 'year': year, 'month_days': month_days, 'today_num': today.day,
        'updates_dict': updates_dict, 'next_month_date': next_month, 'prev_month_date': prev_month, 'base_template': base
    })

@login_required
def manager_daily_update_list_view(request):
    today = datetime.date.today()
    latest = DailyUpdate.objects.filter(user=OuterRef('pk'), date=today).order_by('-created_at').values('description')[:1]
    count = DailyUpdate.objects.filter(user=OuterRef('pk'), date=today).values('user').annotate(cnt=Count('id')).values('cnt')
    employees = User.objects.filter(role=User.Role.EMPLOYEE).annotate(latest_update_desc=Subquery(latest), update_count=Subquery(count)).order_by('first_name')
    return render(request, 'management/daily_update_list.html', {'employees': employees, 'today': today, 'base_template': 'base_management.html'})

@login_required
def load_tasks_for_project(request):
    pid = request.GET.get('project_id')
    tasks = TaskPage.objects.filter(project_id=pid, assigned_to=request.user)
    return render(request, 'pms/partials/task_dropdown_list_options.html', {'tasks': tasks})

@login_required
def employee_calendar_view(request, user_id, year=None, month=None):
    if not user_is_project_admin_or_manager(request.user): return redirect('index')
    target_user = get_object_or_404(User, id=user_id)
    today = datetime.date.today()
    if not year: year, month = today.year, today.month
    current_date = datetime.date(year, month, 1)
    next_month = (current_date + datetime.timedelta(days=32)).replace(day=1)
    prev_month = (current_date - datetime.timedelta(days=1)).replace(day=1)
    
    updates = DailyUpdate.objects.filter(user=target_user, date__year=year, date__month=month).prefetch_related('line_items__project', 'line_items__task_page')
    cal = calendar.Calendar(); month_days = cal.monthdayscalendar(year, month)
    updates_dict = {}
    for u in updates:
        day = u.date.day
        if day not in updates_dict: updates_dict[day] = []
        updates_dict[day].append(u)
    
    base = 'base_management.html'
    return render(request, 'pms/daily_update_calendar.html', {
        'month_name': current_date.strftime('%B'), 'year': year, 'month_days': month_days, 'today_num': today.day,
        'updates_dict': updates_dict, 'next_month_date': next_month, 'prev_month_date': prev_month, 'base_template': base,
        'viewing_employee': target_user
    })

@login_required
def manage_employees_view(request):
    employees = User.objects.filter(role=User.Role.EMPLOYEE).order_by('first_name')
    form = EmployeeCreationForm()
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee created successfully!")
            return redirect('manage_employees')
        else:
            messages.error(request, "Failed to create employee.")
    return render(request, 'management/manage_employees.html', {'employees': employees, 'form': form})

@login_required
def chat_view(request, receiver_id=None): return redirect('project_list')

@login_required
def issue_list_view(request):
    if request.user.role == User.Role.MANAGEMENT:
        issues = Issue.objects.filter(status=IssueStatus.PENDING).select_related('user')
        template_name = 'management/issue_list.html'
    else:
        issues = Issue.objects.filter(user=request.user).select_related('user')
        template_name = 'employee/my_issues.html'
    base = get_base_template(request.user)
    return render(request, template_name, {'issues': issues, 'base_template': base})

@login_required
def submit_issue_view(request):
    if request.method == 'POST':
        form = IssueForm(request.POST, request.FILES)
        if form.is_valid():
            issue = form.save(commit=False); issue.user = request.user; issue.save()
            managers = User.objects.filter(role=User.Role.MANAGEMENT)
            for m in managers: Notification.objects.create(user=m, message=f"Issue from {request.user.username}", link=reverse('issue_detail', args=[issue.id]))
            messages.success(request, "Issue Submitted"); return redirect('issues')
    else: form = IssueForm()
    base = get_base_template(request.user)
    return render(request, 'employee/submit_issue.html', {'form': form, 'base_template': base})

@login_required
@management_only_required
def issue_detail_view(request, issue_id):
    issue = get_object_or_404(Issue.objects.select_related('user'), id=issue_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept': issue.status = IssueStatus.ACCEPTED
        elif action == 'decline': issue.status = IssueStatus.DECLINED
        elif action == 'wfh': issue.status = IssueStatus.WFH_APPROVED
        issue.save()
        Notification.objects.create(user=issue.user, message=f"Your issue updated: {issue.status}", link=reverse('issues'))
        messages.success(request, "Issue Updated"); return redirect('issues')
    return render(request, 'management/issue_detail.html', {'issue': issue, 'base_template': 'base_management.html'})

@login_required
def notification_list_view(request):
    current_user = request.user
    notifications_list = list(Notification.objects.filter(user=current_user))
    Notification.objects.filter(user=current_user, is_read=False).update(is_read=True)
    base = get_base_template(request.user)
    return render(request, 'pms/notification_list.html', {'notifications': notifications_list, 'base_template': base})

@login_required
def daily_update_view(request):
    # TEAM HEADS are redirected to 'add_daily_update' just like Employees
    if request.user.role == User.Role.MANAGEMENT:
        return redirect('manager_daily_updates')
    else:
        return redirect('add_daily_update')

@login_required
@require_POST
def pm_update_task_status_view(request, task_id):
    t = get_object_or_404(TaskPage, id=task_id); 
    if request.user != t.project.team_head: return JsonResponse({}, status=403)
    data = json.loads(request.body); status = data.get('status')
    t.is_complete = (status == 'complete'); t.save()
    return JsonResponse({'status': 'success'})