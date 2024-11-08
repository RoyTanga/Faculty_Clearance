from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.

class User(AbstractUser):
    is_faculty = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class ClearanceSet(models.Model):
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='clearance_sets')
    name = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=9)  # Format: "YYYY-YYYY"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('faculty', 'name')

    def __str__(self):
        return f"{self.name} - {self.academic_year} ({self.faculty.username})"

class Document(models.Model):
    CLEARANCE_TYPES = [
        ('ADMIN', 'Admin Clearance'),
        ('ACADEMIC', 'Academic'),
        ('FINANCIAL', 'Financial'),
        ('LIBRARY', 'Library'),
        ('RESEARCH', 'Research'),
        ('EQUIPMENT', 'Equipment'),
    ]

    CLEARANCE_STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    clearance_set = models.ForeignKey(ClearanceSet, on_delete=models.CASCADE, related_name='documents')
    clearance_type = models.CharField(max_length=20, choices=CLEARANCE_TYPES)
    file = models.FileField(upload_to='documents/')
    file_name = models.CharField(max_length=255)
    clearance_status = models.CharField(max_length=20, choices=CLEARANCE_STATUS, default='PENDING')
    predicted_status = models.CharField(max_length=20, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.file_name and self.file:
            self.file_name = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_clearance_type_display()} - {self.file_name}"

    def get_clearance_type_display(self):
        return dict(self.CLEARANCE_TYPES)[self.clearance_type]
