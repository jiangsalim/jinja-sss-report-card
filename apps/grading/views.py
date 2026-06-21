from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models as db_models
from apps.teachers.models import TeacherAssignment
from apps.students.models import Student, StudentSubject, Enrollment
from apps.academic.models import Class, Stream, Subject, AcademicYear, Term, ClassCompulsorySubject, StreamOfficials
from .models import Assessment, GradeEntry, GradingScale
from .services import calculate_grade, get_letter_grade
from decimal import Decimal
import hashlib
import qrcode
import base64
from io import BytesIO


@login_required
def grade_entry(request, assignment_id):
    assignment = get_object_or_404(
        TeacherAssignment,
        id=assignment_id,
        teacher=request.user
    )

    stream = assignment.stream
    subject = assignment.subject
    current_term = Term.objects.filter(is_current=True).first()
    current_year = AcademicYear.objects.get(is_current=True)

    student_subjects = StudentSubject.objects.filter(
        stream=stream,
        subject=subject,
        academic_year=current_year
    ).select_related('student').order_by('student__last_name', 'student__first_name')

    for ss in student_subjects:
        ss.existing_assessments = Assessment.objects.filter(
            student_subject=ss,
            term=current_term
        ).order_by('created_at')

    assessment_names = Assessment.objects.filter(
        student_subject__in=student_subjects,
        term=current_term
    ).values_list('name', flat=True).distinct().order_by('name')

    context = {
        'assignment': assignment,
        'stream': stream,
        'subject': subject,
        'student_subjects': student_subjects,
        'assessment_names': assessment_names,
        'current_term': current_term,
    }
    return render(request, 'grading/grade_entry.html', context)


@login_required
def save_marks(request):
    if request.method == 'POST':
        current_term = Term.objects.filter(is_current=True).first()
        assessment_name = request.POST.get('assessment_name', '').strip()
        max_marks = request.POST.get('max_marks', '100')
        weight = request.POST.get('weight', '0')

        if not assessment_name:
            messages.error(request, 'Assessment name is required.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        try:
            max_marks = Decimal(max_marks)
            weight = Decimal(weight)
        except:
            messages.error(request, 'Invalid marks or weight.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        for key, value in request.POST.items():
            if key.startswith('marks_') and value.strip():
                student_subject_id = key.replace('marks_', '')
                marks_obtained = Decimal(value.strip())

                try:
                    student_subject = StudentSubject.objects.get(id=student_subject_id)
                except StudentSubject.DoesNotExist:
                    continue

                assessment, created = Assessment.objects.update_or_create(
                    student_subject=student_subject,
                    term=current_term,
                    name=assessment_name,
                    defaults={
                        'teacher': request.user,
                        'max_marks': max_marks,
                        'weight': weight,
                        'marks_obtained': marks_obtained,
                        'status': 'draft',
                    }
                )

        messages.success(request, f'Marks saved for "{assessment_name}" (out of {max_marks}, weight {weight}%).')

    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def submit_marks(request, assignment_id):
    assignment = get_object_or_404(TeacherAssignment, id=assignment_id, teacher=request.user)
    current_term = Term.objects.filter(is_current=True).first()
    current_year = AcademicYear.objects.get(is_current=True)

    stream = assignment.stream
    subject = assignment.subject

    student_subjects = StudentSubject.objects.filter(
        stream=stream,
        subject=subject,
        academic_year=current_year
    )

    updated = Assessment.objects.filter(
        student_subject__in=student_subjects,
        term=current_term,
        status='draft'
    ).update(status='submitted')

    for ss in student_subjects:
        final_percent, letter = calculate_grade(ss, current_term)
        if final_percent is not None:
            GradeEntry.objects.update_or_create(
                student_subject=ss,
                term=current_term,
                defaults={
                    'teacher': request.user,
                    'final_percentage': final_percent,
                    'letter_grade': letter,
                    'status': 'submitted',
                }
            )

    messages.success(request, f'{updated} assessments submitted. Grades calculated.')
    return redirect('teacher_dashboard')


@login_required
def grading_scale_list(request):
    scales = GradingScale.objects.all()

    if request.method == 'POST':
        grade_letter = request.POST.get('grade_letter', '').strip().upper()
        min_percent = request.POST.get('min_percent', '')
        max_percent = request.POST.get('max_percent', '')
        remark = request.POST.get('remark', '').strip()

        if grade_letter and min_percent and max_percent:
            GradingScale.objects.update_or_create(
                grade_letter=grade_letter,
                defaults={
                    'min_percent': Decimal(min_percent),
                    'max_percent': Decimal(max_percent),
                    'remark': remark,
                }
            )
            messages.success(request, f'Grade {grade_letter} saved.')
        return redirect('grading_scale')

    return render(request, 'grading/grading_scale.html', {'scales': scales})


@login_required
def delete_scale(request, scale_id):
    scale = get_object_or_404(GradingScale, id=scale_id)
    scale.delete()
    messages.success(request, f'Grade {scale.grade_letter} deleted.')
    return redirect('grading_scale')


@login_required
def grade_status(request):
    class_filter = request.GET.get('class', '')
    stream_filter = request.GET.get('stream', '')

    classes = Class.objects.filter(level_type='O-Level')
    streams = Stream.objects.all()
    if class_filter:
        streams = streams.filter(class_obj_id=class_filter)

    current_term = Term.objects.filter(is_current=True).first()
    current_year = AcademicYear.objects.get(is_current=True)

    status_data = []

    if stream_filter:
        stream = get_object_or_404(Stream, id=stream_filter)
        student_subjects = StudentSubject.objects.filter(
            stream=stream,
            academic_year=current_year
        ).select_related('student', 'subject')

        subjects_in_stream = student_subjects.values_list('subject__id', flat=True).distinct()
        for subject_id in subjects_in_stream:
            subject = Subject.objects.get(id=subject_id)
            ss_list = student_subjects.filter(subject=subject)

            total_students = ss_list.count()
            graded_count = GradeEntry.objects.filter(
                student_subject__in=ss_list,
                term=current_term,
                status='submitted'
            ).count()

            status_data.append({
                'subject': subject,
                'total': total_students,
                'graded': graded_count,
                'pending': total_students - graded_count,
                'percent': round((graded_count / total_students * 100) if total_students > 0 else 0, 1),
            })

    context = {
        'classes': classes,
        'streams': streams,
        'class_filter': class_filter,
        'stream_filter': stream_filter,
        'status_data': status_data,
        'current_term': current_term,
    }
    return render(request, 'grading/grade_status.html', context)


@login_required
def finalize_grades(request):
    if request.method == 'POST':
        stream_id = request.POST.get('stream_id')
        current_term = Term.objects.filter(is_current=True).first()
        current_year = AcademicYear.objects.get(is_current=True)

        stream = get_object_or_404(Stream, id=stream_id)

        student_subjects = StudentSubject.objects.filter(
            stream=stream,
            academic_year=current_year
        )

        updated = GradeEntry.objects.filter(
            student_subject__in=student_subjects,
            term=current_term,
            status='submitted'
        ).update(status='locked')

        Assessment.objects.filter(
            student_subject__in=student_subjects,
            term=current_term,
            status='submitted'
        ).update(status='locked')

        messages.success(request, f'Grades finalized for {stream}. {updated} entries locked.')
        return redirect('grade_status')

    return redirect('grade_status')


@login_required
def report_card(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    current_term = Term.objects.filter(is_current=True).first()
    current_year = AcademicYear.objects.get(is_current=True)

    enrollment = Enrollment.objects.filter(
        student=student,
        academic_year=current_year
    ).first()

    if not enrollment:
        messages.error(request, 'Student not enrolled in current academic year.')
        return redirect('student_list')

    # Get stream officials
    officials = StreamOfficials.objects.filter(stream=enrollment.stream).first()

    student_subjects = StudentSubject.objects.filter(
        student=student,
        academic_year=current_year
    ).select_related('subject')

    subject_grades = []
    total_percent = 0
    graded_subjects = 0

    for ss in student_subjects:
        grade_entry = GradeEntry.objects.filter(
            student_subject=ss,
            term=current_term
        ).first()

        assessments = Assessment.objects.filter(
            student_subject=ss,
            term=current_term
        ).order_by('created_at')

        if grade_entry and grade_entry.final_percentage:
            total_percent += float(grade_entry.final_percentage)
            graded_subjects += 1

        subject_grades.append({
            'subject': ss.subject,
            'subject_type': ss.get_subject_type_display(),
            'assessments': assessments,
            'grade_entry': grade_entry,
        })

    average = round(total_percent / graded_subjects, 2) if graded_subjects > 0 else None
    average_letter = get_letter_grade(average) if average else None

    # Generate verification code
    verify_string = f"{student.admission_no}-{current_term.id}-{student.id}-jinja-sss-secret"
    verification_code = hashlib.sha256(verify_string.encode()).hexdigest()[:12].upper()

    # Generate QR code
    verify_url = f"http://127.0.0.1:8000/grades/verify/{verification_code}/"
    qr = qrcode.make(verify_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    qr_image = f"data:image/png;base64,{qr_base64}"

    context = {
        'student': student,
        'enrollment': enrollment,
        'officials': officials,
        'subject_grades': subject_grades,
        'average': average,
        'average_letter': average_letter,
        'current_term': current_term,
        'verification_code': verification_code,
        'qr_image': qr_image,
    }
    return render(request, 'grading/report_card.html', context)


@login_required
def verify_report(request, code):
    current_term = Term.objects.filter(is_current=True).first()

    if not current_term:
        return render(request, 'grading/verify.html', {'valid': False, 'message': 'No active term found.'})

    grade_entries = GradeEntry.objects.filter(term=current_term, status__in=['submitted', 'locked'])

    found = None
    for entry in grade_entries:
        verify_string = f"{entry.student_subject.student.admission_no}-{current_term.id}-{entry.student_subject.student.id}-jinja-sss-secret"
        expected_code = hashlib.sha256(verify_string.encode()).hexdigest()[:12].upper()
        if expected_code == code:
            found = entry.student_subject.student
            break

    if found:
        enrollment = Enrollment.objects.filter(
            student=found,
            academic_year=current_term.academic_year
        ).first()

        return render(request, 'grading/verify.html', {
            'valid': True,
            'student': found,
            'enrollment': enrollment,
            'term': current_term,
        })
    else:
        return render(request, 'grading/verify.html', {
            'valid': False,
            'message': 'Invalid or unrecognized verification code.'
        })


@login_required
def bulk_reports(request):
    """Admin: View all report cards for a stream at once."""
    stream_filter = request.GET.get('stream', '')
    level = request.GET.get('level', 'O-Level')
    
    classes = Class.objects.filter(level_type=level)
    streams = Stream.objects.filter(class_obj__level_type=level)
    
    students = []
    stream = None
    
    if stream_filter:
        stream = get_object_or_404(Stream, id=stream_filter)
        current_year = AcademicYear.objects.get(is_current=True)
        current_term = Term.objects.filter(is_current=True).first()
        
        enrollments = Enrollment.objects.filter(
            stream=stream,
            academic_year=current_year,
            status='active'
        ).select_related('student')
        
        for enrollment in enrollments:
            student = enrollment.student
            grade_entries = GradeEntry.objects.filter(
                student_subject__student=student,
                term=current_term
            )
            graded = grade_entries.filter(status='locked').count()
            total = grade_entries.count()
            students.append({
                'student': student,
                'graded': graded,
                'total': total,
                'ready': graded == total and total > 0,
            })
    
    context = {
        'classes': classes,
        'streams': streams,
        'stream_filter': stream_filter,
        'students': students,
        'stream': stream,
        'current_level': level,
    }
    return render(request, 'grading/bulk_reports.html', context)