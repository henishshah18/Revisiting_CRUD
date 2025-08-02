# main.py
# To run this file:
# 1. pip install fastapi "uvicorn[standard]" email-validator
# 2. uvicorn main:app --reload

from fastapi import FastAPI, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import (BaseModel, EmailStr, Field, field_validator)
from typing import Any, Dict, List, Optional
from datetime import date, datetime, timezone
import re

# --- 1. Custom Exception & Response Models ---

class AppException(Exception):
    """Base class for custom application exceptions."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        **kwargs: Dict[str, Any]
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.extra_info = kwargs

class NotFound(AppException):
    """Custom exception for 404 Not Found errors."""
    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with ID '{resource_id}' not found.",
            error_code=f"{resource.upper()}_NOT_FOUND"
        )

class Conflict(AppException):
    """Custom exception for 409 Conflict errors."""
    def __init__(self, detail: str, error_code: str, **kwargs):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code,
            **kwargs
        )

# --- 2. FastAPI App Initialization & Exception Handlers ---
app = FastAPI(
    title="Enhanced University Course Management API",
    description="A complete API to manage students, courses, and enrollments with structured error and success responses.",
    version="3.0.0"
)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handles custom application exceptions to provide a structured error response."""
    content = {
        "detail": exc.detail,
        "error_code": exc.error_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **exc.extra_info
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation errors to provide a structured field_errors response."""
    field_errors = {}
    for error in exc.errors():
        # Use a tuple for the location to handle nested models
        field_name = " -> ".join(map(str, error["loc"][1:]))
        if field_name not in field_errors:
            field_errors[field_name] = []
        field_errors[field_name].append(error["msg"])

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation failed",
            "field_errors": field_errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

# --- 3. Pydantic Models (Data Schemas) ---

# Professor Schemas
class ProfessorBase(BaseModel):
    name: str = Field(..., example="Dr. Grace Hopper")
    email: EmailStr = Field(..., example="grace.hopper@yale.edu")
    department: str = Field(..., example="Computer Science")

class ProfessorCreate(ProfessorBase):
    hire_date: date = Field(..., example=date(1959, 1, 1))

    @field_validator('hire_date')
    def hire_date_not_in_future(cls, v):
        if v > date.today():
            raise ValueError("Hire date cannot be in the future.")
        return v

class ProfessorUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Rear Admiral Grace Hopper")
    email: Optional[EmailStr] = Field(None, example="grace.hopper@navy.mil")
    department: Optional[str] = Field(None, example="Electrical Engineering")

class Professor(ProfessorBase):
    id: int
    hire_date: date

# Course Schemas
class CourseBase(BaseModel):
    name: str = Field(..., example="Compiler Construction")
    code: str = Field(..., example="CS432")
    credits: int = Field(..., ge=1, le=6, example=3)
    max_capacity: int = Field(..., ge=1, example=30)

    @field_validator('code')
    def validate_course_code(cls, v):
        if not re.match(r'^[A-Z]{2,4}\d{3}$', v):
            raise ValueError('Invalid course code format. Use format like "CS101" or "MATH203".')
        return v.upper()

class CourseCreate(CourseBase):
    professor_id: int = Field(..., example=1)

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Advanced Compiler Construction")
    code: Optional[str] = Field(None, example="CS532")
    credits: Optional[int] = Field(None, ge=1, le=6, example=4)
    max_capacity: Optional[int] = Field(None, ge=1, example=35)
    professor_id: Optional[int] = Field(None, example=1)

class Course(CourseBase):
    id: int
    professor_id: int
    enrolled_students: int = 0

# Student Schemas
class StudentBase(BaseModel):
    name: str = Field(..., example="John von Neumann")
    email: EmailStr = Field(..., example="john.vonneumann@ias.edu")
    major: str = Field(..., example="Chemical Engineering")
    year: int = Field(..., ge=1, le=5, example=4)

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None)
    email: Optional[EmailStr] = Field(None)
    major: Optional[str] = Field(None)
    year: Optional[int] = Field(None, ge=1, le=5)

class Student(StudentBase):
    id: int
    gpa: float = Field(default=0.0, ge=0.0, le=4.0)
    academic_probation: bool = Field(default=False, description="True if GPA is below 2.0")

# Enrollment Schemas
class EnrollmentBase(BaseModel):
    student_id: int = Field(..., example=1)
    course_id: int = Field(..., example=1)

class EnrollmentCreate(EnrollmentBase):
    pass

class Enrollment(EnrollmentBase):
    id: str
    enrollment_date: date = Field(default_factory=date.today)
    grade: Optional[str] = Field(None, pattern=r'^[A-DF]$', example="A")

class EnrollmentSuccessResponse(BaseModel):
    message: str = "Student successfully enrolled"
    enrollment_id: str
    student: Student
    course: Course
    enrollment_date: date

# --- 4. In-Memory Database ---
db = {
    "professors": {
        1: Professor(id=1, name="Dr. Alan Turing", email="alan.turing@bletchleypark.edu", department="Computer Science", hire_date=date(1936, 9, 30)),
    },
    "students": {
        1: Student(id=1, name="Joan Clarke", email="joan.clarke@example.com", major="Mathematics", year=2, gpa=0.0),
    },
    "courses": {
        1: Course(id=1, name="Introduction to Cryptography", code="CS101", credits=3, max_capacity=30, professor_id=1, enrolled_students=1),
    },
    "enrollments": {
        "ENR1": Enrollment(id="ENR1", student_id=1, course_id=1)
    },
}

# ID Counters & GPA Mapping
next_professor_id = 2
next_student_id = 2
next_course_id = 2
next_enrollment_id = 2
GRADE_TO_POINTS = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}

# --- 5. Helper Functions ---
def calculate_gpa(student_id: int):
    student = db["students"].get(student_id)
    if not student: return
    total_points, total_credits = 0, 0
    student_enrollments = [e for e in db["enrollments"].values() if e.student_id == student_id and e.grade]
    for enrollment in student_enrollments:
        course = db["courses"].get(enrollment.course_id)
        if course and enrollment.grade in GRADE_TO_POINTS:
            total_points += GRADE_TO_POINTS[enrollment.grade] * course.credits
            total_credits += course.credits
    student.gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
    student.academic_probation = student.gpa < 2.0

def check_unique_email(email: str, current_id: Optional[int] = None):
    for p in db["professors"].values():
        if p.email == email and p.id != current_id:
            raise Conflict(detail=f"Email '{email}' is already in use.", error_code="EMAIL_ALREADY_EXISTS")
    for s in db["students"].values():
        if s.email == email and s.id != current_id:
            raise Conflict(detail=f"Email '{email}' is already in use.", error_code="EMAIL_ALREADY_EXISTS")

def get_enrollment_key_by_ids(student_id: int, course_id: int) -> Optional[str]:
    for id, enrollment in db["enrollments"].items():
        if enrollment.student_id == student_id and enrollment.course_id == course_id:
            return id
    return None

# --- 6. API Endpoints ---

@app.get("/", tags=["Health Check"])
def read_root():
    return {"message": "Welcome to the University Management API!"}

# --- Professor Endpoints (Full CRUD) ---
@app.post("/professors/", response_model=Professor, status_code=status.HTTP_201_CREATED, tags=["Professors"])
def create_professor(professor_data: ProfessorCreate):
    check_unique_email(professor_data.email)
    global next_professor_id
    new_professor = Professor(id=next_professor_id, **professor_data.model_dump())
    db["professors"][next_professor_id] = new_professor
    next_professor_id += 1
    return new_professor

@app.get("/professors/", response_model=List[Professor], tags=["Professors"])
def get_all_professors(department: Optional[str] = None, page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100)):
    professors = list(db["professors"].values())
    if department:
        professors = [p for p in professors if p.department.lower() == department.lower()]
    start = (page - 1) * size
    return professors[start:start + size]

@app.get("/professors/{professor_id}", response_model=Professor, tags=["Professors"])
def get_professor(professor_id: int):
    professor = db["professors"].get(professor_id)
    if not professor:
        raise NotFound("Professor", professor_id)
    return professor

@app.put("/professors/{professor_id}", response_model=Professor, tags=["Professors"])
def update_professor(professor_id: int, professor_update: ProfessorUpdate):
    professor = db["professors"].get(professor_id)
    if not professor:
        raise NotFound("Professor", professor_id)
    if professor_update.email:
        check_unique_email(professor_update.email, current_id=professor_id)
    update_data = professor_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(professor, key, value)
    return professor

@app.delete("/professors/{professor_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Professors"])
def delete_professor(professor_id: int):
    if professor_id not in db["professors"]:
        raise NotFound("Professor", professor_id)
    assigned_courses = [c.id for c in db["courses"].values() if c.professor_id == professor_id]
    if assigned_courses:
        raise Conflict(
            detail=f"Cannot delete professor. Reassign courses first.",
            error_code="PROFESSOR_HAS_COURSES",
            assigned_courses=assigned_courses
        )
    del db["professors"][professor_id]
    return

# --- Student Endpoints (Full CRUD) ---
@app.post("/students/", response_model=Student, status_code=status.HTTP_201_CREATED, tags=["Students"])
def create_student(student_data: StudentCreate):
    check_unique_email(student_data.email)
    global next_student_id
    new_student = Student(id=next_student_id, **student_data.model_dump())
    db["students"][next_student_id] = new_student
    next_student_id += 1
    return new_student

@app.get("/students/", response_model=List[Student], tags=["Students"])
def get_all_students(major: Optional[str] = None, year: Optional[int] = None, page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100)):
    students = list(db["students"].values())
    if major: students = [s for s in students if s.major.lower() == major.lower()]
    if year: students = [s for s in students if s.year == year]
    start = (page - 1) * size
    return students[start:start + size]

@app.get("/students/{student_id}", response_model=Student, tags=["Students"])
def get_student(student_id: int):
    student = db["students"].get(student_id)
    if not student:
        raise NotFound("Student", student_id)
    return student

@app.put("/students/{student_id}", response_model=Student, tags=["Students"])
def update_student(student_id: int, student_update: StudentUpdate):
    student = db["students"].get(student_id)
    if not student:
        raise NotFound("Student", student_id)
    if student_update.email:
        check_unique_email(student_update.email, current_id=student_id)
    update_data = student_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(student, key, value)
    return student

@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Students"])
def delete_student(student_id: int):
    if student_id not in db["students"]:
        raise NotFound("Student", student_id)
    enrollments_to_delete = [eid for eid, e in db["enrollments"].items() if e.student_id == student_id]
    for eid in enrollments_to_delete:
        course_id = db["enrollments"][eid].course_id
        if course_id in db["courses"]:
            db["courses"][course_id].enrolled_students -= 1
        del db["enrollments"][eid]
    del db["students"][student_id]
    return

# --- Course Endpoints (Full CRUD) ---
@app.post("/courses/", response_model=Course, status_code=status.HTTP_201_CREATED, tags=["Courses"])
def create_course(course_data: CourseCreate):
    if course_data.professor_id not in db["professors"]:
        raise NotFound("Professor", course_data.professor_id)
    global next_course_id
    new_course = Course(id=next_course_id, **course_data.model_dump())
    db["courses"][next_course_id] = new_course
    next_course_id += 1
    return new_course

@app.get("/courses/", response_model=List[Course], tags=["Courses"])
def get_all_courses(department: Optional[str] = None, credits: Optional[int] = None, page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100)):
    courses = list(db["courses"].values())
    if department:
        prof_depts = {p.id: p.department for p in db["professors"].values()}
        courses = [c for c in courses if prof_depts.get(c.professor_id, '').lower() == department.lower()]
    if credits:
        courses = [c for c in courses if c.credits == credits]
    start = (page - 1) * size
    return courses[start:start + size]

@app.get("/courses/{course_id}", response_model=Course, tags=["Courses"])
def get_course(course_id: int):
    course = db["courses"].get(course_id)
    if not course:
        raise NotFound("Course", course_id)
    return course

@app.put("/courses/{course_id}", response_model=Course, tags=["Courses"])
def update_course(course_id: int, course_update: CourseUpdate):
    course = db["courses"].get(course_id)
    if not course:
        raise NotFound("Course", course_id)
    update_data = course_update.model_dump(exclude_unset=True)
    if "professor_id" in update_data and update_data["professor_id"] not in db["professors"]:
        raise NotFound("Professor", update_data["professor_id"])
    for key, value in update_data.items():
        setattr(course, key, value)
    return course

@app.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Courses"])
def delete_course(course_id: int):
    if course_id not in db["courses"]:
        raise NotFound("Course", course_id)
    enrollments_to_delete = [eid for eid, e in db["enrollments"].items() if e.course_id == course_id]
    for eid in enrollments_to_delete:
        del db["enrollments"][eid]
    del db["courses"][course_id]
    return

# --- Enrollment Endpoints ---
@app.post("/enrollments/", response_model=EnrollmentSuccessResponse, status_code=status.HTTP_201_CREATED, tags=["Enrollments"])
def enroll_student_in_course(enrollment_data: EnrollmentCreate):
    student = db["students"].get(enrollment_data.student_id)
    if not student: raise NotFound("Student", enrollment_data.student_id)
    course = db["courses"].get(enrollment_data.course_id)
    if not course: raise NotFound("Course", enrollment_data.course_id)
    if course.enrolled_students >= course.max_capacity:
        raise Conflict("Course has reached maximum capacity", "ENROLLMENT_CAPACITY_EXCEEDED",
                       current_enrollment=course.enrolled_students, max_capacity=course.max_capacity)
    if get_enrollment_key_by_ids(student.id, course.id):
        raise Conflict("Student is already enrolled in this course", "DUPLICATE_ENROLLMENT")
    global next_enrollment_id
    enrollment_id = f"ENR{next_enrollment_id}"
    new_enrollment = Enrollment(id=enrollment_id, **enrollment_data.model_dump())
    db["enrollments"][enrollment_id] = new_enrollment
    course.enrolled_students += 1
    next_enrollment_id += 1
    return EnrollmentSuccessResponse(enrollment_id=enrollment_id, student=student, course=course, enrollment_date=new_enrollment.enrollment_date)

@app.get("/enrollments/", response_model=List[Enrollment], tags=["Enrollments"])
def get_all_enrollments():
    return list(db["enrollments"].values())

@app.put("/enrollments/{student_id}/{course_id}/grade", response_model=Enrollment, tags=["Enrollments"])
def update_enrollment_grade(student_id: int, course_id: int, grade: str = Query(..., regex="^[A-DF]$")):
    enrollment_id = get_enrollment_key_by_ids(student_id, course_id)
    if not enrollment_id:
        raise NotFound("Enrollment", f"student_id: {student_id}, course_id: {course_id}")
    enrollment = db["enrollments"][enrollment_id]
    enrollment.grade = grade.upper()
    calculate_gpa(student_id)
    return enrollment

@app.delete("/enrollments/{student_id}/{course_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Enrollments"])
def drop_course(student_id: int, course_id: int):
    enrollment_id = get_enrollment_key_by_ids(student_id, course_id)
    if not enrollment_id:
        raise NotFound("Enrollment", f"student_id: {student_id}, course_id: {course_id}")
    if course_id in db["courses"]:
        db["courses"][course_id].enrolled_students -= 1
    del db["enrollments"][enrollment_id]
    calculate_gpa(student_id)
    return

# --- Complex Query & Analytics Endpoints ---
@app.get("/students/{student_id}/courses", response_model=List[Course], tags=["Students"])
def get_student_courses(student_id: int):
    if student_id not in db["students"]: raise NotFound("Student", student_id)
    enrolled_course_ids = [e.course_id for e in db["enrollments"].values() if e.student_id == student_id]
    return [db["courses"][cid] for cid in enrolled_course_ids if cid in db["courses"]]

@app.get("/courses/{course_id}/students", response_model=List[Student], tags=["Courses"])
def get_course_roster(course_id: int):
    if course_id not in db["courses"]: raise NotFound("Course", course_id)
    enrolled_student_ids = [e.student_id for e in db["enrollments"].values() if e.course_id == course_id]
    return [db["students"][sid] for sid in enrolled_student_ids if sid in db["students"]]

@app.get("/professors/{professor_id}/courses", response_model=List[Course], tags=["Professors"])
def get_professor_teaching_schedule(professor_id: int):
    if professor_id not in db["professors"]: raise NotFound("Professor", professor_id)
    return [c for c in db["courses"].values() if c.professor_id == professor_id]

@app.get("/analytics/students/gpa-distribution", tags=["Analytics"])
def get_gpa_distribution():
    distribution = {"0.0-0.99": 0, "1.0-1.99": 0, "2.0-2.99": 0, "3.0-4.0": 0, "Not Graded": 0}
    for s in db["students"].values():
        if s.gpa == 0 and not any(e.grade for e in db["enrollments"].values() if e.student_id == s.id):
            distribution["Not Graded"] += 1
        elif 0.0 <= s.gpa < 1.0: distribution["0.0-0.99"] += 1
        elif 1.0 <= s.gpa < 2.0: distribution["1.0-1.99"] += 1
        elif 2.0 <= s.gpa < 3.0: distribution["2.0-2.99"] += 1
        elif 3.0 <= s.gpa <= 4.0: distribution["3.0-4.0"] += 1
    return distribution

@app.get("/analytics/courses/enrollment-stats", tags=["Analytics"])
def get_course_enrollment_stats():
    if not db["courses"]: return {"message": "No courses available."}
    enrollments = [c.enrolled_students for c in db["courses"].values()]
    count = len(enrollments)
    total = sum(enrollments)
    return {"total_courses": count, "total_enrollment": total,
            "average_enrollment_per_course": round(total / count, 2) if count > 0 else 0,
            "min_enrollment": min(enrollments) if enrollments else 0,
            "max_enrollment": max(enrollments) if enrollments else 0}