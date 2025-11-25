from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGEMENT = "MANAGEMENT", "Management"
        EMPLOYEE = "EMPLOYEE", "Employee"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.EMPLOYEE)
    
    # --- ADD THIS FIELD ---
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    
    def __str__(self):
        return self.username