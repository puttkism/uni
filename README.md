# University Management System — Django OOD

ระบบบริหารมหาวิทยาลัยตาม Domain Model แบบ Curriculum-based Registration ใช้ UUID เป็น Primary Key และพัฒนาด้วย Django MVT

## Domain Model

```text
University -> Faculty -> Department
Department -> Curriculum
Department -> Subject
Curriculum <-> CurriculumSubject <-> Subject
Student -> Curriculum
Subject -> OpenClass -> Section
Student <-> Enrollment <-> Section
```

ไฟล์สำหรับนำเข้า dbdiagram.io อยู่ที่ `schema.dbml`

## Entities

| Entity | หน้าที่ |
|---|---|
| `University` | มหาวิทยาลัย |
| `Faculty` | คณะที่สังกัดมหาวิทยาลัย |
| `Department` | ภาควิชาที่สังกัดคณะ |
| `Curriculum` | หลักสูตรของภาควิชาและปีหลักสูตร |
| `Subject` | ตัวรายวิชา โดยไม่กำหนดประเภท Core/Major ในตัวเอง |
| `CurriculumSubject` | กำหนดประเภทและปี/เทอมแนะนำของวิชาในแต่ละหลักสูตร |
| `Student` | นักศึกษาที่สังกัดหลักสูตร |
| `OpenClass` | วิชาที่เปิดในปีการศึกษาและภาคเรียนหนึ่ง |
| `Section` | กลุ่มเรียนและความจุของ OpenClass |
| `Enrollment` | เชื่อมนักศึกษากับ Section พร้อมสถานะและเกรด |

## Enumerations

```text
SubjectRequirementType = Core | Major | GenEd | Elective
EnrollmentStatus       = Enrolled | Withdrawn | Completed | Failed
```

## Business Rules

- นักศึกษาลงทะเบียนได้เฉพาะ Subject ที่อยู่ใน Curriculum ของตนเอง
- นักศึกษาลง Subject เดียวกันซ้ำในปี/เทอมเดียวกันไม่ได้
- จำนวนผู้ลงทะเบียนต้องไม่เกินความจุของ Section; หากไม่กำหนด capacity ถือว่าไม่จำกัด
- หน่วยกิตรวมสถานะ Enrolled ต้องไม่เกิน 22 หน่วยกิตต่อเทอม
- ถอนรายวิชาได้เฉพาะ Enrollment สถานะ `Enrolled`
- บันทึกเกรด `F` แล้วสถานะเปลี่ยนเป็น `Failed`
- บันทึกเกรดอื่นแล้วสถานะเปลี่ยนเป็น `Completed`

## ฟังก์ชันหน้าเว็บ

- Dashboard
- จัดการ University, Faculty, Department และ Curriculum
- จัดการ Subject และเพิ่ม Subject เข้า Curriculum
- จัดการ Student
- เปิดวิชาด้วย OpenClass และเพิ่ม Section
- ลงทะเบียน ถอนรายวิชา และบันทึกผลการเรียน
- Django Admin สำหรับจัดการทุก Entity

## วิธีรันในโฟลเดอร์ Ood

```bash
cd /Users/macbooklp/Ood/uni
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py seed_demo
../.venv/bin/python manage.py runserver
```

เปิดระบบที่ <http://127.0.0.1:8000/>

## รันทดสอบ

```bash
../.venv/bin/python manage.py test
```

## โครงสร้างแบบ Django MVT/MVC

```text
MVC Model       -> academics/models.py
MVC Controller  -> academics/views.py + academics/services.py
MVC View        -> academics/templates/academics/*.html
Forms           -> academics/forms.py
Router          -> academics/urls.py + university/urls.py
Database model  -> schema.dbml
```
