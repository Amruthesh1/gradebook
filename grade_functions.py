# ============================================================
# GRADE FUNCTIONS
# This file contains the calculations used by the whole app.
# Keeping calculations here avoids repeating them in app.py.
# ============================================================

# A student needs at least this mark in EACH subject to pass.
PASS_MARK = 35


def validate_marks(marks):
    """Check that every subject has a valid mark from 0 to 100."""
    if not marks:
        return "Enter marks for at least one subject."

    for subject, mark in marks.items():
        if not isinstance(mark, (int, float)) or isinstance(mark, bool):
            return f"Marks for {subject} must be a number."
        if mark < 0 or mark > 100:
            return f"Marks for {subject} must be between 0 and 100."

    return None


def calculate_total(marks):
    """Add the marks of all subjects."""
    error = validate_marks(marks)
    if error:
        raise ValueError(error)

    return sum(marks.values())


def calculate_percentage(marks):
    """Calculate percentage assuming every subject is out of 100."""
    total = calculate_total(marks)
    maximum_marks = len(marks) * 100
    return round((total / maximum_marks) * 100, 2)


def calculate_grade(mark_or_percentage):
    """
    Return a grade for one subject mark OR an overall percentage.
    The same grade bands are used for individual subjects and total.
    """
    if mark_or_percentage >= 90:
        return "A"
    elif mark_or_percentage >= 80:
        return "B"
    elif mark_or_percentage >= 70:
        return "C"
    elif mark_or_percentage >= 60:
        return "D"
    elif mark_or_percentage >= 40:
        return "E"
    else:
        return "F"


def check_result(marks):
    """Pass only when the student scores at least 35 in every subject."""
    for mark in marks.values():
        if mark < PASS_MARK:
            return "Fail"

    return "Pass"


def get_student_result(marks):
    """
    Calculate the complete result:
    total, percentage, overall grade, pass/fail,
    and the grade and result for each subject.
    """
    error = validate_marks(marks)
    if error:
        raise ValueError(error)

    total = calculate_total(marks)
    percentage = calculate_percentage(marks)

    # Calculate an individual grade for every subject.
    subject_results = {}
    for subject, mark in marks.items():
        subject_results[subject] = {
            "mark": mark,
            "grade": calculate_grade(mark),
            "result": "Pass" if mark >= PASS_MARK else "Fail",
        }

    return {
        "total": total,
        "maximum_marks": len(marks) * 100,
        "percentage": percentage,
        "grade": calculate_grade(percentage),
        "result": check_result(marks),
        "subject_results": subject_results,
    }
