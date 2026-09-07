from django.core.management.base import BaseCommand

from academics.models import (
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
from academics.services import EnrollmentService


class Command(BaseCommand):
    help = "สร้างข้อมูลสาธิตตาม University Domain Model (สั่งซ้ำได้)"

    def handle(self, *args, **options):
        university, _ = University.objects.get_or_create(
            name="มหาวิทยาลัยตัวอย่าง"
        )
        faculty, _ = Faculty.objects.get_or_create(
            university=university, name="คณะวิศวกรรมศาสตร์"
        )
        department, _ = Department.objects.get_or_create(
            faculty=faculty, name="วิศวกรรมคอมพิวเตอร์"
        )
        curriculum, _ = Curriculum.objects.get_or_create(
            department=department,
            name="Computer Engineering Curriculum",
            year=2026,
        )
        subject, _ = Subject.objects.get_or_create(
            code="CPE101",
            defaults={
                "department": department,
                "name": "Computer Programming",
                "credit": 3,
            },
        )
        CurriculumSubject.objects.get_or_create(
            curriculum=curriculum,
            subject=subject,
            defaults={
                "type": CurriculumSubject.RequirementType.MAJOR,
                "year_recommended": 1,
                "semester_recommended": 1,
            },
        )
        student, _ = Student.objects.get_or_create(
            student_code="69000001",
            defaults={"curriculum": curriculum, "name": "สมชาย ใจดี"},
        )
        open_class, _ = OpenClass.objects.get_or_create(
            subject=subject, academic_year=2026, semester=1
        )
        section, _ = Section.objects.get_or_create(
            open_class=open_class,
            section_no="1",
            defaults={"capacity": 40},
        )
        if not student.enrollments.filter(section=section).exists():
            EnrollmentService.enroll(student, section)

        self.stdout.write(self.style.SUCCESS("สร้างข้อมูลตัวอย่างเรียบร้อยแล้ว"))
