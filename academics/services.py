from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import CurriculumSubject, Enrollment, Section, Student


class EnrollmentService:
    """Domain service สำหรับกฎการลงทะเบียนที่เกี่ยวข้องกับหลาย entity."""

    MAX_CREDITS_PER_SEMESTER = 22

    @classmethod
    @transaction.atomic
    def enroll(cls, student, section):
        student = Student.objects.select_for_update().get(pk=student.pk)
        section = Section.objects.select_for_update().select_related(
            "open_class__subject"
        ).get(pk=section.pk)
        open_class = section.open_class

        if not CurriculumSubject.objects.filter(
            curriculum=student.curriculum, subject=open_class.subject
        ).exists():
            raise ValidationError("รายวิชานี้ไม่ได้อยู่ในหลักสูตรของนักศึกษา")
        if Enrollment.objects.filter(student=student, section=section).exists():
            raise ValidationError("นักศึกษาลงทะเบียน Section นี้แล้ว")
        if Enrollment.objects.filter(
            student=student,
            section__open_class__subject=open_class.subject,
            section__open_class__academic_year=open_class.academic_year,
            section__open_class__semester=open_class.semester,
            status=Enrollment.Status.ENROLLED,
        ).exists():
            raise ValidationError("นักศึกษาลงทะเบียนวิชานี้ใน Section อื่นแล้ว")
        if not section.has_available_seat():
            raise ValidationError("Section เต็มแล้ว")

        current_credits = (
            Enrollment.objects.filter(
                student=student,
                section__open_class__academic_year=open_class.academic_year,
                section__open_class__semester=open_class.semester,
                status=Enrollment.Status.ENROLLED,
            ).aggregate(total=Sum("section__open_class__subject__credit"))["total"]
            or 0
        )
        if current_credits + open_class.subject.credit > cls.MAX_CREDITS_PER_SEMESTER:
            raise ValidationError(
                f"หน่วยกิตรวมเกิน {cls.MAX_CREDITS_PER_SEMESTER} หน่วยกิต"
            )

        return Enrollment.objects.create(student=student, section=section)

    @staticmethod
    @transaction.atomic
    def withdraw(enrollment):
        enrollment = Enrollment.objects.select_for_update().get(pk=enrollment.pk)
        if enrollment.status != Enrollment.Status.ENROLLED:
            raise ValidationError("ถอนได้เฉพาะรายการที่มีสถานะ Enrolled")
        enrollment.status = Enrollment.Status.WITHDRAWN
        enrollment.grade = None
        enrollment.full_clean()
        enrollment.save(update_fields=["status", "grade"])
        return enrollment
