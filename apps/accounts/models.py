from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='teacher')
    phone = models.CharField(max_length=20, blank=True)
    must_change_password = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_users'
    )

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"