from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, logout # Added logout here
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserProfileForm
from .models import User

@login_required
def profile_view(request):
    user = request.user
    
    # Determine base template based on ROLE
    if user.role == User.Role.MANAGEMENT:
        base_template = 'base_management.html'
    else:
        # Team Heads are technically "Employees" in the role system, so they get this
        base_template = 'base_employee.html'

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)

    context = {
        'form': form,
        'base_template': base_template
    }
    return render(request, 'users/profile.html', context)

@login_required
def change_password_view(request):
    user = request.user
    
    if user.role == User.Role.MANAGEMENT:
        base_template = 'base_management.html'
    else:
        base_template = 'base_employee.html'

    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            # Updating the password logs out all other sessions
            # This function keeps the current user logged in
            update_session_auth_hash(request, user) 
            messages.success(request, "Your password was successfully updated!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = PasswordChangeForm(user)
        
    context = {
        'form': form,
        'base_template': base_template
    }
    return render(request, 'users/change_password.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')