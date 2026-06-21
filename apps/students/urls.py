from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('create/', views.create_student, name='create_student'),
    path('<int:student_id>/', views.student_detail, name='student_detail'),
    path('<int:student_id>/edit/', views.edit_student, name='edit_student'),
    path('<int:student_id>/delete/', views.delete_student, name='delete_student'),
    path('import/', views.import_students, name='import_students'),
    path('import-alevel/', views.import_alevel_students, name='import_alevel_students'),
    path('assign-optionals/', views.assign_optionals, name='assign_optionals'),
    path('assign-alevel/', views.assign_alevel_subjects, name='assign_alevel_subjects'),
    path('promote/', views.promote_students, name='promote_students'),
]