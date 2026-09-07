import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UUIDModel(models.Model):
    """Base entity ที่กำหนด UUID primary key ให้ทุก domain object."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class University(UUIDModel):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "universities"

    def __str__(self):
        return self.name


class Faculty(UUIDModel):
    university = models.ForeignKey(
        University, on_delete=models.CASCADE, related_name="faculties"
    )
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "faculties"

    def __str__(self):
        return self.name


class Department(UUIDModel):
    faculty = models.ForeignKey(
        Faculty, on_delete=models.CASCADE, related_name="departments"
    )
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Curriculum(UUIDModel):
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="curricula"
    )
    name = models.CharField(max_length=255)
    year = models.PositiveIntegerField()
    subjects = models.ManyToManyField(
        "Subject", through="CurriculumSubject", related_name="curricula"
    )

    class Meta:
        ordering = ["-year", "name"]

    def __str__(self):
        return f"{self.name} ({self.year})"


class Subject(UUIDModel):
    """ตัววิชาไม่มีประเภท Core/Major/GenEd ในตัวเอง."""

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subjects",
    )
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=255)
    credit = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}"


class CurriculumSubject(UUIDModel):
    class RequirementType(models.TextChoices):
        CORE = "Core", "Core"
        MAJOR = "Major", "Major"
        GEN_ED = "GenEd", "General Education"
        ELECTIVE = "Elective", "Elective"

    curriculum = models.ForeignKey(
        Curriculum, on_delete=models.CASCADE, related_name="subject_requirements"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="curriculum_requirements"
    )
    type = models.CharField(max_length=10, choices=RequirementType.choices)
    semester_recommended = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
    )
    year_recommended = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["curriculum", "subject"],
                name="unique_curriculum_subject",
            )
        ]
        ordering = ["year_recommended", "semester_recommended", "subject__code"]

    def __str__(self):
        return f"{self.curriculum} - {self.subject.code} ({self.type})"


class Student(UUIDModel):
    curriculum = models.ForeignKey(
        Curriculum, on_delete=models.PROTECT, related_name="students"
    )
    student_code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["student_code"]

    def __str__(self):
        return f"{self.student_code} - {self.name}"


class OpenClass(UUIDModel):
    """การเปิดวิชาหนึ่งในปีการศึกษาและภาคเรียนที่กำหนด."""

    subject = models.ForeignKey(
        Subject, on_delete=models.PROTECT, related_name="open_classes"
    )
    academic_year = models.PositiveIntegerField()
    semester = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)]
    )

    class Meta:
        ordering = ["-academic_year", "semester", "subject__code"]

    def __str__(self):
        return f"{self.subject.code} - {self.semester}/{self.academic_year}"


class Section(UUIDModel):
    open_class = models.ForeignKey(
        OpenClass, on_delete=models.CASCADE, related_name="sections"
    )
    section_no = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["open_class", "section_no"], name="unique_open_class_section"
            )
        ]
        ordering = ["open_class", "section_no"]

    @property
    def enrolled_count(self):
        return self.enrollments.filter(status=Enrollment.Status.ENROLLED).count()

    def has_available_seat(self):
        return self.capacity is None or self.enrolled_count < self.capacity

    def __str__(self):
        return f"{self.open_class} Section {self.section_no}"


class Enrollment(UUIDModel):
    class Status(models.TextChoices):
        ENROLLED = "Enrolled", "Enrolled"
        WITHDRAWN = "Withdrawn", "Withdrawn"
        COMPLETED = "Completed", "Completed"
        FAILED = "Failed", "Failed"

    ALLOWED_GRADES = {"A", "B+", "B", "C+", "C", "D+", "D", "F"}

    student = models.ForeignKey(
        Student, on_delete=models.PROTECT, related_name="enrollments"
    )
    section = models.ForeignKey(
        Section, on_delete=models.PROTECT, related_name="enrollments"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ENROLLED
    )
    grade = models.CharField(max_length=5, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "section"], name="unique_student_section"
            )
        ]

    def clean(self):
        if self.grade and self.grade not in self.ALLOWED_GRADES:
            raise ValidationError({"grade": "เกรดไม่ถูกต้อง"})
        if self.status in {self.Status.COMPLETED, self.Status.FAILED} and not self.grade:
            raise ValidationError({"grade": "สถานะ Completed/Failed ต้องมีเกรด"})

    def record_grade(self, grade):
        if grade not in self.ALLOWED_GRADES:
            raise ValidationError("เกรดไม่ถูกต้อง")
        self.grade = grade
        self.status = self.Status.FAILED if grade == "F" else self.Status.COMPLETED
        self.full_clean()
        self.save(update_fields=["grade", "status"])

    def __str__(self):
        return f"{self.student.student_code} -> {self.section}"
