from django.urls import path

from . import views

app_name = "academics"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("organization/", views.organization, name="organization"),
    path("organization/universities/add/", views.university_create, name="university-create"),
    path("organization/faculties/add/", views.faculty_create, name="faculty-create"),
    path("organization/departments/add/", views.department_create, name="department-create"),
    path("organization/curricula/add/", views.curriculum_create, name="curriculum-create"),
    path("students/", views.student_list, name="student-list"),
    path("students/add/", views.student_create, name="student-create"),
    path("students/<uuid:pk>/", views.student_detail, name="student-detail"),
    path("students/<uuid:pk>/edit/", views.student_edit, name="student-edit"),
    path("subjects/", views.catalog, name="catalog"),
    path("subjects/add/", views.subject_create, name="subject-create"),
    path("subjects/<uuid:pk>/edit/", views.subject_edit, name="subject-edit"),
    path("curriculum-subjects/add/", views.curriculum_subject_create, name="curriculum-subject-create"),
    path("open-classes/", views.open_class_list, name="open-class-list"),
    path("open-classes/add/", views.open_class_create, name="open-class-create"),
    path("open-classes/<uuid:pk>/", views.open_class_detail, name="open-class-detail"),
    path("open-classes/<uuid:open_class_pk>/sections/add/", views.section_create, name="section-create"),
    path("sections/<uuid:pk>/", views.section_detail, name="section-detail"),
    path("enrollments/add/", views.enrollment_create, name="enrollment-create"),
    path("enrollments/<uuid:pk>/withdraw/", views.enrollment_withdraw, name="enrollment-withdraw"),
    path("enrollments/<uuid:pk>/grade/", views.enrollment_grade, name="enrollment-grade"),
]
