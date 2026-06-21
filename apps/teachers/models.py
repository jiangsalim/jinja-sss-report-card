from django.db import models
from django.conf import settings
from apps.academic.models import Stream, Subject, AcademicYear, Term


class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teaching_assignments',
        limit_choices_to={'role': 'teacher'}
    )
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)

    class Meta:
        db_table = 'teacher_assignments'
        unique_together = ['teacher', 'stream', 'subject', 'academic_year', 'term']

    def __str__(self):
        return f"{self.teacher.get_full_name()} - {self.stream} - {self.subject.name}"