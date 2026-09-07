from django.contrib import admin

from .models import (
    Curriculum,
    CurriculumSubject,
    Department,
    Enrollment,
    Faculty,
    OpenClass,
    Section,
    Student,
    Subject,
    University,
)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_code", "name", "curriculum")
    list_filter = ("curriculum",)
    search_fields = ("student_code", "name")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "credit", "department")
    list_filter = ("department",)
    search_fields = ("code", "name")


@admin.register(OpenClass)
class OpenClassAdmin(admin.ModelAdmin):
    list_display = ("subject", "academic_year", "semester")
    list_filter = ("academic_year", "semester")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("open_class", "section_no", "capacity", "enrolled_count")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "section", "status", "grade")
    list_filter = ("status", "section__open_class__academic_year")


admin.site.register(
    [University, Faculty, Department, Curriculum, CurriculumSubject]
)
