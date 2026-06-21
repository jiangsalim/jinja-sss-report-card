# Jinja SSS Report Card System

Online Report Card Issuing System for Jinja Senior Secondary School, Uganda.

---

## Features

### Admin Dashboard
- Real-time stats (students, teachers, classes, streams, grades)
- Class & stream management (O-Level S1-S4, A-Level S5-S6)
- Subject catalog with compulsory, optional, principal & subsidiary categories
- Student management (CSV import, manual add, edit, delete)
- Teacher management (CSV import, manual add, credentials, assignments)
- Grade monitoring & finalization
- Secure report cards with QR verification
- Student promotion (Term 3 only)
- School settings & term management
- System reset (super admin only)

### Teacher Portal
- View assigned classes
- Create assessments with custom max marks & weights
- Enter student marks
- Auto-calculation of percentages & final grades
- Submit grades for review

### Student/Parent Portal
- Simple login (admission number + class-stream)
- View published report cards
- Access past term reports
- Print-friendly reports
- Mobile responsive design

### Report Card Security
- 12-character unique verification code
- QR code for online verification
- Watermark with student details
- Anti-photocopy pattern
- Online verification page

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x (Python 3.11+) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | Django Templates + Custom CSS |
| Icons | SVG |
| CSV Processing | Pandas |
| PDF Generation | WeasyPrint |
| QR Codes | qrcode[pil] |
| Background Tasks | Celery + Redis |

---

## Installation

### Prerequisites
- Python 3.11+
- Git
- Virtual environment (recommended)

### Setup

```bash
# Clone the repository
git clone https://github.com/jiangsalim/jinja-sss-report-card.git
cd jinja-sss-report-card

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create super admin
python manage.py createsuperuser

# Run server
python manage.py runserver
Seed Grading Scale (Optional)
bash
python manage.py shell
python
from apps.grading.models import GradingScale

scales = [
    ('A', 80, 100, 'Excellent'),
    ('B+', 75, 79, 'Very Good'),
    ('B', 70, 74, 'Good'),
    ('C', 60, 69, 'Credit'),
    ('D', 50, 59, 'Pass'),
    ('F', 0, 49, 'Fail'),
]

for letter, min_p, max_p, remark in scales:
    GradingScale.objects.get_or_create(
        grade_letter=letter,
        defaults={'min_percent': min_p, 'max_percent': max_p, 'remark': remark}
    )

print('Grading scale seeded!')
exit()
URL Structure
URL	Description
/login/	Staff login
/portal/login/	Student/Parent login
/admin-dashboard/	Admin dashboard
/teacher-dashboard/	Teacher dashboard
/academic/classes/	Class management
/academic/terms/	Term management
/students/	Student list
/students/import/	O-Level CSV import
/students/import-alevel/	A-Level CSV import
/teachers/	Teacher list
/teachers/assignments/	Teacher assignments
/grades/scale/	Grading scale
/grades/status/	Grade monitoring
/grades/report/<id>/	View report card
/grades/verify/<code>/	Verify report
/school-settings/	School settings
/system-reset/	System reset
/profile/	Admin profile
CSV Import Formats
O-Level Students
Column	Required	Example
admission_no	Yes	ADM-001
first_name	Yes	John
last_name	Yes	Doe
gender	Yes	M or F
class_name	Yes	Senior 1
stream_name	Yes	A
optional_subjects	No	F/A, COMP
parent_name	No	James Doe
parent_phone	No	+256712345678
parent_email	No	james@email.com
A-Level Students
Column	Required	Example
admission_no	Yes	ADM-500
first_name	Yes	Alice
last_name	Yes	Mbeki
gender	Yes	F
class_name	Yes	Senior 5
stream_name	Yes	A
subject_1	Yes	PHY
subject_2	Yes	CHEM
subject_3	Yes	MATH
subsidiary	No	ICT
parent_name	No	Robert Mbeki
parent_phone	No	+256712345678
Promotion Logic
Only available during Term 3

S1 to S2, S2 to S3, S3 to S4, S5 to S6

S4 & S6 students graduate (archived)

S1 & S5 streams wiped for new intake

Classes & subjects preserved

Project Structure
text
jinja_sss_report_card/
├── apps/
│   ├── core/           # Dashboard, settings, reset
│   ├── accounts/       # User model, auth, portal
│   ├── academic/       # Classes, streams, subjects
│   ├── students/       # Student CRUD, imports
│   ├── teachers/       # Teacher CRUD, assignments
│   ├── grading/        # Assessments, grades, reports
│   └── parents/        # Parent/student portal
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── media/              # Uploads, exports
├── config/             # Django settings
├── requirements.txt    # Dependencies
└── manage.py           # Django CLI
Author
Jiang Salim

GitHub: @jiangsalim

Email: jaingsalim@gmail.com

License
This project is proprietary software developed for Jinja Senior Secondary School.

Built with Django for Jinja SSS, Uganda