from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db import models as db_models
from apps.academic.models import Class, Stream, Subject, AcademicYear, Term, ClassCompulsorySubject
from .models import Student, Enrollment, StudentSubject
from .services import StudentImportService
import os
import pandas as pd


@login_required
def student_list(request):
    class_filter = request.GET.get('class', '')
    stream_filter = request.GET.get('stream', '')
    search = request.GET.get('search', '')

    students = Student.objects.all()

    if class_filter:
        students = students.filter(enrollments__stream__class_obj_id=class_filter)
    if stream_filter:
        students = students.filter(enrollments__stream_id=stream_filter)
    if search:
        students = students.filter(
            db_models.Q(first_name__icontains=search) |
            db_models.Q(last_name__icontains=search) |
            db_models.Q(admission_no__icontains=search)
        )

    students = students.distinct().order_by('admission_no')

    classes = Class.objects.all()
    streams = Stream.objects.all()
    if class_filter:
        streams = streams.filter(class_obj_id=class_filter)

    context = {
        'students': students,
        'classes': classes,
        'streams': streams,
        'class_filter': class_filter,
        'stream_filter': stream_filter,
        'search': search,
    }
    return render(request, 'students/student_list.html', context)


@login_required
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    enrollment = Enrollment.objects.filter(
        student=student,
        academic_year__is_current=True
    ).first()

    student_subjects = StudentSubject.objects.filter(
        student=student,
        academic_year__is_current=True
    ).select_related('subject')

    context = {
        'student': student,
        'enrollment': enrollment,
        'student_subjects': student_subjects,
    }
    return render(request, 'students/student_detail.html', context)


@login_required
def import_students(request):
    current_year = AcademicYear.objects.filter(is_current=True).first()

    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'imports')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, csv_file.name)

        with open(file_path, 'wb+') as dest:
            for chunk in csv_file.chunks():
                dest.write(chunk)

        service = StudentImportService(file_path, current_year.id)
        result = service.process()

        if result['created']:
            messages.success(request, f"✅ {result['created']} students imported successfully.")
        if result['updated']:
            messages.info(request, f"ℹ️ {result['updated']} students updated.")
        if result['skipped']:
            messages.warning(request, f"⚠️ {result['skipped']} rows skipped.")
        for error in result['errors'][:10]:
            messages.error(request, error)

        return redirect('student_list')

    return render(request, 'students/import.html')


@login_required
def assign_optionals(request):
    class_filter = request.GET.get('class', '')
    stream_filter = request.GET.get('stream', '')

    streams = Stream.objects.filter(class_obj__level_type='O-Level')
    students = Student.objects.filter(enrollments__stream__class_obj__level_type='O-Level')
    all_optionals = Subject.objects.filter(category='optional')

    if class_filter:
        streams = streams.filter(class_obj_id=class_filter)
    if stream_filter:
        students = students.filter(enrollments__stream_id=stream_filter)

    students = students.distinct().order_by('admission_no')

    if request.method == 'POST':
        for student in students:
            subject_ids = request.POST.getlist(f'optionals_{student.id}')
            current_year = AcademicYear.objects.get(is_current=True)
            enrollment = student.enrollments.filter(academic_year=current_year).first()

            if enrollment:
                StudentSubject.objects.filter(
                    student=student,
                    academic_year=current_year,
                    subject_type='optional'
                ).delete()

                for subject_id in subject_ids:
                    subject = Subject.objects.get(id=subject_id)
                    StudentSubject.objects.create(
                        student=student,
                        subject=subject,
                        stream=enrollment.stream,
                        subject_type='optional',
                        academic_year=current_year
                    )

        messages.success(request, 'Optional subjects updated successfully!')
        return redirect(request.path + f'?class={class_filter}&stream={stream_filter}')

    classes = Class.objects.filter(level_type='O-Level')

    context = {
        'students': students,
        'streams': streams,
        'classes': classes,
        'all_optionals': all_optionals,
        'class_filter': class_filter,
        'stream_filter': stream_filter,
    }
    return render(request, 'students/assign_optionals.html', context)


@login_required
def promote_students(request):
    """Promote students to next class. Only works in Term 3."""
    current_term = Term.objects.filter(is_current=True).first()
    current_year = AcademicYear.objects.get(is_current=True)

    # Block if not Term 3
    if not current_term or current_term.name != 'Term 3':
        messages.error(request, 'Promotion is only available during Term 3 (end of academic year).')
        return redirect('student_list')

    if request.method == 'POST' and request.POST.get('confirm') == 'YES':
        promoted_count = 0
        graduated_count = 0
        wiped_streams = []

        promotion_map = {
            'Senior 1': 'Senior 2',
            'Senior 2': 'Senior 3',
            'Senior 3': 'Senior 4',
            'Senior 5': 'Senior 6',
        }

        graduating_classes = ['Senior 4', 'Senior 6']
        wipe_classes = ['Senior 1', 'Senior 5']

        for from_class_name, to_class_name in promotion_map.items():
            try:
                from_class = Class.objects.get(name=from_class_name)
                to_class = Class.objects.get(name=to_class_name)
            except Class.DoesNotExist:
                continue

            enrollments = Enrollment.objects.filter(
                stream__class_obj=from_class,
                academic_year=current_year,
                status='active'
            ).select_related('student', 'stream')

            for enrollment in enrollments:
                new_stream, _ = Stream.objects.get_or_create(
                    class_obj=to_class,
                    name=enrollment.stream.name,
                )
                enrollment.stream = new_stream
                enrollment.save()
                promoted_count += 1

        for class_name in graduating_classes:
            try:
                grad_class = Class.objects.get(name=class_name)
            except Class.DoesNotExist:
                continue

            graduating = Enrollment.objects.filter(
                stream__class_obj=grad_class,
                academic_year=current_year,
                status='active'
            )

            for enrollment in graduating:
                enrollment.status = 'graduated'
                enrollment.save()
                graduated_count += 1

        for class_name in wipe_classes:
            try:
                wipe_class = Class.objects.get(name=class_name)
                streams = Stream.objects.filter(class_obj=wipe_class)
                for stream in streams:
                    wiped_streams.append(str(stream))
                streams.delete()
            except Class.DoesNotExist:
                pass

        messages.success(request,
            f'✅ {promoted_count} students promoted. '
            f'{graduated_count} students graduated. '
            f'S1 and S5 streams cleared for new intake.'
        )
        return redirect('student_list')

    # GET request — show promotion preview
    preview = {}
    graduating = {}
    current_counts = {}

    promotion_map = {
        'Senior 1': 'Senior 2',
        'Senior 2': 'Senior 3',
        'Senior 3': 'Senior 4',
        'Senior 5': 'Senior 6',
    }

    for from_class, to_class in promotion_map.items():
        try:
            fc = Class.objects.get(name=from_class)
            count = Enrollment.objects.filter(
                stream__class_obj=fc,
                academic_year=current_year,
                status='active'
            ).count()
            if count > 0:
                preview[f"{from_class} → {to_class}"] = count
        except Class.DoesNotExist:
            pass

    for class_name in ['Senior 4', 'Senior 6']:
        try:
            gc = Class.objects.get(name=class_name)
            count = Enrollment.objects.filter(
                stream__class_obj=gc,
                academic_year=current_year,
                status='active'
            ).count()
            if count > 0:
                graduating[class_name] = count
        except Class.DoesNotExist:
            pass

    for c in Class.objects.all().order_by('sort_order'):
        count = Enrollment.objects.filter(
            stream__class_obj=c,
            academic_year=current_year,
            status='active'
        ).count()
        current_counts[c.name] = count

    return render(request, 'students/promote.html', {
        'preview': preview,
        'graduating': graduating,
        'current_counts': current_counts,
        'current_term': current_term,
    })


@login_required
def create_student(request):
    """Manual student creation."""
    if request.method == 'POST':
        admission_no = request.POST.get('admission_no', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        gender = request.POST.get('gender', 'M').strip()
        class_id = request.POST.get('class_id', '')
        stream_id = request.POST.get('stream_id', '')
        parent_name = request.POST.get('parent_name', '').strip()
        parent_phone = request.POST.get('parent_phone', '').strip()
        parent_email = request.POST.get('parent_email', '').strip()

        if not admission_no or not first_name or not class_id or not stream_id:
            messages.error(request, 'Admission number, name, class and stream are required.')
            return redirect('create_student')

        if Student.objects.filter(admission_no=admission_no).exists():
            messages.error(request, 'A student with this admission number already exists.')
            return redirect('create_student')

        current_year = AcademicYear.objects.get(is_current=True)
        stream = get_object_or_404(Stream, id=stream_id)

        student = Student.objects.create(
            admission_no=admission_no,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            parent_name=parent_name,
            parent_phone=parent_phone,
            parent_email=parent_email,
        )

        Enrollment.objects.create(
            student=student,
            stream=stream,
            academic_year=current_year,
        )

        if stream.class_obj.level_type == 'O-Level':
            compulsory_links = ClassCompulsorySubject.objects.filter(class_obj=stream.class_obj)
            for link in compulsory_links:
                StudentSubject.objects.create(
                    student=student,
                    subject=link.subject,
                    stream=stream,
                    subject_type='compulsory',
                    academic_year=current_year,
                )
        else:
            try:
                gp = Subject.objects.get(code='GP')
                StudentSubject.objects.create(
                    student=student,
                    subject=gp,
                    stream=stream,
                    subject_type='compulsory',
                    academic_year=current_year,
                )
            except Subject.DoesNotExist:
                pass

        messages.success(request, f'Student {first_name} {last_name} created successfully.')
        return redirect('student_detail', student_id=student.id)

    classes = Class.objects.all()
    streams = Stream.objects.all()
    return render(request, 'students/create.html', {
        'classes': classes,
        'streams': streams,
    })


@login_required
def import_alevel_students(request):
    current_year = AcademicYear.objects.filter(is_current=True).first()

    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'imports')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, csv_file.name)

        with open(file_path, 'wb+') as dest:
            for chunk in csv_file.chunks():
                dest.write(chunk)

        df = pd.read_csv(file_path)
        created = 0
        errors = []

        for index, row in df.iterrows():
            try:
                admission_no = str(row.get('admission_no', '')).strip()
                first_name = str(row.get('first_name', '')).strip()
                last_name = str(row.get('last_name', '')).strip()
                gender = str(row.get('gender', 'M')).strip().upper()
                class_name = str(row.get('class_name', '')).strip()
                stream_name = str(row.get('stream_name', '')).strip()
                subject_1 = str(row.get('subject_1', '')).strip()
                subject_2 = str(row.get('subject_2', '')).strip()
                subject_3 = str(row.get('subject_3', '')).strip()
                subsidiary = str(row.get('subsidiary', '')).strip()
                parent_name = str(row.get('parent_name', '')).strip()
                parent_phone = str(row.get('parent_phone', '')).strip()

                if not admission_no or not first_name or not class_name:
                    continue

                class_obj, _ = Class.objects.get_or_create(
                    name=class_name,
                    defaults={'level_type': 'A-Level', 'sort_order': int(class_name[-1]) + 4}
                )
                stream, _ = Stream.objects.get_or_create(class_obj=class_obj, name=stream_name)

                student, is_new = Student.objects.update_or_create(
                    admission_no=admission_no,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'gender': gender,
                        'parent_name': parent_name,
                        'parent_phone': parent_phone,
                    }
                )

                Enrollment.objects.get_or_create(student=student, stream=stream, academic_year=current_year)

                for code in [subject_1, subject_2, subject_3]:
                    if code:
                        try:
                            subject = Subject.objects.get(code=code.upper())
                            StudentSubject.objects.get_or_create(
                                student=student, subject=subject,
                                academic_year=current_year,
                                defaults={'stream': stream, 'subject_type': 'principal'}
                            )
                        except Subject.DoesNotExist:
                            errors.append(f"Row {index+2}: Subject '{code}' not found")

                if subsidiary:
                    try:
                        subject = Subject.objects.get(code=subsidiary.upper())
                        StudentSubject.objects.get_or_create(
                            student=student, subject=subject,
                            academic_year=current_year,
                            defaults={'stream': stream, 'subject_type': 'subsidiary'}
                        )
                    except Subject.DoesNotExist:
                        errors.append(f"Row {index+2}: Subsidiary '{subsidiary}' not found")

                try:
                    gp = Subject.objects.get(code='GP')
                    StudentSubject.objects.get_or_create(
                        student=student, subject=gp,
                        academic_year=current_year,
                        defaults={'stream': stream, 'subject_type': 'compulsory'}
                    )
                except Subject.DoesNotExist:
                    errors.append(f"Row {index+2}: GP subject not found. Add it first.")

                if is_new:
                    created += 1

            except Exception as e:
                errors.append(f"Row {index+2}: {str(e)}")

        messages.success(request, f'✅ {created} A-Level students imported.')
        for error in errors[:10]:
            messages.error(request, error)

        return redirect('student_list')

    return render(request, 'students/import_alevel.html')


@login_required
def assign_alevel_subjects(request):
    """Assign A-Level subjects per student."""
    class_filter = request.GET.get('class', '')
    stream_filter = request.GET.get('stream', '')

    classes = Class.objects.filter(level_type='A-Level')
    streams = Stream.objects.filter(class_obj__level_type='A-Level')
    if class_filter:
        streams = streams.filter(class_obj_id=class_filter)

    students = Student.objects.filter(enrollments__stream__class_obj__level_type='A-Level')
    if stream_filter:
        students = students.filter(enrollments__stream_id=stream_filter)
    students = students.distinct().order_by('admission_no')

    all_principals = Subject.objects.filter(category='principal')
    all_subsidiaries = Subject.objects.filter(category='subsidiary')

    if request.method == 'POST':
        current_year = AcademicYear.objects.get(is_current=True)
        for student in students:
            principal_ids = request.POST.getlist(f'principals_{student.id}')
            subsidiary_ids = request.POST.getlist(f'subsidiaries_{student.id}')
            enrollment = student.enrollments.filter(academic_year=current_year).first()

            if enrollment:
                StudentSubject.objects.filter(
                    student=student, academic_year=current_year
                ).exclude(subject__code='GP').delete()

                for subject_id in principal_ids[:3]:
                    subject = Subject.objects.get(id=subject_id)
                    StudentSubject.objects.create(
                        student=student, subject=subject,
                        stream=enrollment.stream, subject_type='principal',
                        academic_year=current_year
                    )

                for subject_id in subsidiary_ids:
                    subject = Subject.objects.get(id=subject_id)
                    StudentSubject.objects.create(
                        student=student, subject=subject,
                        stream=enrollment.stream, subject_type='subsidiary',
                        academic_year=current_year
                    )

                gp = Subject.objects.get(code='GP')
                StudentSubject.objects.get_or_create(
                    student=student, subject=gp,
                    academic_year=current_year,
                    defaults={'stream': enrollment.stream, 'subject_type': 'compulsory'}
                )

        messages.success(request, 'A-Level subjects updated successfully!')
        return redirect(request.path + f'?class={class_filter}&stream={stream_filter}')

    context = {
        'classes': classes,
        'streams': streams,
        'students': students,
        'all_principals': all_principals,
        'all_subsidiaries': all_subsidiaries,
        'class_filter': class_filter,
        'stream_filter': stream_filter,
    }
    return render(request, 'students/assign_alevel.html', context)


@login_required
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    student_name = student.full_name()
    student.delete()
    messages.success(request, f'Student {student_name} deleted successfully.')
    return redirect('student_list')


@login_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    enrollment = Enrollment.objects.filter(student=student, academic_year__is_current=True).first()
    classes = Class.objects.all()
    streams = Stream.objects.all()

    if request.method == 'POST':
        student.first_name = request.POST.get('first_name', student.first_name).strip()
        student.last_name = request.POST.get('last_name', student.last_name).strip()
        student.gender = request.POST.get('gender', student.gender).strip()
        student.parent_name = request.POST.get('parent_name', student.parent_name).strip()
        student.parent_phone = request.POST.get('parent_phone', student.parent_phone).strip()
        student.parent_email = request.POST.get('parent_email', student.parent_email).strip()
        student.save()

        new_stream_id = request.POST.get('stream_id')
        if new_stream_id and enrollment:
            new_stream = get_object_or_404(Stream, id=new_stream_id)
            enrollment.stream = new_stream
            enrollment.save()

        messages.success(request, f'Student {student.full_name()} updated.')
        return redirect('student_detail', student_id=student.id)

    return render(request, 'students/edit.html', {
        'student': student,
        'enrollment': enrollment,
        'classes': classes,
        'streams': streams,
    })