from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Login Page
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    
    # --- FIXED LOGOUT URL ---
    path('logout/', views.logout_view, name='logout'), # Points to your new view
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
]