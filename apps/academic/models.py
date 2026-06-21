from django.db import models


class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academic_years'
        ordering = ['-name']

    def __str__(self):
        return self.name


class Term(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    name = models.CharField(max_length=20)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        db_table = 'terms'
        unique_together = ['academic_year', 'name']
        ordering = ['academic_year', 'start_date']

    def __str__(self):
        return f"{self.name} - {self.academic_year.name}"


class Class(models.Model):
    LEVEL_CHOICES = [
        ('O-Level', 'O-Level'),
        ('A-Level', 'A-Level'),
    ]

    name = models.CharField(max_length=20, unique=True)
    level_type = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='O-Level')
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'classes'
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Classes'

    def __str__(self):
        return self.name


class Stream(models.Model):
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='streams')
    name = models.CharField(max_length=10)
    capacity = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'streams'
        unique_together = ['class_obj', 'name']
        ordering = ['class_obj', 'name']

    def __str__(self):
        return f"{self.class_obj.name}-{self.name}"


class Subject(models.Model):
    CATEGORY_CHOICES = [
        ('compulsory', 'Compulsory'),
        ('optional', 'Optional'),
        ('principal', 'Principal'),
        ('subsidiary', 'Subsidiary'),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='compulsory')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subjects'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ClassCompulsorySubject(models.Model):
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='compulsory_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        db_table = 'class_compulsory_subjects'
        unique_together = ['class_obj', 'subject']

    def __str__(self):
        return f"{self.class_obj.name} - {self.subject.name}"
    

class StreamOfficials(models.Model):
    stream = models.OneToOneField(Stream, on_delete=models.CASCADE, related_name='officials')
    class_teacher = models.CharField(max_length=100, blank=True)
    head_of_academics = models.CharField(max_length=100, blank=True)
    head_teacher = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stream_officials'

    def __str__(self):
        return f"Officials for {self.stream}"