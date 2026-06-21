from .models import GradingScale


def calculate_grade(student_subject, term):
    """Calculate final grade from all assessments for a student-subject-term."""
    assessments = student_subject.assessments.filter(term=term, status='submitted')

    if not assessments:
        return None, None

    total_weighted = 0
    total_weight = 0

    for assessment in assessments:
        if assessment.percentage is not None and assessment.weight > 0:
            total_weighted += float(assessment.percentage) * (float(assessment.weight) / 100)
            total_weight += float(assessment.weight)

    if total_weight == 0:
        # If no weights set, use simple average
        percentages = [float(a.percentage) for a in assessments if a.percentage is not None]
        if percentages:
            final_percent = sum(percentages) / len(percentages)
        else:
            return None, None
    else:
        final_percent = total_weighted

    final_percent = round(final_percent, 2)
    letter = get_letter_grade(final_percent)

    return final_percent, letter


def get_letter_grade(percentage):
    """Convert percentage to letter grade."""
    scale = GradingScale.objects.filter(
        min_percent__lte=percentage,
        max_percent__gte=percentage
    ).first()

    if scale:
        return scale.grade_letter
    return 'F'