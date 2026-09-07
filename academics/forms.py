from django import forms

from .models import (
    Curriculum,
    CurriculumSubject,
    Department,
    Faculty,
    OpenClass,
    Section,
    Student,
    Subject,
    University,
)


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class UniversityForm(StyledModelForm):
    class Meta:
        model = University
        fields = ["name"]
        labels = {"name": "ชื่อมหาวิทยาลัย"}


class FacultyForm(StyledModelForm):
    class Meta:
        model = Faculty
        fields = ["university", "name"]
        labels = {"university": "มหาวิทยาลัย", "name": "ชื่อคณะ"}


class DepartmentForm(StyledModelForm):
    class Meta:
        model = Department
        fields = ["faculty", "name"]
        labels = {"faculty": "คณะ", "name": "ชื่อภาควิชา"}


class CurriculumForm(StyledModelForm):
    class Meta:
        model = Curriculum
        fields = ["department", "name", "year"]
        labels = {
            "department": "ภาควิชา",
            "name": "ชื่อหลักสูตร",
            "year": "ปีหลักสูตร",
        }


class SubjectForm(StyledModelForm):
    class Meta:
        model = Subject
        fields = ["department", "code", "name", "credit"]
        labels = {
            "department": "ภาควิชาเจ้าของวิชา",
            "code": "รหัสวิชา",
            "name": "ชื่อวิชา",
            "credit": "หน่วยกิต",
        }


class CurriculumSubjectForm(StyledModelForm):
    class Meta:
        model = CurriculumSubject
        fields = [
            "curriculum",
            "subject",
            "type",
            "year_recommended",
            "semester_recommended",
        ]
        labels = {
            "curriculum": "หลักสูตร",
            "subject": "รายวิชา",
            "type": "ประเภทในหลักสูตร",
            "year_recommended": "ชั้นปีที่แนะนำ",
            "semester_recommended": "ภาคเรียนที่แนะนำ",
        }


class StudentForm(StyledModelForm):
    class Meta:
        model = Student
        fields = ["curriculum", "student_code", "name"]
        labels = {
            "curriculum": "หลักสูตร",
            "student_code": "รหัสนักศึกษา",
            "name": "ชื่อ-นามสกุล",
        }


class OpenClassForm(StyledModelForm):
    class Meta:
        model = OpenClass
        fields = ["subject", "academic_year", "semester"]
        labels = {
            "subject": "รายวิชา",
            "academic_year": "ปีการศึกษา",
            "semester": "ภาคเรียน",
        }


class SectionForm(StyledModelForm):
    class Meta:
        model = Section
        fields = ["section_no", "capacity"]
        labels = {
            "section_no": "หมายเลข Section",
            "capacity": "ความจุ (เว้นว่างหากไม่จำกัด)",
        }


class EnrollmentRequestForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(), label="นักศึกษา"
    )
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(), label="Section"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.select_related("curriculum")
        self.fields["section"].queryset = Section.objects.select_related(
            "open_class__subject"
        )
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class GradeForm(forms.Form):
    grade = forms.ChoiceField(
        label="ผลการเรียน",
        choices=[
            (grade, grade)
            for grade in ["A", "B+", "B", "C+", "C", "D+", "D", "F"]
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
