from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, PasswordChangeForm
from apps.students.models import Student, Enrollment
from apps.academic.models import AcademicYear, Term

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        return redirect_dashboard(request.user)

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.must_change_password:
                return redirect('first_login')

            return redirect_dashboard(user)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def first_login_view(request):
    if not request.user.must_change_password:
        return redirect_dashboard(request.user)

    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            user = request.user
            if not user.check_password(form.cleaned_data['old_password']):
                messages.error(request, 'Current password is incorrect.')
            else:
                user.set_password(form.cleaned_data['new_password'])
                user.must_change_password = False
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect_dashboard(user)
    else:
        form = PasswordChangeForm()

    return render(request, 'accounts/first_login.html', {'form': form})


def redirect_dashboard(user):
    if user.role in ['super_admin', 'admin']:
        return redirect('admin_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    elif user.role == 'parent':
        return redirect('student_parent_dashboard')
    return redirect('login')


def student_parent_login(request):
    """Custom login for students/parents using admission number + class-stream."""
    if request.method == 'POST':
        admission_no = request.POST.get('admission_no', '').strip()
        class_stream = request.POST.get('class_stream', '').strip()

        if not admission_no or not class_stream:
            messages.error(request, 'Please enter both admission number and class+stream.')
            return render(request, 'parents/login.html')

        # Find the student
        try:
            student = Student.objects.get(admission_no=admission_no)
        except Student.DoesNotExist:
            messages.error(request, 'Student not found. Check your admission number.')
            return render(request, 'parents/login.html')

        # Get current enrollment
        current_year = AcademicYear.objects.filter(is_current=True).first()
        enrollment = Enrollment.objects.filter(
            student=student,
            academic_year=current_year
        ).first()

        if not enrollment:
            messages.error(request, 'You are not enrolled in the current academic year.')
            return render(request, 'parents/login.html')

        # Build all possible formats for matching
        class_name = enrollment.stream.class_obj.name
        stream_name = enrollment.stream.name

        acceptable = []
        acceptable.append(f"{class_name}{stream_name}")
        acceptable.append(f"{class_name} {stream_name}")
        acceptable.append(f"{class_name.replace(' ', '')}{stream_name}")

        class_num = class_name.split()[-1]
        acceptable.append(f"{class_num}{stream_name}")
        acceptable.append(f"{class_num} {stream_name}")
        acceptable.append(f"S{class_num}{stream_name}")
        acceptable.append(f"S{class_num} {stream_name}")
        acceptable.append(f"S.{class_num}{stream_name}")
        acceptable.append(f"S.{class_num} {stream_name}")

        user_input = class_stream.replace(' ', '').upper()

        matched = False
        for fmt in acceptable:
            if fmt.replace(' ', '').upper() == user_input:
                matched = True
                break

        if not matched:
            messages.error(request, 'Incorrect class/stream. Try formats like: Senior 1A, S1A, 1A, or 1 A')
            return render(request, 'parents/login.html')

        # Create or get user for this student
        username = f"student_{admission_no}"
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email=student.parent_email or f"{admission_no}@student.jinjasss.sc.ug",
                password=None,
                first_name=student.first_name,
                last_name=student.last_name,
                role='parent',
                must_change_password=False,
            )
            user.set_unusable_password()
            user.save()

        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        messages.success(request, f'Welcome, {student.first_name}!')
        return redirect('student_parent_dashboard')

    return render(request, 'parents/login.html')


@login_required
def student_parent_dashboard(request):
    """Dashboard for students and parents - shows report cards."""
    student = None
    enrollment = None
    current_report = None
    past_reports = []

    username = request.user.username
    if username.startswith('student_'):
        admission_no = username.replace('student_', '')
        try:
            student = Student.objects.get(admission_no=admission_no)
        except Student.DoesNotExist:
            pass

    if student:
        current_year = AcademicYear.objects.filter(is_current=True).first()
        enrollment = Enrollment.objects.filter(
            student=student,
            academic_year=current_year
        ).first()

        # Check if current term report is published
        if enrollment:
            current_term = Term.objects.filter(academic_year=current_year, is_current=True).first()
            if current_term:
                from apps.grading.models import GradeEntry
                grade_entries = GradeEntry.objects.filter(
                    student_subject__student=student,
                    term=current_term,
                    status='locked'
                )
                if grade_entries.exists():
                    current_report = {
                        'term': current_term,
                        'student_id': student.id,
                    }

        # Get past published reports
        from apps.grading.models import GradeEntry
        past_entries = GradeEntry.objects.filter(
            student_subject__student=student,
            status='locked'
        ).exclude(
            term__is_current=True
        ).select_related('term__academic_year').order_by('-term__academic_year__name', '-term__start_date')

        # Get unique terms
        seen_terms = set()
        for entry in past_entries:
            if entry.term.id not in seen_terms:
                seen_terms.add(entry.term.id)
                past_reports.append({
                    'term': entry.term,
                    'student_id': student.id,
                })

    context = {
        'student': student,
        'enrollment': enrollment,
        'current_report': current_report,
        'past_reports': past_reports,
    }
    return render(request, 'parents/dashboard.html', context)