from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)  # Increased from 30 to 150
    last_name = models.CharField(max_length=150)  # Increased from 30 to 150
    first_name = models.CharField(max_length=150)  # Increased from 30 to 150
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=128)  # Increased from 30 to 128
    avatarUrl = models.CharField(blank=True, null=True, default="avatar1.jpeg")  # New field for avatar

    
    def __str__(self):
        return self.username