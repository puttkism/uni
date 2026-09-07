import uuid

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

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


class UniversityDomainTests(TestCase):
    def setUp(self):
        self.university = University.objects.create(name="มหาวิทยาลัยตัวอย่าง")
        self.faculty = Faculty.objects.create(
            university=self.university, name="คณะวิศวกรรมศาสตร์"
        )
        self.department = Department.objects.create(
            faculty=self.faculty, name="วิศวกรรมคอมพิวเตอร์"
        )
        self.curriculum = Curriculum.objects.create(
            department=self.department,
            name="Computer Engineering Curriculum",
            year=2026,
        )
        self.subject = Subject.objects.create(
            department=self.department,
            code="CPE101",
            name="Computer Programming",
            credit=3,
        )
        CurriculumSubject.objects.create(
            curriculum=self.curriculum,
            subject=self.subject,
            type=CurriculumSubject.RequirementType.MAJOR,
            year_recommended=1,
            semester_recommended=1,
        )
        self.student = Student.objects.create(
            curriculum=self.curriculum,
            student_code="69000001",
            name="สมชาย ใจดี",
        )
        self.open_class = OpenClass.objects.create(
            subject=self.subject, academic_year=2026, semester=1
        )
        self.section = Section.objects.create(
            open_class=self.open_class, section_no="1", capacity=1
        )

    def test_domain_entities_use_uuid(self):
        self.assertIsInstance(self.student.pk, uuid.UUID)
        self.assertIsInstance(self.section.pk, uuid.UUID)

    def test_student_can_enroll_in_curriculum_subject(self):
        enrollment = EnrollmentService.enroll(self.student, self.section)
        self.assertEqual(enrollment.status, Enrollment.Status.ENROLLED)

    def test_duplicate_enrollment_is_rejected(self):
        EnrollmentService.enroll(self.student, self.section)
        with self.assertRaises(ValidationError):
            EnrollmentService.enroll(self.student, self.section)

    def test_subject_outside_curriculum_is_rejected(self):
        other_subject = Subject.objects.create(
            code="FREE101", name="Outside Curriculum", credit=3
        )
        other_class = OpenClass.objects.create(
            subject=other_subject, academic_year=2026, semester=1
        )
        other_section = Section.objects.create(
            open_class=other_class, section_no="1"
        )
        with self.assertRaises(ValidationError):
            EnrollmentService.enroll(self.student, other_section)

    def test_enrollment_can_be_withdrawn(self):
        enrollment = EnrollmentService.enroll(self.student, self.section)
        EnrollmentService.withdraw(enrollment)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.WITHDRAWN)

    def test_f_grade_changes_status_to_failed(self):
        enrollment = EnrollmentService.enroll(self.student, self.section)
        enrollment.record_grade("F")
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.FAILED)

    def test_main_web_pages_are_available(self):
        names = [
            "academics:dashboard",
            "academics:organization",
            "academics:student-list",
            "academics:catalog",
            "academics:open-class-list",
            "academics:enrollment-create",
        ]
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_enrollment_controller_creates_enrollment(self):
        response = self.client.post(
            reverse("academics:enrollment-create"),
            {"student": self.student.pk, "section": self.section.pk},
        )
        self.assertRedirects(
            response, reverse("academics:student-detail", args=[self.student.pk])
        )
        self.assertTrue(
            Enrollment.objects.filter(student=self.student, section=self.section).exists()
        )

    def test_grade_controller_completes_enrollment(self):
        enrollment = EnrollmentService.enroll(self.student, self.section)
        response = self.client.post(
            reverse("academics:enrollment-grade", args=[enrollment.pk]),
            {"grade": "A"},
        )
        self.assertRedirects(
            response, reverse("academics:section-detail", args=[self.section.pk])
        )
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.COMPLETED)

    def test_demo_seed_command_can_run_repeatedly(self):
        call_command("seed_demo", verbosity=0)
        call_command("seed_demo", verbosity=0)
        self.assertTrue(OpenClass.objects.exists())
