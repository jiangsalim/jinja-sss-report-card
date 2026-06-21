from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings as django_settings
from apps.teachers.models import TeacherAssignment
from apps.students.models import Student, Enrollment, StudentSubject
from apps.academic.models import AcademicYear, Term, Class, Stream, Subject, ClassCompulsorySubject, StreamOfficials
from apps.grading.models import Assessment, GradeEntry, GradingScale
from django.contrib.auth import update_session_auth_hash
import os
import json

User = get_user_model()


@login_required
def admin_dashboard(request):
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()

    total_students = Student.objects.count()
    total_teachers = User.objects.filter(role='teacher', is_active=True).count()
    total_classes = Class.objects.filter(level_type='O-Level').count() + Class.objects.filter(level_type='A-Level').count()
    total_streams = Stream.objects.count()

    if current_term:
        total_grades = GradeEntry.objects.filter(term=current_term).count()
        submitted_grades = GradeEntry.objects.filter(term=current_term, status='submitted').count()
        locked_grades = GradeEntry.objects.filter(term=current_term, status='locked').count()
        pending_grades = GradeEntry.objects.filter(term=current_term, status='draft').count()
    else:
        total_grades = submitted_grades = locked_grades = pending_grades = 0

    context = {
        'page_title': 'Admin Dashboard',
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_streams': total_streams,
        'total_grades': total_grades,
        'submitted_grades': submitted_grades,
        'locked_grades': locked_grades,
        'pending_grades': pending_grades,
        'current_term': current_term,
    }
    return render(request, 'core/admin_dashboard.html', context)


@login_required
def teacher_dashboard(request):
    assignments = TeacherAssignment.objects.filter(
        teacher=request.user,
        academic_year__is_current=True
    ).select_related('stream__class_obj', 'subject')

    context = {
        'page_title': 'Teacher Dashboard',
        'assignments': assignments,
    }
    return render(request, 'core/teacher_dashboard.html', context)


@login_required
def parent_dashboard(request):
    context = {
        'page_title': 'Parent Dashboard',
    }
    return render(request, 'core/parent_dashboard.html', context)


@login_required
def school_settings(request):
    """Edit school information."""
    if request.method == 'POST':
        settings_data = {
            'SCHOOL_NAME': request.POST.get('school_name', ''),
            'SCHOOL_ADDRESS': request.POST.get('school_address', ''),
            'SCHOOL_PHONE': request.POST.get('school_phone', ''),
            'SCHOOL_EMAIL': request.POST.get('school_email', ''),
            'SCHOOL_MOTTO': request.POST.get('school_motto', ''),
        }

        settings_path = os.path.join(django_settings.BASE_DIR, 'school_settings.json')
        with open(settings_path, 'w') as f:
            json.dump(settings_data, f, indent=4)

        messages.success(request, 'School settings updated successfully!')
        return redirect('school_settings')

    settings_path = os.path.join(django_settings.BASE_DIR, 'school_settings.json')
    current_settings = {
        'SCHOOL_NAME': 'Jinja Senior Secondary School',
        'SCHOOL_ADDRESS': 'P.O. Box 255, Jinja, Uganda',
        'SCHOOL_PHONE': '+256 123 456789',
        'SCHOOL_EMAIL': 'info@jinjasss.sc.ug',
        'SCHOOL_MOTTO': 'Striving for Excellence',
    }

    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            saved = json.load(f)
            current_settings.update(saved)

    return render(request, 'core/school_settings.html', {'settings': current_settings})


@login_required
def system_reset(request):
    """Super admin: Wipe all data except classes and admin users."""
    if request.user.role != 'super_admin':
        messages.error(request, 'Only Super Admin can reset the system.')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        confirm_text = request.POST.get('confirm_text', '')

        if confirm_text != 'RESET JINJA SSS':
            messages.error(request, 'Please type exactly: RESET JINJA SSS')
            return redirect('system_reset')

        students_count = Student.objects.count()
        teachers_count = User.objects.filter(role='teacher').count()
        parents_count = User.objects.filter(role='parent').count()
        streams_count = Stream.objects.count()
        grades_count = GradeEntry.objects.count()
        enrollments_count = Enrollment.objects.count()
        assignments_count = TeacherAssignment.objects.count()
        assessments_count = Assessment.objects.count()
        officials_count = StreamOfficials.objects.count()
        student_subjects_count = StudentSubject.objects.count()
        compulsory_count = ClassCompulsorySubject.objects.count()

        Assessment.objects.all().delete()
        GradeEntry.objects.all().delete()
        TeacherAssignment.objects.all().delete()
        StudentSubject.objects.all().delete()
        Enrollment.objects.all().delete()
        StreamOfficials.objects.all().delete()
        ClassCompulsorySubject.objects.all().delete()
        Stream.objects.all().delete()
        Student.objects.all().delete()
        User.objects.filter(role='teacher').delete()
        User.objects.filter(role='parent').delete()

        settings_path = os.path.join(django_settings.BASE_DIR, 'school_settings.json')
        if os.path.exists(settings_path):
            os.remove(settings_path)

        total_deleted = (students_count + teachers_count + parents_count + streams_count + 
                        grades_count + enrollments_count + assignments_count + 
                        assessments_count + officials_count + student_subjects_count + 
                        compulsory_count)

        messages.success(request,
            f'🔥 SYSTEM RESET COMPLETE — {total_deleted} records deleted.\n'
            f'✅ Preserved: Classes, Subjects, Admin accounts, Grading scale, Academic years & terms.'
        )
        return redirect('admin_dashboard')

    stats = {
        'students': Student.objects.count(),
        'teachers': User.objects.filter(role='teacher').count(),
        'parents': User.objects.filter(role='parent').count(),
        'streams': Stream.objects.count(),
        'grades': GradeEntry.objects.count(),
        'enrollments': Enrollment.objects.count(),
        'assignments': TeacherAssignment.objects.count(),
        'assessments': Assessment.objects.count(),
        'officials': StreamOfficials.objects.count(),
        'student_subjects': StudentSubject.objects.count(),
        'compulsory': ClassCompulsorySubject.objects.count(),
    }

    preserved = {
        'classes': Class.objects.count(),
        'subjects': Subject.objects.count(),
        'admins': User.objects.filter(role__in=['super_admin', 'admin']).count(),
        'grading_scales': GradingScale.objects.count(),
        'academic_years': AcademicYear.objects.count(),
    }

    return render(request, 'core/system_reset.html', {
        'stats': stats,
        'preserved': preserved,
    })

@login_required
def admin_profile(request):
    """Admin can update their own username and password."""
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'update_profile':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            
            if username and User.objects.filter(username=username).exclude(id=request.user.id).exists():
                messages.error(request, 'Username already taken.')
                return redirect('admin_profile')
            
            request.user.username = username
            request.user.email = email
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()
            messages.success(request, 'Profile updated successfully.')
            
        elif action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters.')
            else:
                request.user.set_password(new_password)
                request.user.must_change_password = False
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
        
        return redirect('admin_profile')
    
    return render(request, 'core/admin_profile.html')