# ============================================================
# STUDENT MANAGER
# This file handles adding, viewing, searching, editing,
# deleting and analysing student records.
# ============================================================

from datetime import datetime

from grade_functions import get_student_result, validate_marks
from storage import load_students, save_students


def add_student(student_id, name, student_class, marks, email=""):
    """Validate the details and add a new student."""
    student_id = str(student_id).strip().upper()
    name = str(name).strip()
    student_class = str(student_class).strip()
    email = str(email).strip()

    # Required field checks.
    if not student_id:
        return False, "Student ID is required."
    if not name:
        return False, "Student name is required."
    if not student_class:
        return False, "Class or course is required."

    # Check marks before saving.
    error = validate_marks(marks)
    if error:
        return False, error

    students = load_students()

    # Student IDs must be unique.
    for student in students:
        if student["id"].upper() == student_id:
            return False, "This student ID already exists."

    # Store details and marks in one dictionary.
    new_student = {
        "id": student_id,
        "name": name,
        "class": student_class,
        "email": email,
        "marks": marks,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }

    students.append(new_student)
    save_students(students)
    return True, "Student added successfully."


def view_students():
    """Return the complete list of students."""
    return load_students()


def search_student(student_id):
    """Find and return one student using their ID."""
    student_id = str(student_id).strip().upper()

    for student in load_students():
        if student["id"].upper() == student_id:
            return student

    return None


def update_student(student_id, name, student_class, marks, email=""):
    """Update an existing student's details and marks."""
    student_id = str(student_id).strip().upper()
    name = str(name).strip()
    student_class = str(student_class).strip()
    email = str(email).strip()

    if not name or not student_class:
        return False, "Name and class/course are required."

    error = validate_marks(marks)
    if error:
        return False, error

    students = load_students()

    for student in students:
        if student["id"].upper() == student_id:
            student["name"] = name
            student["class"] = student_class
            student["email"] = email
            student["marks"] = marks
            student["updated_at"] = datetime.now().isoformat(timespec="seconds")

            save_students(students)
            return True, "Student record updated successfully."

    return False, "Student not found."


def delete_student(student_id):
    """Delete one student using their ID."""
    student_id = str(student_id).strip().upper()
    students = load_students()

    for student in students:
        if student["id"].upper() == student_id:
            students.remove(student)
            save_students(students)
            return True, "Student deleted successfully."

    return False, "Student not found."


def get_student_report(student_id):
    """Return student details together with calculated results."""
    student = search_student(student_id)

    if student is None:
        return None

    result = get_student_result(student["marks"])

    # Combine the original record and calculated result.
    report = student.copy()
    report.update(result)
    return report


def get_class_statistics():
    """Calculate class totals, average, pass rate and grade counts."""
    students = load_students()

    if not students:
        return {
            "total_students": 0,
            "class_average": 0,
            "pass_count": 0,
            "fail_count": 0,
            "pass_rate": 0,
            "topper": None,
            "grade_counts": {},
            "subject_averages": {},
        }

    reports = []
    for student in students:
        reports.append((student, get_student_result(student["marks"])))

    percentages = [result["percentage"] for student, result in reports]
    pass_count = sum(
        1 for student, result in reports if result["result"] == "Pass"
    )
    fail_count = len(reports) - pass_count

    # Count how many students received each overall grade.
    grade_counts = {}
    for student, result in reports:
        grade = result["grade"]
        grade_counts[grade] = grade_counts.get(grade, 0) + 1

    # Calculate the average mark for each subject.
    subject_averages = {}
    for subject in students[0]["marks"]:
        subject_marks = [
            student["marks"].get(subject, 0) for student in students
        ]
        subject_averages[subject] = round(
            sum(subject_marks) / len(subject_marks), 2
        )

    # Find the student with the highest overall percentage.
    topper_student, topper_result = max(
        reports, key=lambda item: item[1]["percentage"]
    )

    return {
        "total_students": len(students),
        "class_average": round(sum(percentages) / len(percentages), 2),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": round((pass_count / len(students)) * 100, 2),
        "topper": {
            "id": topper_student["id"],
            "name": topper_student["name"],
            "percentage": topper_result["percentage"],
            "grade": topper_result["grade"],
        },
        "grade_counts": grade_counts,
        "subject_averages": subject_averages,
    }
