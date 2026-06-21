from django.db import models
from apps.academic.models import Stream, Subject, AcademicYear


class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    admission_no = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    parent_name = models.CharField(max_length=100, blank=True)
    parent_phone = models.CharField(max_length=20, blank=True)
    parent_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        ordering = ['admission_no']

    def __str__(self):
        return f"{self.admission_no} - {self.first_name} {self.last_name}"

    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('transferred', 'Transferred'),
        ('withdrawn', 'Withdrawn'),
        ('graduated', 'Graduated'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'enrollments'
        unique_together = ['student', 'academic_year']

    def __str__(self):
        return f"{self.student.full_name()} - {self.stream} ({self.academic_year})"


class StudentSubject(models.Model):
    SUBJECT_TYPE_CHOICES = [
        ('compulsory', 'Compulsory'),
        ('optional', 'Optional'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    subject_type = models.CharField(max_length=20, choices=SUBJECT_TYPE_CHOICES)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)

    class Meta:
        db_table = 'student_subjects'
        unique_together = ['student', 'subject', 'academic_year']

    def __str__(self):
        return f"{self.student.full_name()} - {self.subject.name} ({self.subject_type})"