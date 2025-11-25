from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # Add your custom fields to the "Edit User" page
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'profile_photo')}),
    )
    
    # Add your custom fields to the "Add User" page
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role', 'profile_photo')}),
    )

    # Columns to show in the list of users
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    
    # Filters on the right side
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    
    # Search bar
    search_fields = ('username', 'first_name', 'last_name', 'email')

# Register the model
admin.site.register(User, CustomUserAdmin)