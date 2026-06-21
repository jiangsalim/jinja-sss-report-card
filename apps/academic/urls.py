from django.urls import path
from . import views

urlpatterns = [
    path('classes/', views.class_list, name='class_list'),
    path('classes/<int:class_id>/', views.class_detail, name='class_detail'),
    path('classes/<int:class_id>/create-stream/', views.create_stream, name='create_stream'),
    path('streams/<int:stream_id>/delete/', views.delete_stream, name='delete_stream'),
    path('streams/<int:stream_id>/officials/', views.stream_officials, name='stream_officials'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('terms/', views.manage_terms, name='manage_terms'),
]