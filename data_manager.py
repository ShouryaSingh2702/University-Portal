# app/data_manager.py

import os
import json

class DataManager:
    def __init__(self, credentials_file, student_data_file, courses_file):
        self.credentials_file = credentials_file
        self.student_data_file = student_data_file
        self.courses_file = courses_file
        
        self.credentials = {}
        self.student_data = {}
        self.exam_schedule = []
        self.courses = {}
        
        self._load_credentials()
        self._load_courses()
        self._load_student_data()

    # ---------- Credential Management ----------
    
    def _load_credentials(self):
        if os.path.exists(self.credentials_file):
            with open(self.credentials_file, 'r') as c:
                try:
                    self.credentials = json.load(c)
                except json.JSONDecodeError:
                    self.credentials = self._get_default_credentials()
                    self._save_credentials()
        else:
            self.credentials = self._get_default_credentials()
            self._save_credentials()

    def _get_default_credentials(self):
        return {
            'admin': {'admin': 'admin12'},
            'student': {'Harshit': 'harshit12', 'SHILAJIT': 'SHILAJIT12', 'Shourya': 'shourya12'},
            'faculty': {'Prabhu': 'prabhu12', 'Sukanta': 'sukanta12', 'Diddy': 'oiloiloil'}
        }

    def _save_credentials(self):
        with open(self.credentials_file, 'w') as c:
            json.dump(self.credentials, c, indent=4)
            
    def validate_login(self, role, user_id, password):
        return self.credentials.get(role, {}).get(user_id) == password

    def delete_user(self, role, user_id):
        if user_id in self.credentials.get(role, {}):
            del self.credentials[role][user_id]
            self._save_credentials()
            
            # Clean up student data if they were a student
            if role == 'student' and user_id in self.student_data['students']:
                del self.student_data['students'][user_id]
                self._save_student_data()
            
            # Clean up course data if they were a faculty member
            if role == 'faculty':
                for course_id, data in self.courses.items():
                    if data.get('faculty') == user_id:
                        data['faculty'] = None
                self._save_courses()
                
            return True, f"{role.capitalize()} '{user_id}' deleted successfully."
        return False, f"{role.capitalize()} ID not found."

    def reset_password(self, role, user_id, new_password):
        if user_id in self.credentials.get(role, {}):
            self.credentials[role][user_id] = new_password
            self._save_credentials()
            return True, f"Password for {role.capitalize()} '{user_id}' reset successfully."
        return False, f"{role.capitalize()} ID not found."
    
    def get_all_students(self):
        """Returns a list of all student IDs."""
        return list(self.credentials.get('student', {}).keys())

    def get_all_faculty(self):
        """Returns a list of all faculty IDs."""
        return list(self.credentials.get('faculty', {}).keys())
    
    # *** MODIFIED METHOD ***
    def add_user(self, role, user_id, password, courses=None): # Added courses=None
        if not user_id or not password:
            return False, "User ID and password cannot be empty."

        user_id = user_id.strip()

        # Check for existing user in any role
        for r in self.credentials:
            if user_id in self.credentials[r]:
                 return False, f"User ID '{user_id}' already exists in the {r} role."

        if role == 'student':
            # 1. Assign ALL courses to the new student
            all_course_ids = self.get_all_course_ids()
            
            self.credentials['student'][user_id] = password
            self.student_data['students'][user_id] = {
                "enrolled_courses": all_course_ids, # Enroll in all courses
                "course_data": {}
            }
            # Initialize course_data for all enrolled courses
            for course_id in all_course_ids:
                self.student_data['students'][user_id]['course_data'][course_id] = {
                    "attendance": None,
                    "marks": {},
                    "projects": []
                }
            self._save_credentials()
            self._save_student_data()
            return True, f"Student '{user_id}' added successfully and enrolled in all courses ({len(all_course_ids)} total)."

        elif role == 'faculty':
            self.credentials['faculty'][user_id] = password
            
            # 2. Assign selected courses to the faculty member
            assigned_courses = []
            if courses:
                for course_id in courses:
                    if course_id in self.courses:
                        # Update the course data to assign the faculty member
                        self.courses[course_id]['faculty'] = user_id
                        assigned_courses.append(course_id)
                self._save_courses()
                
            self._save_credentials()
            course_list = ", ".join(assigned_courses) if assigned_courses else "No courses assigned."
            return True, f"Faculty '{user_id}' added successfully. Courses assigned: {course_list}"
        
        elif role == 'admin':
             self.credentials['admin'][user_id] = password
             self._save_credentials()
             return True, f"Admin '{user_id}' added successfully."

        else:
            return False, "Invalid role specified."

    # ---------- Student Data Management ----------
    
    def _load_student_data(self):
        if os.path.exists(self.student_data_file):
            with open(self.student_data_file, 'r') as s:
                try:
                    data = json.load(s)
                    self.student_data = data
                    # Load exam schedule separately
                    self.exam_schedule = data.get('exam_schedule', [])
                except json.JSONDecodeError:
                    self.student_data = self._get_default_student_data()
                    self._save_student_data()
        else:
            self.student_data = self._get_default_student_data()
            self._save_student_data()

    def _get_default_student_data(self):
        # Initializes a default student data structure for existing students
        default_data = {"students": {}, "exam_schedule": []}
        for student_id in self.credentials.get('student', {}).keys():
            default_data['students'][student_id] = {
                "enrolled_courses": [],
                "course_data": {}
            }
        return default_data

    def _save_student_data(self):
        # Ensure exam_schedule is saved back into student_data structure
        self.student_data['exam_schedule'] = self.exam_schedule
        with open(self.student_data_file, 'w') as s:
            json.dump(self.student_data, s, indent=4)

    def _get_student_course_data(self, student_id, course_id, save_after=True):
        # Helper function to ensure student/course structure exists
        student_entry = self.student_data['students'].setdefault(student_id, {"enrolled_courses": [], "course_data": {}})
        course_data = student_entry['course_data'].setdefault(course_id, {
            "attendance": None,
            "marks": {},
            "projects": []
        })
        # Ensure enrollment list is updated
        if course_id not in student_entry['enrolled_courses']:
            student_entry['enrolled_courses'].append(course_id)
            if save_after:
                 self._save_student_data()

        return course_data

    def get_courses_for_student(self, student_id):
        """Returns a list of course IDs for a student."""
        return self.student_data.get('students', {}).get(student_id, {}).get('enrolled_courses', [])

    def get_students_in_course(self, course_id):
        """Returns a list of student IDs enrolled in a course."""
        enrolled = []
        for student_id, data in self.student_data.get('students', {}).items():
            if course_id in data.get('enrolled_courses', []):
                enrolled.append(student_id)
        return enrolled

    def set_attendance(self, student_id, course_id, percentage):
        try:
            percent = int(percentage)
            if not (0 <= percent <= 100):
                 return False, "Attendance must be between 0 and 100."
        except ValueError:
            return False, "Attendance must be a valid number."
            
        course_data = self._get_student_course_data(student_id, course_id)
        course_data["attendance"] = percent
        self._save_student_data()
        return True, f"Attendance for {student_id} in {course_id} set to {percent}%."

    def get_attendance(self, student_id, course_id):
        course_data = self.student_data.get('students', {}).get(student_id, {}).get('course_data', {}).get(course_id, {})
        return course_data.get('attendance')

    def get_marks(self, student_id, course_id):
        course_data = self.student_data.get('students', {}).get(student_id, {}).get('course_data', {}).get(course_id, {})
        return course_data.get('marks', {})

    def get_projects(self, student_id, course_id):
        course_data = self.student_data.get('students', {}).get(student_id, {}).get('course_data', {}).get(course_id, {})
        return course_data.get('projects', [])

    def add_student_mark(self, student_id, course_id, subject, mark):
        if not student_id:
            return False, "Student ID cannot be empty."
        if student_id not in self.credentials.get('student', {}):
            return False, "Student not found."
        if not subject or not mark:
            return False, "Subject and Mark fields are required."
        
        course_data = self._get_student_course_data(student_id, course_id)
        course_data["marks"][subject] = mark
        self._save_student_data()
        return True, f"Mark recorded for {student_id} in {course_id}."

    def add_project(self, course_id, title, due_date):
        if not title or not due_date:
            return False, "Project Title and Due Date are required."
            
        project_entry = {"title": title, "due": due_date}
        
        # Get all students in that course
        enrolled_students = self.get_students_in_course(course_id)
        if not enrolled_students:
            return False, "No students are enrolled in this course."
            
        for s in enrolled_students:
            course_data = self._get_student_course_data(s, course_id, save_after=False)
            course_data["projects"].append(project_entry)
        
        self._save_student_data()
        return True, f"Project '{title}' added for all {len(enrolled_students)} enrolled students in {course_id}."

    def get_exam_schedule(self):
        return self.exam_schedule

    def add_exam(self, subject, date, time):
        if not subject or not date or not time:
            return False, "All fields (Subject, Date, Time) are required."
        
        exam = {"subject": subject, "date": date, "time": time}
        self.exam_schedule.append(exam)
        self._save_student_data()
        return True, f"Exam '{subject}' scheduled successfully."

    # ---------- Course Management ----------

    def _load_courses(self):
        if os.path.exists(self.courses_file):
            with open(self.courses_file, 'r') as c:
                try:
                    self.courses = json.load(c)
                except json.JSONDecodeError:
                    self.courses = self._get_default_courses()
                    self._save_courses()
        else:
            self.courses = self._get_default_courses()
            self._save_courses()

    def _get_default_courses(self):
        return {
            "CS101": {"name": "Intro to Python", "faculty": "Prabhu"},
            "MATH201": {"name": "Calculus I", "faculty": "Sukanta"},
            "PHYS101": {"name": "Basic Engineering", "faculty": "Prabhu"},
            "CHEM101": {"name": "Chemistry", "faculty": "Diddy"}
        }

    def _save_courses(self):
        with open(self.courses_file, 'w') as c:
            json.dump(self.courses, c, indent=4)
            
    # *** NEW METHOD ***
    def get_all_course_ids(self):
        """Returns a list of all available course IDs."""
        return list(self.courses.keys())

    def get_course_name(self, course_id):
        return self.courses.get(course_id, {}).get('name', course_id)
    
    def get_courses_for_faculty(self, faculty_id):
        """Returns a dict of {course_id: course_name} taught by a faculty member."""
        faculty_courses = {}
        for course_id, data in self.courses.items():
            if data.get('faculty') == faculty_id:
                faculty_courses[course_id] = data['name']
        return faculty_courses