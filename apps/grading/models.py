from django.db import models
from django.conf import settings
from apps.students.models import StudentSubject
from apps.academic.models import Term


class Assessment(models.Model):
    """A single assessment created by the teacher for their class."""
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'}
    )
    student_subject = models.ForeignKey(
        StudentSubject,
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Weight as percentage (e.g., 30 for 30%)"
    )
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('locked', 'Locked')],
        default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assessments'

    def save(self, *args, **kwargs):
        # Auto-calculate percentage when marks are entered
        if self.marks_obtained is not None and self.max_marks > 0:
            self.percentage = round((self.marks_obtained / self.max_marks) * 100, 2)
        else:
            self.percentage = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student_subject.student.full_name()} - {self.name}"


class GradeEntry(models.Model):
    """Final calculated grade for a student in a subject for a term."""
    student_subject = models.ForeignKey(
        StudentSubject,
        on_delete=models.CASCADE,
        related_name='grade_entries'
    )
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'}
    )
    final_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    letter_grade = models.CharField(max_length=3, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('locked', 'Locked')],
        default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'grade_entries'
        unique_together = ['student_subject', 'term']

    def __str__(self):
        return f"{self.student_subject.student.full_name()} - {self.student_subject.subject.name}"


class GradingScale(models.Model):
    """School grading scale."""
    grade_letter = models.CharField(max_length=3, unique=True)
    min_percent = models.DecimalField(max_digits=5, decimal_places=2)
    max_percent = models.DecimalField(max_digits=5, decimal_places=2)
    remark = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'grading_scale'
        ordering = ['-min_percent']

    def __str__(self):
        return f"{self.grade_letter}: {self.min_percent}% - {self.max_percent}%"