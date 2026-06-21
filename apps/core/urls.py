from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('parent-dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('school-settings/', views.school_settings, name='school_settings'),
    path('system-reset/', views.system_reset, name='system_reset'),
    path('profile/', views.admin_profile, name='admin_profile'),
]