from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('', include('apps.core.urls')),
    path('academic/', include('apps.academic.urls')),
    path('students/', include('apps.students.urls')),
    path('teachers/', include('apps.teachers.urls')),
    path('grades/', include('apps.grading.urls')),
]