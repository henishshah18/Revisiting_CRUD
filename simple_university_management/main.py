# main.py
# To run this file:
# 1. pip install fastapi "uvicorn[standard]"
# 2. uvicorn main:app --reload

from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date
import copy

# --- 1. FastAPI App Initialization ---
app = FastAPI(
    title="University Course Management API",
    description="A simple, single-file API to manage students, courses, and enrollments.",
    version="1.0.0"
)

# --- 2. Pydantic Models (Data Schemas) ---

# Professor Schemas
class ProfessorBase(BaseModel):
    name: str = Field(..., example="Dr. Alan Turing")
    email: str = Field(..., example="alan.turing@bletchleypark.edu")
    department: str = Field(..., example="Computer Science")

class ProfessorCreate(ProfessorBase):
    pass

class ProfessorUpdate(ProfessorBase):
    pass

class Professor(ProfessorBase):
    id: int
    hire_date: date = Field(default_factory=date.today)

# Course Schemas
class CourseBase(BaseModel):
    name: str = Field(..., example="Introduction to Cryptography")
    code: str = Field(..., example="CS101")
    credits: int = Field(..., ge=1, le=5, example=3)
    max_capacity: int = Field(..., ge=1, example=50)

class CourseCreate(CourseBase):
    professor_id: int = Field(..., example=1)

class CourseUpdate(CourseBase):
    professor_id: Optional[int] = Field(None, example=1)

class Course(CourseBase):
    id: int
    professor_id: int
    enrolled_students: int = 0

# Student Schemas
class StudentBase(BaseModel):
    name: str = Field(..., example="Joan Clarke")
    email: str = Field(..., example="joan.clarke@example.com")
    major: str = Field(..., example="Mathematics")
    year: int = Field(..., ge=1, le=5, example=2)

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    pass

class Student(StudentBase):
    id: int
    gpa: float = Field(default=0.0, ge=0.0, le=4.0)

# Enrollment Schemas
class EnrollmentBase(BaseModel):
    student_id: int = Field(..., example=1)
    course_id: int = Field(..., example=1)

class EnrollmentCreate(EnrollmentBase):
    pass

class Enrollment(EnrollmentBase):
    enrollment_date: date = Field(default_factory=date.today)
    grade: Optional[str] = Field(None, example="A")


# --- 3. In-Memory Database ---
db = {
    "professors": {
        1: Professor(id=1, name="Dr. Alan Turing", email="alan.turing@bletchleypark.edu", department="Computer Science"),
    },
    "students": {
        1: Student(id=1, name="Joan Clarke", email="joan.clarke@example.com", major="Mathematics", year=2, gpa=0.0),
    },
    "courses": {
        1: Course(id=1, name="Introduction to Cryptography", code="CS101", credits=3, max_capacity=50, professor_id=1),
    },
    "enrollments": {}, # Key: (student_id, course_id), Value: Enrollment object
}

# ID Counters
next_professor_id = 2
next_student_id = 2
next_course_id = 2

# Grade to GPA point mapping
GRADE_TO_POINTS = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}

# --- 4. Helper Functions ---
def calculate_gpa(student_id: int):
    """Calculates and updates a student's GPA based on their graded courses."""
    if student_id not in db["students"]:
        return

    total_points = 0
    total_credits = 0
    student_enrollments = [e for e in db["enrollments"].values() if e.student_id == student_id and e.grade]

    for enrollment in student_enrollments:
        course = db["courses"].get(enrollment.course_id)
        if course and enrollment.grade in GRADE_TO_POINTS:
            total_points += GRADE_TO_POINTS[enrollment.grade] * course.credits
            total_credits += course.credits
    
    student = db["students"][student_id]
    if total_credits > 0:
        student.gpa = round(total_points / total_credits, 2)
    else:
        student.gpa = 0.0

# --- 5. API Endpoints ---

@app.get("/", tags=["Health Check"])
def read_root():
    return {"message": "Welcome to the University Management API!"}

# --- Professor Endpoints (Full CRUD) ---
@app.post("/professors/", response_model=Professor, status_code=status.HTTP_201_CREATED, tags=["Professors"])
def create_professor(professor: ProfessorCreate):
    global next_professor_id
    new_professor = Professor(id=next_professor_id, **professor.model_dump())
    db["professors"][next_professor_id] = new_professor
    next_professor_id += 1
    return new_professor

@app.get("/professors/", response_model=List[Professor], tags=["Professors"])
def get_all_professors():
    return list(db["professors"].values())

@app.get("/professors/{professor_id}", response_model=Professor, tags=["Professors"])
def get_professor(professor_id: int):
    professor = db["professors"].get(professor_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    return professor

@app.put("/professors/{professor_id}", response_model=Professor, tags=["Professors"])
def update_professor(professor_id: int, professor_update: ProfessorUpdate):
    professor = db["professors"].get(professor_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    
    update_data = professor_update.model_dump()
    for key, value in update_data.items():
        setattr(professor, key, value)
    return professor

@app.delete("/professors/{professor_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Professors"])
def delete_professor(professor_id: int):
    if professor_id not in db["professors"]:
        raise HTTPException(status_code=404, detail="Professor not found")
    
    # Cascading delete logic: Prevent deleting a professor assigned to any course
    for course in db["courses"].values():
        if course.professor_id == professor_id:
            raise HTTPException(status_code=400, detail=f"Cannot delete professor. Reassign courses first (e.g., Course ID: {course.id})")
            
    del db["professors"][professor_id]
    return

# --- Student Endpoints (Full CRUD) ---
@app.post("/students/", response_model=Student, status_code=status.HTTP_201_CREATED, tags=["Students"])
def create_student(student: StudentCreate):
    global next_student_id
    new_student = Student(id=next_student_id, **student.model_dump())
    db["students"][next_student_id] = new_student
    next_student_id += 1
    return new_student

@app.get("/students/", response_model=List[Student], tags=["Students"])
def get_all_students():
    return list(db["students"].values())

@app.get("/students/{student_id}", response_model=Student, tags=["Students"])
def get_student(student_id: int):
    student = db["students"].get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/students/{student_id}", response_model=Student, tags=["Students"])
def update_student(student_id: int, student_update: StudentUpdate):
    student = db["students"].get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    update_data = student_update.model_dump()
    for key, value in update_data.items():
        setattr(student, key, value)
    return student

@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Students"])
def delete_student(student_id: int):
    if student_id not in db["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Cascading delete logic: Remove all enrollments for this student
    enrollments_to_delete = [key for key, enrollment in db["enrollments"].items() if enrollment.student_id == student_id]
    for key in enrollments_to_delete:
        course_id = key[1]
        if course_id in db["courses"]:
            db["courses"][course_id].enrolled_students -= 1
        del db["enrollments"][key]
        
    del db["students"][student_id]
    return

# --- Course Endpoints (Full CRUD) ---
@app.post("/courses/", response_model=Course, status_code=status.HTTP_201_CREATED, tags=["Courses"])
def create_course(course: CourseCreate):
    global next_course_id
    if course.professor_id not in db["professors"]:
        raise HTTPException(status_code=404, detail=f"Professor with id {course.professor_id} not found")
    new_course = Course(id=next_course_id, **course.model_dump())
    db["courses"][next_course_id] = new_course
    next_course_id += 1
    return new_course

@app.get("/courses/", response_model=List[Course], tags=["Courses"])
def get_all_courses():
    return list(db["courses"].values())

@app.get("/courses/{course_id}", response_model=Course, tags=["Courses"])
def get_course(course_id: int):
    course = db["courses"].get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@app.put("/courses/{course_id}", response_model=Course, tags=["Courses"])
def update_course(course_id: int, course_update: CourseUpdate):
    course = db["courses"].get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    update_data = course_update.model_dump(exclude_unset=True)
    if "professor_id" in update_data and update_data["professor_id"] not in db["professors"]:
        raise HTTPException(status_code=404, detail=f"Professor with id {update_data['professor_id']} not found")
        
    for key, value in update_data.items():
        setattr(course, key, value)
    return course

@app.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Courses"])
def delete_course(course_id: int):
    if course_id not in db["courses"]:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Cascading delete logic: Remove all enrollments for this course
    enrollments_to_delete = [key for key, enrollment in db["enrollments"].items() if enrollment.course_id == course_id]
    for key in enrollments_to_delete:
        del db["enrollments"][key]
        
    del db["courses"][course_id]
    return

# --- Enrollment Endpoints ---
@app.post("/enrollments/", response_model=Enrollment, status_code=status.HTTP_201_CREATED, tags=["Enrollments"])
def enroll_student_in_course(enrollment: EnrollmentCreate):
    student_id = enrollment.student_id
    course_id = enrollment.course_id

    if student_id not in db["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    if course_id not in db["courses"]:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course = db["courses"][course_id]
    if course.enrolled_students >= course.max_capacity:
        raise HTTPException(status_code=400, detail="Course is full")
    
    if (student_id, course_id) in db["enrollments"]:
        raise HTTPException(status_code=400, detail="Student is already enrolled in this course")

    new_enrollment = Enrollment(**enrollment.model_dump())
    db["enrollments"][(student_id, course_id)] = new_enrollment
    course.enrolled_students += 1
    return new_enrollment

@app.get("/enrollments/", response_model=List[Enrollment], tags=["Enrollments"])
def get_all_enrollments():
    return list(db["enrollments"].values())

@app.put("/enrollments/{student_id}/{course_id}", response_model=Enrollment, tags=["Enrollments"])
def update_enrollment_grade(student_id: int, course_id: int, grade: str = Query(..., description="The new grade (A, B, C, D, F)")):
    if grade.upper() not in GRADE_TO_POINTS:
        raise HTTPException(status_code=400, detail="Invalid grade. Must be one of A, B, C, D, F.")
    
    enrollment_key = (student_id, course_id)
    if enrollment_key not in db["enrollments"]:
        raise HTTPException(status_code=404, detail="Enrollment record not found")
    
    db["enrollments"][enrollment_key].grade = grade.upper()
    calculate_gpa(student_id) # Recalculate GPA after updating a grade
    return db["enrollments"][enrollment_key]

@app.delete("/enrollments/{student_id}/{course_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Enrollments"])
def drop_course(student_id: int, course_id: int):
    enrollment_key = (student_id, course_id)
    if enrollment_key not in db["enrollments"]:
        raise HTTPException(status_code=404, detail="Enrollment record not found")
    
    if course_id in db["courses"]:
        db["courses"][course_id].enrolled_students -= 1
    
    del db["enrollments"][enrollment_key]
    calculate_gpa(student_id)
    return

# --- Complex Query Endpoints ---
@app.get("/students/{student_id}/courses", response_model=List[Course], tags=["Students"])
def get_student_courses(student_id: int):
    if student_id not in db["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    enrolled_course_ids = [e.course_id for e in db["enrollments"].values() if e.student_id == student_id]
    student_courses = [db["courses"][cid] for cid in enrolled_course_ids if cid in db["courses"]]
    return student_courses

@app.get("/courses/{course_id}/students", response_model=List[Student], tags=["Courses"])
def get_course_roster(course_id: int):
    if course_id not in db["courses"]:
        raise HTTPException(status_code=404, detail="Course not found")
    
    enrolled_student_ids = [e.student_id for e in db["enrollments"].values() if e.course_id == course_id]
    course_roster = [db["students"][sid] for sid in enrolled_student_ids if sid in db["students"]]
    return course_roster

@app.get("/professors/{professor_id}/courses", response_model=List[Course], tags=["Professors"])
def get_professor_teaching_schedule(professor_id: int):
    if professor_id not in db["professors"]:
        raise HTTPException(status_code=404, detail="Professor not found")
    
    professor_courses = [course for course in db["courses"].values() if course.professor_id == professor_id]
    return professor_courses
