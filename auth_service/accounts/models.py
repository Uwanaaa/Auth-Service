from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db import models

class User(AbstractUser):
    """
    Custom user model that uses email as the unique identifier instead of username.
    """
    email = models.EmailField(unique=True, blank=False, null=False , verbose_name=_('email address'))
    full_name = models.CharField(max_length=255, blank=False, null=False, verbose_name=_('full name'))
    

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
        ]
        ordering = ['id']

    def __str__(self):
        return self.username
        
        