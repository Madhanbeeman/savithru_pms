from django.urls import path
from . import views

urlpatterns = [
    # --- Main ---
    path('', views.index_view, name='index'),
    path('placeholder/', views.placeholder_view, name='placeholder'),

    # --- Dashboards ---
    path('dashboard/management/', views.management_dashboard, name='management_dashboard'),
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'), 
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),

    # --- Project ---
    path('projects/', views.project_list_view, name='project_list'),
    path('projects/add/', views.add_project, name='add_project'),
    path('project/<int:project_id>/', views.project_detail_view, name='project_detail'),
    path('project/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('project/<int:project_id>/meet/', views.project_meeting_view, name='project_meeting'),
    
    # --- Chat & Updates ---
    path('project/<int:project_id>/chat/', views.project_chat_view, name='project_chat'),
    path('project/<int:project_id>/updates/', views.project_updates_view, name='project_updates'),

    # --- Team & Task ---
    path('project/<int:project_id>/team/', views.manage_project_team, name='manage_project_team'),
    path('project/<int:project_id>/team/assign-project/<int:user_id>/', views.assign_project_pages_view, name='assign_project_pages'),

    # --- Employee Actions ---
    path('my-projects/', views.project_list_view, name='employee_project_list'), 
    path('my-tasks/', views.employee_task_list, name='employee_task_list'), 
    path('employees/', views.manage_employees_view, name='manage_employees'),
    
    path('task-page/<int:task_id>/complete/', views.complete_task_page_view, name='complete_task_page'),
    path('task-page/<int:task_id>/pm-update-status/', views.pm_update_task_status_view, name='pm_update_task_status'),
    path('project/<int:project_id>/update-status/', views.employee_work_update_view, name='employee_work_update'),
    path('project/<int:project_id>/pm-update-status/', views.team_head_project_update_view, name='team_head_project_update'),
    
    # --- Daily Updates & Calendar ---
    # 1. Generic URL (Redirects based on role)
    path('daily-updates/', views.daily_update_view, name='daily_updates'),
    
    # 2. Specific URLs
    path('daily-update/add/', views.add_daily_update_view, name='add_daily_update'),
    path('calendar/', views.daily_update_calendar_view, name='calendar_view'),
    path('calendar/<int:year>/<int:month>/', views.daily_update_calendar_view, name='calendar_view_nav'),
    
    # 3. Manager Overview
    path('daily-updates/overview/', views.manager_daily_update_list_view, name='manager_daily_updates'),
    
    # 4. AJAX Task Loader
    path('ajax/load-tasks/', views.load_tasks_for_project, name='ajax_load_tasks'),
    
    # 5. Manager viewing Employee Calendar
    path('daily-updates/<int:user_id>/', views.employee_calendar_view, name='employee_calendar'), 
    path('daily-updates/<int:user_id>/<int:year>/<int:month>/', views.employee_calendar_view, name='employee_calendar_nav'), 

    # --- Issues ---
    path('issues/', views.issue_list_view, name='issues'),
    path('issues/submit/', views.submit_issue_view, name='submit_issue'),
    path('issues/<int:issue_id>/', views.issue_detail_view, name='issue_detail'),
    path('project/<int:project_id>/meet/end/', views.end_project_meeting, name='end_project_meeting'),
    
    # --- Notifications ---
    path('notifications/', views.notification_list_view, name='notification_list'),
    path('project/<int:project_id>/task/<int:task_id>/toggle/', views.pm_toggle_task_status, name='pm_toggle_task_status'),
]