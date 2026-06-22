from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.academic.models import Class, Subject, AcademicYear, Term
from apps.grading.models import GradingScale


class Command(BaseCommand):
    help = 'Seeds the system with default data for first-time setup'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding system data...')

        # Create super admin if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@jinjasss.sc.ug',
                password='jinja2026',
                role='super_admin',
                must_change_password=True,
            )
            self.stdout.write(self.style.SUCCESS('Super admin created (admin / jinja2026)'))

        # Create O-Level classes
        o_level_classes = [
            ('Senior 1', 'O-Level', 1),
            ('Senior 2', 'O-Level', 2),
            ('Senior 3', 'O-Level', 3),
            ('Senior 4', 'O-Level', 4),
        ]
        for name, level, order in o_level_classes:
            Class.objects.get_or_create(
                name=name,
                defaults={'level_type': level, 'sort_order': order}
            )
        self.stdout.write('O-Level classes seeded')

        # Create A-Level classes
        a_level_classes = [
            ('Senior 5', 'A-Level', 5),
            ('Senior 6', 'A-Level', 6),
        ]
        for name, level, order in a_level_classes:
            Class.objects.get_or_create(
                name=name,
                defaults={'level_type': level, 'sort_order': order}
            )
        self.stdout.write('A-Level classes seeded')

        # Create subjects
        subjects = [
            ('ENG', 'English Language', 'compulsory'),
            ('MATH', 'Mathematics', 'compulsory'),
            ('BIO', 'Biology', 'compulsory'),
            ('CHEM', 'Chemistry', 'compulsory'),
            ('PHY', 'Physics', 'compulsory'),
            ('GEO', 'Geography', 'compulsory'),
            ('HIST', 'History', 'compulsory'),
            ('CRE', 'Christian Religious Education', 'compulsory'),
            ('LIT', 'Literature in English', 'compulsory'),
            ('GP', 'General Paper', 'compulsory'),
            ('F/A', 'Fine Art', 'optional'),
            ('COMP', 'Computer Studies', 'optional'),
            ('FRE', 'French', 'optional'),
            ('KISW', 'Kiswahili', 'optional'),
            ('AGRIC', 'Agriculture', 'optional'),
            ('ENT', 'Entrepreneurship', 'optional'),
            ('F/N', 'Food & Nutrition', 'optional'),
            ('T/D', 'Technical Drawing', 'optional'),
            ('MUS', 'Music', 'optional'),
            ('IRE', 'Islamic Religious Education', 'optional'),
            ('ICT', 'Information Communication Technology', 'subsidiary'),
            ('SUB-MATH', 'Subsidiary Mathematics', 'subsidiary'),
            ('ECON', 'Economics', 'principal'),
            ('ARABIC', 'Arabic', 'principal'),
            ('LUS', 'Lusonga', 'principal'),
            ('LUG', 'Luganda', 'principal'),
        ]
        for code, name, category in subjects:
            Subject.objects.get_or_create(
                code=code,
                defaults={'name': name, 'category': category}
            )
        self.stdout.write(f'{len(subjects)} subjects seeded')

        # Create academic year
        from django.utils import timezone
        current_year = timezone.now().year
        academic_year, created = AcademicYear.objects.get_or_create(
            name=str(current_year),
            defaults={
                'is_current': True,
                'start_date': f'{current_year}-02-01',
                'end_date': f'{current_year}-12-15',
            }
        )
        if created:
            terms_data = [
                ('Term 1', f'{current_year}-02-01', f'{current_year}-05-15', True),
                ('Term 2', f'{current_year}-05-25', f'{current_year}-08-30', False),
                ('Term 3', f'{current_year}-09-10', f'{current_year}-12-15', False),
            ]
            for name, start, end, is_current in terms_data:
                Term.objects.create(
                    academic_year=academic_year,
                    name=name,
                    start_date=start,
                    end_date=end,
                    is_current=is_current,
                )
            self.stdout.write(f'Academic year {current_year} created with 3 terms')

        # Create grading scale
        scales = [
            ('A', 80, 100, 'Excellent'),
            ('B+', 75, 79, 'Very Good'),
            ('B', 70, 74, 'Good'),
            ('C', 60, 69, 'Credit'),
            ('D', 50, 59, 'Pass'),
            ('F', 0, 49, 'Fail'),
        ]
        for letter, min_p, max_p, remark in scales:
            GradingScale.objects.get_or_create(
                grade_letter=letter,
                defaults={'min_percent': min_p, 'max_percent': max_p, 'remark': remark}
            )
        self.stdout.write('Grading scale seeded')

        self.stdout.write(self.style.SUCCESS('System seeding complete!'))