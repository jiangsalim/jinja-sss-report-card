from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_list, name='teacher_list'),
    path('<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    path('import/', views.import_teachers, name='import_teachers'),
    path('<int:teacher_id>/credentials/', views.download_credentials, name='download_credentials'),
    path('<int:teacher_id>/reset-password/', views.reset_password, name='reset_password'),
    path('<int:teacher_id>/delete/', views.delete_teacher, name='delete_teacher'),
    path('assignments/', views.assignments, name='teacher_assignments'),
    path('assignments/<int:assignment_id>/remove/', views.remove_assignment, name='remove_assignment'),
    path('create/', views.create_teacher, name='create_teacher'),
]