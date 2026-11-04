# ============================================================
# STORAGE
# This file saves and reads student records from a JSON file.
# JSON storage means records remain available after app restart.
# ============================================================

import json
import os

# Build the data file path relative to this Python project.
PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(PROJECT_FOLDER, "data")
DATA_FILE = os.path.join(DATA_FOLDER, "students.json")


def create_file_if_missing():
    """Create the data folder and an empty JSON file if required."""
    os.makedirs(DATA_FOLDER, exist_ok=True)

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump([], file, indent=4)


def load_students():
    """Read all students from the JSON file."""
    create_file_if_missing()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            students = json.load(file)

        # The main data should always be a list of student records.
        if isinstance(students, list):
            return students
        return []

    except (json.JSONDecodeError, OSError):
        # Return an empty list if the file is empty or cannot be read.
        return []


def save_students(students):
    """Write the complete student list to the JSON file."""
    create_file_if_missing()

    # Save to a temporary file first to reduce the chance of a
    # partially written JSON file if the app is interrupted.
    temporary_file = DATA_FILE + ".tmp"

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(students, file, indent=4, ensure_ascii=False)

    os.replace(temporary_file, DATA_FILE)
