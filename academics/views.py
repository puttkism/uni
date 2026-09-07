from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    CurriculumForm,
    CurriculumSubjectForm,
    DepartmentForm,
    EnrollmentRequestForm,
    FacultyForm,
    GradeForm,
    OpenClassForm,
    SectionForm,
    StudentForm,
    SubjectForm,
    UniversityForm,
)
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
from .services import EnrollmentService


def dashboard(request):
    context = {
        "student_count": Student.objects.count(),
        "curriculum_count": Curriculum.objects.count(),
        "subject_count": Subject.objects.count(),
        "open_class_count": OpenClass.objects.count(),
        "recent_enrollments": Enrollment.objects.select_related(
            "student", "section__open_class__subject"
        ).order_by("-section__open_class__academic_year")[:8],
        "open_classes": OpenClass.objects.select_related("subject").annotate(
            section_count=Count("sections")
        )[:8],
    }
    return render(request, "academics/dashboard.html", context)


def organization(request):
    return render(
        request,
        "academics/organization.html",
        {
            "universities": University.objects.prefetch_related("faculties"),
            "faculties": Faculty.objects.select_related("university"),
            "departments": Department.objects.select_related("faculty"),
            "curricula": Curriculum.objects.select_related("department"),
        },
    )


def student_list(request):
    query = request.GET.get("q", "").strip()
    students = Student.objects.select_related("curriculum")
    if query:
        students = students.filter(
            Q(student_code__icontains=query) | Q(name__icontains=query)
        )
    return render(
        request, "academics/student_list.html", {"students": students, "query": query}
    )


def student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related("curriculum"), pk=pk)
    enrollments = student.enrollments.select_related(
        "section__open_class__subject"
    ).order_by(
        "-section__open_class__academic_year",
        "section__open_class__semester",
        "section__open_class__subject__code",
    )
    return render(
        request,
        "academics/student_detail.html",
        {"student": student, "enrollments": enrollments},
    )


def catalog(request):
    return render(
        request,
        "academics/catalog.html",
        {
            "subjects": Subject.objects.select_related("department"),
            "requirements": CurriculumSubject.objects.select_related(
                "curriculum", "subject"
            ),
        },
    )


def open_class_list(request):
    classes = OpenClass.objects.select_related("subject").prefetch_related("sections")
    return render(
        request, "academics/open_class_list.html", {"open_classes": classes}
    )


def open_class_detail(request, pk):
    open_class = get_object_or_404(
        OpenClass.objects.select_related("subject").prefetch_related("sections"), pk=pk
    )
    return render(
        request,
        "academics/open_class_detail.html",
        {"open_class": open_class},
    )


def section_detail(request, pk):
    section = get_object_or_404(
        Section.objects.select_related("open_class__subject"), pk=pk
    )
    enrollments = section.enrollments.select_related("student").order_by(
        "student__student_code"
    )
    return render(
        request,
        "academics/section_detail.html",
        {"section": section, "enrollments": enrollments},
    )


def _model_form(request, form_class, title, success_name, instance=None):
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"บันทึก {title} เรียบร้อยแล้ว")
        return redirect(success_name)
    return render(
        request,
        "academics/form.html",
        {"form": form, "title": title, "cancel_url": reverse(success_name)},
    )


def university_create(request):
    return _model_form(request, UniversityForm, "มหาวิทยาลัย", "academics:organization")


def faculty_create(request):
    return _model_form(request, FacultyForm, "คณะ", "academics:organization")


def department_create(request):
    return _model_form(request, DepartmentForm, "ภาควิชา", "academics:organization")


def curriculum_create(request):
    return _model_form(request, CurriculumForm, "หลักสูตร", "academics:organization")


def subject_create(request):
    return _model_form(request, SubjectForm, "รายวิชา", "academics:catalog")


def subject_edit(request, pk):
    return _model_form(
        request,
        SubjectForm,
        "รายวิชา",
        "academics:catalog",
        get_object_or_404(Subject, pk=pk),
    )


def curriculum_subject_create(request):
    return _model_form(
        request,
        CurriculumSubjectForm,
        "วิชาในหลักสูตร",
        "academics:catalog",
    )


def student_create(request):
    return _model_form(request, StudentForm, "นักศึกษา", "academics:student-list")


def student_edit(request, pk):
    return _model_form(
        request,
        StudentForm,
        "ข้อมูลนักศึกษา",
        "academics:student-list",
        get_object_or_404(Student, pk=pk),
    )


def open_class_create(request):
    return _model_form(
        request, OpenClassForm, "การเปิดวิชา", "academics:open-class-list"
    )


def section_create(request, open_class_pk):
    open_class = get_object_or_404(OpenClass, pk=open_class_pk)
    form = SectionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        section = form.save(commit=False)
        section.open_class = open_class
        try:
            section.full_clean()
            section.save()
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "สร้าง Section เรียบร้อยแล้ว")
            return redirect("academics:open-class-detail", pk=open_class.pk)
    return render(
        request,
        "academics/form.html",
        {
            "form": form,
            "title": f"เพิ่ม Section: {open_class}",
            "cancel_url": reverse("academics:open-class-detail", args=[open_class.pk]),
        },
    )


def enrollment_create(request):
    initial = {
        "student": request.GET.get("student"),
        "section": request.GET.get("section"),
    }
    form = EnrollmentRequestForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            enrollment = EnrollmentService.enroll(
                form.cleaned_data["student"], form.cleaned_data["section"]
            )
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "ลงทะเบียนสำเร็จ")
            return redirect("academics:student-detail", pk=enrollment.student_id)
    return render(
        request,
        "academics/form.html",
        {
            "form": form,
            "title": "ลงทะเบียนเรียน",
            "cancel_url": reverse("academics:dashboard"),
        },
    )


def enrollment_withdraw(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    enrollment = get_object_or_404(Enrollment, pk=pk)
    try:
        EnrollmentService.withdraw(enrollment)
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(request, "ถอนรายวิชาเรียบร้อยแล้ว")
    return redirect("academics:student-detail", pk=enrollment.student_id)


def enrollment_grade(request, pk):
    enrollment = get_object_or_404(
        Enrollment.objects.select_related("student", "section__open_class__subject"),
        pk=pk,
    )
    form = GradeForm(request.POST or None, initial={"grade": enrollment.grade})
    if request.method == "POST" and form.is_valid():
        try:
            enrollment.record_grade(form.cleaned_data["grade"])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "บันทึกผลการเรียนเรียบร้อยแล้ว")
            return redirect("academics:section-detail", pk=enrollment.section_id)
    return render(
        request,
        "academics/form.html",
        {
            "form": form,
            "title": f"บันทึกเกรด: {enrollment.student.name}",
            "cancel_url": reverse("academics:section-detail", args=[enrollment.section_id]),
        },
    )
