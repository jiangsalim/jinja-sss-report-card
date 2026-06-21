import pandas as pd
from django.db import transaction
from apps.academic.models import Class, Stream, Subject, AcademicYear, ClassCompulsorySubject
from .models import Student, Enrollment, StudentSubject


class StudentImportService:

    def __init__(self, file_path, academic_year_id):
        self.file_path = file_path
        self.academic_year = AcademicYear.objects.get(id=academic_year_id)
        self.errors = []
        self.created_count = 0
        self.updated_count = 0
        self.skipped_count = 0

    def process(self):
        df = pd.read_csv(self.file_path)

        for index, row in df.iterrows():
            try:
                with transaction.atomic():
                    self._process_row(row, index + 2)
            except Exception as e:
                self.errors.append(f"Row {index + 2}: {str(e)}")

        return {
            'created': self.created_count,
            'updated': self.updated_count,
            'skipped': self.skipped_count,
            'errors': self.errors,
        }

    def _process_row(self, row, row_number):
        admission_no = str(row.get('admission_no', '')).strip()
        first_name = str(row.get('first_name', '')).strip()
        last_name = str(row.get('last_name', '')).strip()
        gender = str(row.get('gender', 'M')).strip().upper()
        class_name = str(row.get('class_name', '')).strip()
        stream_name = str(row.get('stream_name', '')).strip()
        optional_subjects = str(row.get('optional_subjects', '')).strip()
        parent_name = str(row.get('parent_name', '')).strip()
        parent_phone = str(row.get('parent_phone', '')).strip()
        parent_email = str(row.get('parent_email', '')).strip()

        if not admission_no or not first_name or not class_name or not stream_name:
            self.skipped_count += 1
            self.errors.append(f"Row {row_number}: Missing required fields")
            return

        # Find or create class
        class_obj, _ = Class.objects.get_or_create(
            name=class_name,
            defaults={'level_type': 'O-Level', 'sort_order': int(class_name[-1]) if class_name[-1].isdigit() else 1}
        )

        # Find or create stream
        stream, _ = Stream.objects.get_or_create(
            class_obj=class_obj,
            name=stream_name
        )

        # Create or update student
        student, created = Student.objects.update_or_create(
            admission_no=admission_no,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'gender': gender,
                'parent_name': parent_name,
                'parent_phone': parent_phone,
                'parent_email': parent_email,
            }
        )

        if created:
            self.created_count += 1
        else:
            self.updated_count += 1

        # Enroll student in stream
        Enrollment.objects.get_or_create(
            student=student,
            academic_year=self.academic_year,
            defaults={'stream': stream}
        )

        # Assign compulsory subjects
        compulsory_links = ClassCompulsorySubject.objects.filter(class_obj=class_obj)
        for link in compulsory_links:
            StudentSubject.objects.get_or_create(
                student=student,
                subject=link.subject,
                academic_year=self.academic_year,
                defaults={
                    'stream': stream,
                    'subject_type': 'compulsory'
                }
            )

        # Assign optional subjects from CSV
        if optional_subjects and optional_subjects.lower() != 'nan':
            codes = [c.strip().upper() for c in optional_subjects.split(',')]
            for code in codes:
                try:
                    subject = Subject.objects.get(code=code)
                    StudentSubject.objects.get_or_create(
                        student=student,
                        subject=subject,
                        academic_year=self.academic_year,
                        defaults={
                            'stream': stream,
                            'subject_type': 'optional'
                        }
                    )
                except Subject.DoesNotExist:
                    self.errors.append(f"Row {row_number}: Subject code '{code}' not found")