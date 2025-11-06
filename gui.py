# app/gui.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import ttkbootstrap as tkb

# Define some theme colors (used for backgrounds/text where tkb doesn't override)
BG_COLOR = "#F0F0F0"
HEADER_COLOR = "#003366"  # A dark blue
TITLE_COLOR = "#FFFFFF"

class App(tkb.Window):
    """Main application window that manages all frames."""
    def __init__(self, data_manager):
        # 1. Set a theme for the whole application (e.g., 'cosmo' for light/clean)
        super().__init__(themename="cosmo") 
        
        self.data_manager = data_manager
        self.current_user = None
        self.current_role = None

        self.title("VIT University Portal")
        self.geometry("900x600")

        # Container frame to hold all pages
        # Use tkb.Frame for better integration
        self.container = tkb.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.show_frame(LoginFrame)

    def show_frame(self, FrameClass):
        """Raises a frame to the top."""
        # Destroy old role-specific frames on logout
        if FrameClass == LoginFrame:
            for F in self.frames.values():
                if F.__class__ != LoginFrame:
                    F.destroy()
            self.frames = {}
            self.current_user = None
            self.current_role = None
            
        if FrameClass not in self.frames:
            self.frames[FrameClass] = FrameClass(self.container, self)
        
        frame = self.frames[FrameClass]
        frame.grid(row=0, column=0, sticky="nsew")
        
        # Call 'on_show' method if it exists, to refresh data
        if hasattr(frame, "on_show"):
            frame.on_show()
            
        frame.tkraise()

    def attempt_login(self, role, user, password):
        if self.data_manager.validate_login(role, user, password):
            self.current_user = user
            self.current_role = role
            if role == 'student':
                self.show_frame(StudentFrame)
            elif role == 'faculty':
                self.show_frame(FacultyFrame)
            elif role == 'admin':
                self.show_frame(AdminFrame)
            return True
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            return False

# ---------- Login Page ----------

class LoginFrame(tkb.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        main_frame = tkb.Frame(self, padding=40)
        main_frame.pack(expand=True)

        tkb.Label(main_frame, text="🎓 Welcome to VIT University Portal 🎓", 
                  font=("Arial", 24, "bold"), bootstyle="primary").pack(pady=20)

        # Role Selection
        tkb.Label(main_frame, text="Select Role:", font=("Arial", 12)).pack(pady=(10,0))
        self.role = tk.StringVar(value="student")
        
        role_menu = tkb.OptionMenu(main_frame, self.role, "student", "student", "faculty", "admin", bootstyle="info")
        role_menu.pack(pady=5, fill='x')

        # Credentials
        tkb.Label(main_frame, text="Username:", font=("Arial", 12)).pack(pady=(10,0))
        self.user_entry = tkb.Entry(main_frame, font=("Arial", 12))
        self.user_entry.pack(pady=5, fill='x')

        tkb.Label(main_frame, text="Password:", font=("Arial", 12)).pack(pady=(10,0))
        self.pass_entry = tkb.Entry(main_frame, show="*", font=("Arial", 12))
        self.pass_entry.pack(pady=5, fill='x')

        login_button = tkb.Button(main_frame, text="Login", command=self.on_login, bootstyle="primary")
        login_button.pack(pady=5, fill='x', ipady=10)

    def on_login(self):
        role = self.role.get()
        user = self.user_entry.get()
        password = self.pass_entry.get()
        self.controller.attempt_login(role, user, password)

# ---------- Base Dashboard Frame (for common layout) ----------

class DashboardFrame(tkb.Frame):
    """A base class for the Student, Faculty, and Admin dashboards."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # 1. Header
        header = tkb.Frame(self, bootstyle="primary")
        header.pack(fill='x')
        self.header_label = tkb.Label(header, text="Dashboard", font=("Arial", 18, "bold"), bootstyle="inverse-primary")
        self.header_label.pack(side='left', padx=10)
        
        logout_button = tkb.Button(header, text="Logout", command=lambda: controller.show_frame(LoginFrame), bootstyle="danger-outline")
        logout_button.pack(side='right', padx=10)

        # 2. Main Content Area (Paned Window)
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=BG_COLOR, sashwidth=5)
        main_pane.pack(fill='both', expand=True)

        # 3. Left Navigation Pane
        self.nav_pane = tkb.Frame(main_pane, width=250, padding=10)
        self.nav_pane.pack_propagate(False)
        main_pane.add(self.nav_pane, stretch="never")

        # 4. Right Content Pane
        self.content_pane = tkb.Frame(main_pane, padding=20)
        main_pane.add(self.content_pane, stretch="always")
        
    def clear_content_pane(self):
        """Removes all widgets from the content pane."""
        for widget in self.content_pane.winfo_children():
            widget.destroy()

# ---------- Student Dashboard ----------

class StudentFrame(DashboardFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.header_label.config(text=f"🧑‍🎓 Student Dashboard (Welcome, {controller.current_user})")
        
        self.student_courses = {}
        
        tkb.Button(self.nav_pane, text="📅 Time Table", bootstyle="info-outline", command=self.show_timetable).pack(fill='x', pady=5)
        tkb.Button(self.nav_pane, text="📝 Exam Schedule", bootstyle="info-outline", command=self.show_exam_schedule).pack(fill='x', pady=5)
        
        tkb.Label(self.nav_pane, text="My Courses", font=("Arial", 16, "bold")).pack(anchor='w', pady=(10, 5))
        
        self.course_nav_frame = tkb.Frame(self.nav_pane)
        self.course_nav_frame.pack(fill='x', expand=False) 

    def on_show(self):
        self.refresh_course_nav()
        self.show_welcome()

    def refresh_course_nav(self):
        for widget in self.course_nav_frame.winfo_children():
            widget.destroy()
            
        dm = self.controller.data_manager
        student_id = self.controller.current_user
        course_ids = dm.get_courses_for_student(student_id)
        
        if not course_ids:
            tkb.Label(self.course_nav_frame, text="Not enrolled in any courses.").pack()
            return

        for course_id in course_ids:
            course_name = dm.get_course_name(course_id)
            self.student_courses[course_id] = course_name
            
            def create_callback(cid):
                return lambda: self.show_course_dashboard(cid)

            btn = tkb.Button(self.course_nav_frame, 
                             text=course_name, 
                             bootstyle="secondary", 
                             command=create_callback(course_id))
            btn.pack(fill='x', pady=2)

    def show_welcome(self):
        self.clear_content_pane()
        tkb.Label(self.content_pane, text="Welcome to your Dashboard", font=("Arial", 16, "bold")).pack(anchor='w')
        tkb.Label(self.content_pane, text="Select a course from the left menu to view your marks, attendance, and projects.").pack(anchor='w', pady=10)

    def show_course_dashboard(self, course_id):
        self.clear_content_pane()
        dm = self.controller.data_manager
        student_id = self.controller.current_user
        course_name = self.student_courses.get(course_id, course_id)
        
        tkb.Label(self.content_pane, text=f"{course_name} ({course_id})", font=("Arial", 16, "bold")).pack(anchor='w')
        
        # --- Attendance ---
        tkb.Label(self.content_pane, text="Attendance", font=("Arial", 14, "bold"), bootstyle="primary").pack(anchor='w', pady=(20, 5))
        att = dm.get_attendance(student_id, course_id)
        att_text = "No attendance recorded." if att is None else f"Your Attendance is: {att}%"
        tkb.Label(self.content_pane, text=att_text, font=("Arial", 12)).pack(anchor='w')

        # --- Marks ---
        tkb.Label(self.content_pane, text="Marks", font=("Arial", 14, "bold"), bootstyle="primary").pack(anchor='w', pady=(20, 5))
        cols = ('Exam', 'Mark')
        tv_marks = tkb.Treeview(self.content_pane, columns=cols, show='headings', height=4, bootstyle="info")
        for c in cols: tv_marks.heading(c, text=c)
        
        marks = dm.get_marks(student_id, course_id)
        if not marks:
            tv_marks.insert('', 'end', values=("No marks available yet.", ""))
        else:
            for subj, mark in marks.items():
                tv_marks.insert('', 'end', values=(subj, mark))
        tv_marks.pack(fill='x', pady=5)
        
        # --- Projects ---
        tkb.Label(self.content_pane, text="Project Deadlines", font=("Arial", 14, "bold"), bootstyle="primary").pack(anchor='w', pady=(20, 5))
        cols = ('Project Title', 'Due Date')
        tv_projects = tkb.Treeview(self.content_pane, columns=cols, show='headings', height=4, bootstyle="info")
        for c in cols: tv_projects.heading(c, text=c)
        
        projects = dm.get_projects(student_id, course_id)
        if not projects:
            tv_projects.insert('', 'end', values=("No projects assigned.", ""))
        else:
            for p in projects:
                tv_projects.insert('', 'end', values=(p.get('title', 'N/A'), p.get('due', 'TBD')))
        tv_projects.pack(fill='x', pady=5)


    def show_timetable(self):
        self.clear_content_pane()
        tkb.Label(self.content_pane, text="Time Table", font=("Arial", 16, "bold")).pack(anchor='w')
        
        cols = ('Day', '9:00 - 9:50', '10:00 - 10:50', '11:00 - 11:50', '12:00 - 12:50')
        tv = tkb.Treeview(self.content_pane, columns=cols, show='headings', height=5, bootstyle="info")
        for c in cols:
            tv.heading(c, text=c)
            tv.column(c, width=120)
        
        timetable_data = [
            ('Mon', 'Basic Engineering', 'Computation Structures', 'Calculus', ''),
            ('Tue', 'Chemistry', 'Python ', '', 'Calculus'),
            ('Wed', 'Computation Structures', 'Basic Engineering', 'Python', ''),
            ('Thu', 'Chemistry', 'Calculus', 'Computation Structures', ''),
            ('Fri', 'Python', 'Basic Engineering', 'Chemistry', '')
        ]
        for row in timetable_data:
            tv.insert('', 'end', values=row)
            
        tv.pack(fill='x', pady=10)

    def show_exam_schedule(self):
        self.clear_content_pane()
        tkb.Label(self.content_pane, text="Exam Schedule", font=("Arial", 16, "bold")).pack(anchor='w')
        
        cols = ('Subject', 'Date', 'Time')
        tv = tkb.Treeview(self.content_pane, columns=cols, show='headings', bootstyle="info")
        for c in cols: tv.heading(c, text=c)
        
        exams = self.controller.data_manager.get_exam_schedule()
        if not exams:
            tv.insert('', 'end', values=("No exams scheduled.", "", ""))
        else:
            for e in exams:
                tv.insert('', 'end', values=(e.get('subject', 'N/A'), e.get('date', 'TBD'), e.get('time', 'TBD')))
        tv.pack(fill='x', pady=10)
        

# ---------- Faculty Dashboard ----------

class FacultyFrame(DashboardFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.header_label.config(text=f"🤓 Faculty Dashboard (Welcome, {controller.current_user})")
        
        self.faculty_courses = {}

        tkb.Button(self.nav_pane, text="📝 Add Global Exam", bootstyle="info-outline", command=self.show_add_exam).pack(fill='x', pady=5)
        
        tkb.Label(self.nav_pane, text="My Courses", font=("Arial", 16, "bold")).pack(anchor='w', pady=(10, 5))
        
        self.course_nav_frame = tkb.Frame(self.nav_pane)
        self.course_nav_frame.pack(fill='x', expand=False)

    def on_show(self):
        self.refresh_course_nav()
        self.show_welcome()

    def refresh_course_nav(self):
        for widget in self.course_nav_frame.winfo_children():
            widget.destroy()
            
        dm = self.controller.data_manager
        faculty_id = self.controller.current_user
        self.faculty_courses = dm.get_courses_for_faculty(faculty_id)
        
        if not self.faculty_courses:
            tkb.Label(self.course_nav_frame, text="Not assigned to any courses.").pack()
            return

        for course_id, course_name in self.faculty_courses.items():
            def create_callback(cid):
                return lambda: self.show_course_management(cid)

            btn = tkb.Button(self.course_nav_frame, 
                             text=course_name, 
                             bootstyle="secondary", 
                             command=create_callback(course_id))
            btn.pack(fill='x', pady=2)

    def show_welcome(self):
        self.clear_content_pane()
        tkb.Label(self.content_pane, text="Welcome to your Dashboard", font=("Arial", 16, "bold")).pack(anchor='w')
        tkb.Label(self.content_pane, text="Select a course from the left menu to manage students, marks, and projects.").pack(anchor='w', pady=10)

    def show_course_management(self, course_id):
        self.clear_content_pane()
        course_name = self.faculty_courses.get(course_id, course_id)
        
        tkb.Label(self.content_pane, text=f"Manage: {course_name} ({course_id})", font=("Arial", 16, "bold")).pack(anchor='w', pady=(0, 20))
        
        # Use a Notebook (tabs) for clean layout
        notebook = tkb.Notebook(self.content_pane)
        notebook.pack(fill='both', expand=True)
        
        # --- Create tabs ---
        tab_att = tkb.Frame(notebook, padding=10)
        tab_marks = tkb.Frame(notebook, padding=10)
        tab_proj = tkb.Frame(notebook, padding=10)
        
        notebook.add(tab_att, text="Mark Attendance")
        notebook.add(tab_marks, text="Add Marks")
        notebook.add(tab_proj, text="Add Project")
        
        # --- Populate tabs ---
        self.populate_attendance_tab(tab_att, course_id)
        self.populate_marks_tab(tab_marks, course_id)
        self.populate_project_tab(tab_proj, course_id)

    def _create_student_dropdown(self, parent, course_id):
        """Helper to create a student dropdown for a course."""
        dm = self.controller.data_manager
        students = dm.get_students_in_course(course_id)
        
        student_var = tk.StringVar()
        if not students:
            tkb.Label(parent, text="No students enrolled.").pack()
            return None, students
            
        student_menu = tkb.OptionMenu(parent, student_var, "Select Student", *students, bootstyle="secondary")
        student_menu.pack(fill='x', pady=5)
        return student_var, students

    def populate_attendance_tab(self, parent, course_id):
        tkb.Label(parent, text="Select Student:", width=15).pack(anchor='w')
        student_var, students = self._create_student_dropdown(parent, course_id)
        if not students: return
        
        tkb.Label(parent, text="Percentage (0-100):", width=20).pack(anchor='w', pady=(10,0))
        
        vcmd = (parent.register(self.validate_percent), '%P')
        percent_entry = tkb.Entry(parent, width=40, validate='key', validatecommand=vcmd)
        percent_entry.pack(fill='x', pady=5, padx=5)
        
        status_label = tkb.Label(parent, text="", font=("Arial", 10))
        status_label.pack(pady=10)
        
        def on_submit():
            percent = percent_entry.get()
            student = student_var.get()
            if student == "Select Student":
                status_label.config(text="Please select a student.", foreground="red")
                return

            success, message = self.controller.data_manager.set_attendance(student, course_id, percent)
            if success:
                status_label.config(text=message, foreground="green")
                percent_entry.delete(0, 'end')
                student_var.set("Select Student")
            else:
                status_label.config(text=message, foreground="red")
        
        tkb.Button(parent, text="Submit", command=on_submit, bootstyle="success").pack(pady=10, ipadx=10)

    def populate_marks_tab(self, parent, course_id):
        tkb.Label(parent, text="Select Student:", width=15).pack(anchor='w')
        student_var, students = self._create_student_dropdown(parent, course_id)
        if not students: return
        
        tkb.Label(parent, text="Assessment Name:", width=30).pack(anchor='w', pady=(10,0))
        subject_entry = tkb.Entry(parent, width=40)
        subject_entry.pack(fill='x', pady=5, padx=5)

        tkb.Label(parent, text="Mark:", width=20).pack(anchor='w', pady=(10,0))
        vcmd = (parent.register(self.validate_percent), '%P')
        mark_entry = tkb.Entry(parent, width=40, validate='key', validatecommand=vcmd)
        mark_entry.pack(fill='x', pady=5, padx=5)

        status_label = tkb.Label(parent, text="", font=("Arial", 10))
        status_label.pack(pady=10)
        
        def on_submit():
            student = student_var.get()
            subject = subject_entry.get()
            mark = mark_entry.get()
            if student == "Select Student":
                status_label.config(text="Please select a student.", foreground="red")
                return

            success, message = self.controller.data_manager.add_student_mark(student, course_id, subject, mark)
            if success:
                status_label.config(text=message, foreground="green")
                subject_entry.delete(0, 'end')
                mark_entry.delete(0, 'end')
                student_var.set("Select Student")
            else:
                status_label.config(text=message, foreground="red")
        
        tkb.Button(parent, text="Submit", command=on_submit, bootstyle="success").pack(pady=10, ipadx=10)

    def populate_project_tab(self, parent, course_id):
        tkb.Label(parent, text="Project Title:", width=15).pack(anchor='w')
        title_entry = tkb.Entry(parent, width=40)
        title_entry.pack(fill='x', pady=5, padx=5)

        tkb.Label(parent, text="Due Date (e.g., 12 March):", width=25).pack(anchor='w', pady=(10,0))
        date_entry = tkb.Entry(parent, width=40)
        date_entry.pack(fill='x', pady=5, padx=5)
        
        status_label = tkb.Label(parent, text="", font=("Arial", 10))
        status_label.pack(pady=10)
        
        def on_submit():
            title = title_entry.get()
            date = date_entry.get()
            
            success, message = self.controller.data_manager.add_project(course_id, title, date)
            if success:
                status_label.config(text=message, foreground="green")
                title_entry.delete(0, 'end')
                date_entry.delete(0, 'end')
            else:
                status_label.config(text=message, foreground="red")
        
        tkb.Button(parent, text="Submit to All Students in Course", command=on_submit, bootstyle="warning").pack(pady=10, ipadx=10)
        
    def validate_percent(self, P):
        """Validation function: allow empty string or numbers 0-100."""
        if P == "":
            return True
        try:
            val = int(P)
            if 0 <= val <= 100:
                return True
            return False
        except ValueError:
            return False

    def show_add_exam(self):
        self.clear_content_pane()
        tkb.Label(self.content_pane, text="Add Global Exam Schedule", font=("Arial", 16, "bold")).pack(anchor='w', pady=(0, 20))
        
        fields = ["Exam", "Date (e.g., 12 March)", "Time (e.g., 10:00 AM)"]
        entries = {}
        for field in fields:
            row = tkb.Frame(self.content_pane)
            row.pack(fill='x', pady=5)
            tkb.Label(row, text=f"{field}:", width=20).pack(side='left')
            entry = tkb.Entry(row, width=40)
            entry.pack(side='left', fill='x', expand=True, padx=5)
            entries[field] = entry
            
        status_label = tkb.Label(self.content_pane, text="", font=("Arial", 10))
        status_label.pack(pady=10)

        def on_submit():
            values = {field: entry.get() for field, entry in entries.items()}
            success, message = self.controller.data_manager.add_exam(values["Exam"], values["Date (e.g., 12 March)"], values["Time (e.g., 10:00 AM)"])
            if success:
                status_label.config(text=message, foreground="green")
                for entry in entries.values(): entry.delete(0, 'end')
            else:
                status_label.config(text=message, foreground="red")
        
        tkb.Button(self.content_pane, text="Submit", command=on_submit, bootstyle="primary").pack(pady=10, ipadx=10)


# ---------- Admin Dashboard ----------

class AdminFrame(DashboardFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.header_label.config(text=f"👨‍🔧 Admin Dashboard (Welcome, {controller.current_user})")

        tkb.Button(self.nav_pane, text="➕ Add User", bootstyle="info-outline", command=self.show_add_user).pack(fill='x', pady=5)
        tkb.Button(self.nav_pane, text="👥 Manage Users", bootstyle="info-outline", command=self.show_manage_users).pack(fill='x', pady=5)
        
        self.on_show()

    def on_show(self):
        self.show_manage_users()
        
    # *** MODIFIED METHOD WITH GRID FIX ***
    def show_add_user(self):
        self.clear_content_pane()
        tkb.Label(self.content_pane, text="Add New User", font=("Arial", 16, "bold")).pack(anchor='w', pady=(0, 20))
        
        # Frame for the form
        form_frame = tkb.Frame(self.content_pane)
        form_frame.pack(fill='x', expand=True)
        form_frame.columnconfigure(1, weight=1)

        # 1. Role
        tkb.Label(form_frame, text="Role:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        role_var = tk.StringVar(value="student")
        
        # 2. User ID & Password
        tkb.Label(form_frame, text="New User ID:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        id_entry = tkb.Entry(form_frame)
        id_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)

        tkb.Label(form_frame, text="New Password:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        pass_entry = tkb.Entry(form_frame, show="*")
        pass_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        # --- Course Assignment UI (Faculty Only) ---
        
        # Frame to hold the faculty course selection UI
        self.course_assignment_frame = tkb.Frame(form_frame)
        
        tkb.Label(self.course_assignment_frame, text="Assign Courses (Faculty Only):", bootstyle="info").pack(anchor='w', pady=(10, 5))
        
        # Get all courses from DataManager
        dm = self.controller.data_manager
        all_course_data = dm.courses
        self.course_vars = {}
        
        # Create Checkboxes for Courses
        for course_id, data in all_course_data.items():
            var = tk.BooleanVar()
            self.course_vars[course_id] = var
            course_name = f"{data['name']} ({course_id})"
            tkb.Checkbutton(self.course_assignment_frame, 
                            text=course_name, 
                            variable=var).pack(anchor='w', padx=10)

        # Function to show/hide course assignment UI and rearrange buttons
        def update_form_layout(*args):
            # Base row for elements after the password field (which is row 2)
            current_row = 3
            
            if role_var.get() == 'faculty':
                # If faculty, place the assignment frame at the current row
                self.course_assignment_frame.grid(row=current_row, column=0, columnspan=2, sticky='ew', pady=10)
                # Advance the current row for the next elements
                current_row += 1 
            else:
                # If not faculty (i.e., student/admin), ensure the assignment frame is hidden
                self.course_assignment_frame.grid_forget()

            # Place the status label right after the optional course frame
            status_label.grid(row=current_row, column=0, columnspan=2, pady=10)
            current_row += 1

            # Place the submit button right after the status label
            submit_button.grid(row=current_row, column=0, columnspan=2, pady=20, ipadx=10)


        # Attach the update function to the OptionMenu
        role_menu = tkb.OptionMenu(form_frame, role_var, "student", "student", "faculty", bootstyle="info", command=update_form_layout)
        role_menu.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Initialize the status label and submit button objects BEFORE the initial call
        status_label = tkb.Label(form_frame, text="", font=("Arial", 10))
        
        # Define the submit function
        def on_submit():
            role = role_var.get()
            uid = id_entry.get()
            pwd = pass_entry.get()
            
            if not uid or not pwd:
                status_label.config(text="⚠️ Please fill in all fields", foreground="red")
                return
            
            selected_courses = []
            if role == 'faculty':
                # Collect selected courses only if role is faculty
                for course_id, var in self.course_vars.items():
                    if var.get():
                        selected_courses.append(course_id)
                        
            success, message = self.controller.data_manager.add_user(role, uid, pwd, courses=selected_courses)
            
            if success:
                status_label.config(text=f"✅ {message}", foreground="green")
                id_entry.delete(0, 'end')
                pass_entry.delete(0, 'end')
                # Reset faculty course checkboxes
                if role == 'faculty':
                    for var in self.course_vars.values():
                        var.set(False)
                # Refresh the user list
                self.controller.frames[AdminFrame].show_manage_users() 
            else:
                status_label.config(text=f"⚠️ {message}", foreground="red")
        
        submit_button = tkb.Button(form_frame, text="Add User", command=on_submit, bootstyle="primary")

        # Initial call to set the correct layout (defaults to student)
        update_form_layout()

        # Define submit function and button
        def on_submit():
            role = role_var.get()
            uid = id_entry.get()
            pwd = pass_entry.get()
            
            if not uid or not pwd:
                status_label.config(text="⚠️ Please fill in all fields", foreground="red")
                return
            
            selected_courses = []
            if role == 'faculty':
                # Collect selected courses only if role is faculty
                for course_id, var in self.course_vars.items():
                    if var.get():
                        selected_courses.append(course_id)
                        
            success, message = self.controller.data_manager.add_user(role, uid, pwd, courses=selected_courses)
            
            if success:
                status_label.config(text=f"✅ {message}", foreground="green")
                id_entry.delete(0, 'end')
                pass_entry.delete(0, 'end')
                # Reset faculty course checkboxes
                if role == 'faculty':
                    for var in self.course_vars.values():
                        var.set(False)
                # Refresh the user list
                self.controller.frames[AdminFrame].show_manage_users() 
            else:
                status_label.config(text=f"⚠️ {message}", foreground="red")
        
        submit_button = tkb.Button(form_frame, text="Add User", command=on_submit, bootstyle="primary")
        submit_button.grid(row=6, column=0, columnspan=2, pady=20, ipadx=10)

        # Initial call to set the correct layout (defaults to student)
        update_form_layout()

    # ... (rest of AdminFrame)
    def show_manage_users(self):
        self.clear_content_pane()
        tkb.Label(self.content_pane, text="Manage Users", font=("Arial", 16, "bold")).pack(anchor='w')
        
        notebook = tkb.Notebook(self.content_pane)
        notebook.pack(fill='both', expand=True, pady=10)
        
        # --- Student Tab ---
        student_tab = tkb.Frame(notebook, padding=10)
        notebook.add(student_tab, text="Students")
        self.create_user_list_tab(student_tab, "student")
        
        # --- Faculty Tab ---
        faculty_tab = tkb.Frame(notebook, padding=10)
        notebook.add(faculty_tab, text="Faculty")
        self.create_user_list_tab(faculty_tab, "faculty")
        
    def create_user_list_tab(self, parent, role):
        dm = self.controller.data_manager
        
        # Get users
        if role == "student":
            users = dm.get_all_students()
        else:
            users = dm.get_all_faculty()
            
        tkb.Label(parent, text=f"Total Registered: {len(users)}").pack(anchor='w', pady=5)
        
        # --- Frame for Listbox and Scrollbar ---
        list_frame = tkb.Frame(parent)
        list_frame.pack(fill='both', expand=True)
        
        scrollbar = tkb.Scrollbar(list_frame, orient='vertical')
        listbox = tk.Listbox(list_frame, font=("Arial", 12), height=15, yscrollcommand=scrollbar.set) 
        
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side='right', fill='y')
        listbox.pack(side='left', fill='both', expand=True)
        
        for user in users:
            listbox.insert('end', user)
            
        # --- Frame for Buttons ---
        btn_frame = tkb.Frame(parent)
        btn_frame.pack(fill='x', pady=10)

        def on_delete():
            try:
                selected_user = listbox.get(listbox.curselection())
                if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{selected_user}'? This cannot be undone."):
                    return
                
                success, message = dm.delete_user(role, selected_user)
                if success:
                    messagebox.showinfo("Success", message)
                    self.show_manage_users()
                else:
                    messagebox.showerror("Error", message)
            except tk.TclError:
                messagebox.showwarning("Warning", "Please select a user from the list first.")
        
        def on_reset_pass():
            try:
                selected_user = listbox.get(listbox.curselection())
                new_pass = simpledialog.askstring("Reset Password", f"Enter new password for '{selected_user}':", show='*')
                
                if not new_pass:
                    messagebox.showwarning("Cancelled", "Password not changed.")
                    return

                success, message = dm.reset_password(role, selected_user, new_pass)
                if success:
                    messagebox.showinfo("Success", message)
                else:
                    messagebox.showerror("Error", message)
            except tk.TclError:
                messagebox.showwarning("Warning", "Please select a user from the list first.")

        tkb.Button(btn_frame, text="Reset Password", command=on_reset_pass, bootstyle="warning").pack(side='right', padx=5)
        tkb.Button(btn_frame, text="Delete Selected User", command=on_delete, bootstyle="danger").pack(side='right', padx=5)