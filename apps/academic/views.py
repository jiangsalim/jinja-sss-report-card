from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Class, Stream, Subject, ClassCompulsorySubject, StreamOfficials, AcademicYear, Term


@login_required
def class_list(request):
    level = request.GET.get('level', 'O-Level')
    classes = Class.objects.filter(level_type=level).prefetch_related('streams', 'compulsory_subjects__subject')
    return render(request, 'academic/class_list.html', {
        'classes': classes,
        'current_level': level,
    })


@login_required
def class_detail(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    streams = class_obj.streams.all()
    compulsory_subjects = class_obj.compulsory_subjects.all()
    all_subjects = Subject.objects.filter(category='compulsory')

    if request.method == 'POST':
        subject_ids = request.POST.getlist('compulsory_subjects')
        ClassCompulsorySubject.objects.filter(class_obj=class_obj).delete()
        for subject_id in subject_ids:
            subject = get_object_or_404(Subject, id=subject_id)
            ClassCompulsorySubject.objects.create(class_obj=class_obj, subject=subject)
        messages.success(request, f'Compulsory subjects updated for {class_obj.name}')
        return redirect('class_detail', class_id=class_obj.id)

    return render(request, 'academic/class_detail.html', {
        'class_obj': class_obj,
        'streams': streams,
        'compulsory_subjects': compulsory_subjects,
        'all_subjects': all_subjects,
    })


@login_required
def create_stream(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        stream_name = request.POST.get('stream_name', '').strip().upper()
        if stream_name:
            stream, created = Stream.objects.get_or_create(
                class_obj=class_obj,
                name=stream_name
            )
            if created:
                messages.success(request, f'Stream {class_obj.name}-{stream_name} created successfully')
            else:
                messages.warning(request, f'Stream {class_obj.name}-{stream_name} already exists')
    return redirect('class_detail', class_id=class_obj.id)


@login_required
def delete_stream(request, stream_id):
    stream = get_object_or_404(Stream, id=stream_id)
    class_id = stream.class_obj.id
    stream_name = str(stream)
    stream.delete()
    messages.success(request, f'Stream {stream_name} deleted')
    return redirect('class_detail', class_id=class_id)


@login_required
def subject_list(request):
    subjects = Subject.objects.all().order_by('category', 'name')
    return render(request, 'academic/subject_list.html', {'subjects': subjects})


@login_required
def add_subject(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'optional')

        if code and name:
            subject, created = Subject.objects.get_or_create(
                code=code,
                defaults={'name': name, 'category': category}
            )
            if created:
                messages.success(request, f'Subject {code} - {name} added successfully')
            else:
                messages.warning(request, f'Subject {code} already exists')

    return redirect('subject_list')


@login_required
def stream_officials(request, stream_id):
    stream = get_object_or_404(Stream, id=stream_id)
    officials, created = StreamOfficials.objects.get_or_create(stream=stream)

    if request.method == 'POST':
        officials.class_teacher = request.POST.get('class_teacher', '').strip()
        officials.head_of_academics = request.POST.get('head_of_academics', '').strip()
        officials.head_teacher = request.POST.get('head_teacher', '').strip()
        officials.save()
        messages.success(request, f'Officials updated for {stream}')
        return redirect('class_detail', class_id=stream.class_obj.id)

    return render(request, 'academic/stream_officials.html', {
        'stream': stream,
        'officials': officials,
    })


@login_required
def manage_terms(request):
    """Admin: View and switch active term. Year is auto-detected."""
    current_year = timezone.now().year

    # Auto-create academic year if not exists
    academic_year, created = AcademicYear.objects.get_or_create(
        name=str(current_year),
        defaults={
            'is_current': True,
            'start_date': f'{current_year}-02-01',
            'end_date': f'{current_year}-12-15',
        }
    )

    if created:
        # Create default terms
        terms_data = [
            {'name': 'Term 1', 'start_date': f'{current_year}-02-01', 'end_date': f'{current_year}-05-15'},
            {'name': 'Term 2', 'start_date': f'{current_year}-05-25', 'end_date': f'{current_year}-08-30'},
            {'name': 'Term 3', 'start_date': f'{current_year}-09-10', 'end_date': f'{current_year}-12-15'},
        ]
        for i, t in enumerate(terms_data):
            Term.objects.create(
                academic_year=academic_year,
                name=t['name'],
                start_date=t['start_date'],
                end_date=t['end_date'],
                is_current=(i == 0),  # Term 1 active by default
            )
        messages.success(request, f'Academic Year {current_year} created with 3 terms.')

    if request.method == 'POST':
        term_id = request.POST.get('activate_term')
        if term_id:
            # Deactivate all terms for this year
            Term.objects.filter(academic_year=academic_year).update(is_current=False)
            # Activate selected term
            term = get_object_or_404(Term, id=term_id)
            term.is_current = True
            term.save()
            messages.success(request, f'{term.name} is now the active term.')
        return redirect('manage_terms')

    terms = Term.objects.filter(academic_year=academic_year).order_by('start_date')
    active_term = terms.filter(is_current=True).first()

    # Check which term we're likely in based on real date
    today = timezone.now().date()
    suggested_term = None
    for term in terms:
        if term.start_date and term.end_date:
            if term.start_date <= today <= term.end_date:
                suggested_term = term
                break

    context = {
        'academic_year': academic_year,
        'terms': terms,
        'active_term': active_term,
        'suggested_term': suggested_term,
        'today': today,
    }
    return render(request, 'academic/manage_terms.html', context)