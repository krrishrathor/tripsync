from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # AbstractUser already provides username, first_name, last_name, email, password, etc.
    email = models.EmailField(unique=True)
    profile_image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # We will use email for authentication but keep username for display/slugs if needed
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        return self.email
