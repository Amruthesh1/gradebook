# Student Grade Management System

A modular Python and Streamlit mini project for managing student records and analysing academic performance.

## Features

- Add, view, search, update and delete student records
- Unique student ID validation
- Five configurable subject fields in the Streamlit app
- Total marks, percentage, overall grade and pass/fail result
- Subject-wise marks, grade and pass/fail status
- Individual student report card and strongest/weakest subject analysis
- Dashboard with grade distribution, pass/fail distribution, subject averages and student comparison charts
- Light/Dark appearance selector inside the application
- JSON storage so records remain after restarting the app
- CSV and JSON export

## Default grading rules

- A: 90–100
- B: 80–89
- C: 70–79
- D: 60–69
- E: 40–59
- F: below 40

A student must score at least 35 in every subject to pass. These are sample project rules and can be changed in `grade_functions.py`.

## Run on Windows

Open the project folder in VS Code, then run:

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Project files

- `app.py`: Streamlit pages, theme selector, dashboard and charts
- `grade_functions.py`: grade and result calculations
- `student_manager.py`: student record operations and class statistics
- `storage.py`: JSON file reading and writing
- `data/students.json`: saved student records

The `data` folder and JSON file are created automatically if missing.

## Customising subjects

Change the `SUBJECTS` list near the top of `app.py`. Use the same subject names consistently for records. Existing records should be updated if you change the subject list.

## Important limitations

This is an educational local project. It has no login, role permissions, encrypted records or production security. Do not store sensitive real student data in a public deployment.
