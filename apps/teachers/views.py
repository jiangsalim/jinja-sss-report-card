from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from apps.academic.models import Class, Stream, Subject, AcademicYear, Term, ClassCompulsorySubject
from apps.students.models import StudentSubject
from .models import TeacherAssignment
from .services import TeacherImportService
import os
import csv

User = get_user_model()


@login_required
def teacher_list(request):
    teachers = User.objects.filter(role='teacher').order_by('first_name', 'last_name')
    return render(request, 'teachers/teacher_list.html', {'teachers': teachers})


@login_required
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, role='teacher')
    assignments = TeacherAssignment.objects.filter(
        teacher=teacher,
        academic_year__is_current=True
    ).select_related('stream__class_obj', 'subject')

    return render(request, 'teachers/teacher_detail.html', {
        'teacher': teacher,
        'assignments': assignments,
    })


@login_required
def import_teachers(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'imports')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, csv_file.name)

        with open(file_path, 'wb+') as dest:
            for chunk in csv_file.chunks():
                dest.write(chunk)

        service = TeacherImportService(file_path)
        result = service.process()

        if result['created']:
            messages.success(request, f"✅ {result['created']} teachers imported.")
        if result['updated']:
            messages.info(request, f"ℹ️ {result['updated']} teachers updated.")
        for error in result['errors'][:10]:
            messages.error(request, error)

        return redirect('teacher_list')

    return render(request, 'teachers/import.html')


@login_required
def download_credentials(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, role='teacher')

    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(10))
    teacher.set_password(password)
    teacher.must_change_password = True
    teacher.save()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{teacher.username}_credentials.csv"'

    writer = csv.writer(response)
    writer.writerow(['Teacher Credentials - Jinja SSS'])
    writer.writerow(['Name', f'{teacher.first_name} {teacher.last_name}'])
    writer.writerow(['Username', teacher.username])
    writer.writerow(['Password', password])
    writer.writerow(['Login URL', 'http://127.0.0.1:8000/login/'])

    messages.success(request, f'Credentials generated for {teacher.get_full_name()}')
    return response


@login_required
def reset_password(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, role='teacher')

    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(10))
    teacher.set_password(password)
    teacher.must_change_password = True
    teacher.save()

    messages.success(request, f'Password reset for {teacher.get_full_name()}. New password: {password}')
    return redirect('teacher_detail', teacher_id=teacher.id)


@login_required
def delete_teacher(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id, role='teacher')
    teacher_name = teacher.get_full_name()
    teacher.delete()
    messages.success(request, f'Teacher {teacher_name} deleted successfully.')
    return redirect('teacher_list')


@login_required
def assignments(request):
    class_filter = request.GET.get('class', '')
    stream_filter = request.GET.get('stream', '')
    level = request.GET.get('level', 'O-Level')

    classes = Class.objects.filter(level_type=level)
    streams = Stream.objects.filter(class_obj__level_type=level)
    if class_filter:
        streams = streams.filter(class_obj_id=class_filter)

    teacher_assignments = TeacherAssignment.objects.filter(
        academic_year__is_current=True,
        stream__class_obj__level_type=level
    )
    if stream_filter:
        teacher_assignments = teacher_assignments.filter(stream_id=stream_filter)

    teacher_assignments = teacher_assignments.select_related('teacher', 'stream__class_obj', 'subject')

    stream_subjects = []
    all_teachers = User.objects.filter(role='teacher', is_active=True)

    if stream_filter:
        stream = Stream.objects.get(id=stream_filter)

        if level == 'O-Level':
            # O-Level: compulsory + optional subjects
            compulsory = ClassCompulsorySubject.objects.filter(class_obj=stream.class_obj)
            stream_subjects = [cs.subject for cs in compulsory]

            optional_ids = StudentSubject.objects.filter(
                stream=stream,
                subject_type='optional',
                academic_year__is_current=True
            ).values_list('subject_id', flat=True).distinct()
            optional_subjects = Subject.objects.filter(id__in=optional_ids)
            stream_subjects.extend(optional_subjects)
        else:
            # A-Level: all subjects in this stream (principal, subsidiary, GP)
            subject_ids = StudentSubject.objects.filter(
                stream=stream,
                academic_year__is_current=True
            ).values_list('subject_id', flat=True).distinct()
            stream_subjects = list(Subject.objects.filter(id__in=subject_ids))

        stream_subjects = list(set(stream_subjects))

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher')
        subject_id = request.POST.get('subject')
        current_year = AcademicYear.objects.get(is_current=True)
        current_term = Term.objects.filter(academic_year=current_year, is_current=True).first()

        if teacher_id and subject_id and stream_filter:
            teacher = get_object_or_404(User, id=teacher_id)
            subject = get_object_or_404(Subject, id=subject_id)
            stream = get_object_or_404(Stream, id=stream_filter)

            assignment, created = TeacherAssignment.objects.get_or_create(
                teacher=teacher,
                stream=stream,
                subject=subject,
                academic_year=current_year,
                term=current_term,
            )

            if created:
                messages.success(request, f'{teacher.get_full_name()} assigned to {stream} - {subject.name}')
            else:
                messages.info(request, 'Assignment already exists.')

        return redirect(request.path + f'?class={class_filter}&stream={stream_filter}&level={level}')

    context = {
        'classes': classes,
        'streams': streams,
        'assignments': teacher_assignments,
        'class_filter': class_filter,
        'stream_filter': stream_filter,
        'stream_subjects': stream_subjects,
        'all_teachers': all_teachers,
        'current_level': level,
    }
    return render(request, 'teachers/assignments.html', context)


@login_required
def remove_assignment(request, assignment_id):
    assignment = get_object_or_404(TeacherAssignment, id=assignment_id)
    info = str(assignment)
    assignment.delete()
    messages.success(request, f'Assignment removed: {info}')
    return redirect('teacher_assignments')


@login_required
def create_teacher(request):
    """Manual teacher creation."""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not first_name or not email:
            messages.error(request, 'First name and email are required.')
            return redirect('create_teacher')

        username = email

        if User.objects.filter(email=email).exists():
            messages.error(request, 'A teacher with this email already exists.')
            return redirect('create_teacher')

        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(10))

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='teacher',
            phone=phone,
            must_change_password=True,
        )

        messages.success(request, f'Teacher {first_name} {last_name} created. Password: {password}')
        return redirect('teacher_detail', teacher_id=user.id)

    return render(request, 'teachers/create.html')