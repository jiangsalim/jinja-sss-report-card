from django.db import migrations


def seed_classes(apps, schema_editor):
    Class = apps.get_model('academic', 'Class')

    classes = [
        {'name': 'Senior 1', 'level_type': 'O-Level', 'sort_order': 1},
        {'name': 'Senior 2', 'level_type': 'O-Level', 'sort_order': 2},
        {'name': 'Senior 3', 'level_type': 'O-Level', 'sort_order': 3},
        {'name': 'Senior 4', 'level_type': 'O-Level', 'sort_order': 4},
    ]

    for class_data in classes:
        Class.objects.get_or_create(
            name=class_data['name'],
            defaults={
                'level_type': class_data['level_type'],
                'sort_order': class_data['sort_order']
            }
        )


def seed_subjects(apps, schema_editor):
    Subject = apps.get_model('academic', 'Subject')

    subjects = [
        # Compulsory subjects
        {'code': 'ENG', 'name': 'English Language', 'category': 'compulsory'},
        {'code': 'MATH', 'name': 'Mathematics', 'category': 'compulsory'},
        {'code': 'BIO', 'name': 'Biology', 'category': 'compulsory'},
        {'code': 'CHEM', 'name': 'Chemistry', 'category': 'compulsory'},
        {'code': 'PHY', 'name': 'Physics', 'category': 'compulsory'},
        {'code': 'GEO', 'name': 'Geography', 'category': 'compulsory'},
        {'code': 'HIST', 'name': 'History', 'category': 'compulsory'},
        {'code': 'CRE', 'name': 'Christian Religious Education', 'category': 'compulsory'},
        {'code': 'LIT', 'name': 'Literature in English', 'category': 'compulsory'},

        # Optional subjects
        {'code': 'F/A', 'name': 'Fine Art', 'category': 'optional'},
        {'code': 'COMP', 'name': 'Computer Studies', 'category': 'optional'},
        {'code': 'FRE', 'name': 'French', 'category': 'optional'},
        {'code': 'KISW', 'name': 'Kiswahili', 'category': 'optional'},
        {'code': 'AGRIC', 'name': 'Agriculture', 'category': 'optional'},
        {'code': 'ENT', 'name': 'Entrepreneurship', 'category': 'optional'},
        {'code': 'F/N', 'name': 'Food & Nutrition', 'category': 'optional'},
        {'code': 'T/D', 'name': 'Technical Drawing', 'category': 'optional'},
        {'code': 'MUS', 'name': 'Music', 'category': 'optional'},
        {'code': 'IRE', 'name': 'Islamic Religious Education', 'category': 'optional'},
    ]

    for subject_data in subjects:
        Subject.objects.get_or_create(
            code=subject_data['code'],
            defaults={
                'name': subject_data['name'],
                'category': subject_data['category']
            }
        )


def seed_academic_year(apps, schema_editor):
    AcademicYear = apps.get_model('academic', 'AcademicYear')
    Term = apps.get_model('academic', 'Term')

    year, _ = AcademicYear.objects.get_or_create(
        name='2026',
        defaults={
            'is_current': True,
            'start_date': '2026-02-01',
            'end_date': '2026-12-15'
        }
    )

    terms = [
        {'name': 'Term 1', 'start_date': '2026-02-01', 'end_date': '2026-05-15'},
        {'name': 'Term 2', 'start_date': '2026-05-25', 'end_date': '2026-08-30'},
        {'name': 'Term 3', 'start_date': '2026-09-10', 'end_date': '2026-12-15'},
    ]

    for i, term_data in enumerate(terms):
        Term.objects.get_or_create(
            academic_year=year,
            name=term_data['name'],
            defaults={
                'start_date': term_data['start_date'],
                'end_date': term_data['end_date'],
                'is_current': (i == 0)
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_classes),
        migrations.RunPython(seed_subjects),
        migrations.RunPython(seed_academic_year),
    ]