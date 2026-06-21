from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('first-login/', views.first_login_view, name='first_login'),
    path('portal/', views.student_parent_dashboard, name='student_parent_dashboard'),
    path('portal/login/', views.student_parent_login, name='student_parent_login'),
]