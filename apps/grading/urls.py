from django.urls import path
from . import views

urlpatterns = [
    path('<int:assignment_id>/', views.grade_entry, name='grade_entry'),
    path('save-marks/', views.save_marks, name='save_marks'),
    path('<int:assignment_id>/submit/', views.submit_marks, name='submit_marks'),
    path('scale/', views.grading_scale_list, name='grading_scale'),
    path('scale/<int:scale_id>/delete/', views.delete_scale, name='delete_scale'),
    path('status/', views.grade_status, name='grade_status'),
    path('finalize/', views.finalize_grades, name='finalize_grades'),
    path('report/<int:student_id>/', views.report_card, name='report_card'),
    path('verify/<str:code>/', views.verify_report, name='verify_report'),
    path('bulk-reports/', views.bulk_reports, name='bulk_reports'),
]