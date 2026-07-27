# app.py
import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import pandas as pd

class DayOfWeek(Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"

@dataclass
class Class:
    name: str
    teacher: str
    room: str
    start_time: str
    end_time: str
    day: DayOfWeek

@dataclass
class Student:
    id: str
    name: str
    grade: int
    classes: List[Class]
    
    def add_class(self, class_obj: Class):
        if self.has_conflict(class_obj):
            raise ValueError(f"Time conflict detected for class {class_obj.name}")
        self.classes.append(class_obj)
    
    def remove_class(self, class_name: str):
        self.classes = [c for c in self.classes if c.name != class_name]
    
    def has_conflict(self, new_class: Class) -> bool:
        """Check if the new class conflicts with existing classes"""
        new_start = datetime.strptime(new_class.start_time, "%H:%M").time()
        new_end = datetime.strptime(new_class.end_time, "%H:%M").time()
        
        for existing_class in self.classes:
            if existing_class.day != new_class.day:
                continue
                
            exist_start = datetime.strptime(existing_class.start_time, "%H:%M").time()
            exist_end = datetime.strptime(existing_class.end_time, "%H:%M").time()
            
            if (new_start < exist_end and new_end > exist_start):
                return True
        return False
    
    def get_schedule_for_day(self, day: DayOfWeek) -> List[Class]:
        return [c for c in self.classes if c.day == day]
    
    def get_weekly_schedule(self) -> Dict[DayOfWeek, List[Class]]:
        schedule = {day: [] for day in DayOfWeek}
        for class_obj in self.classes:
            schedule[class_obj.day].append(class_obj)
        for day in schedule:
            schedule[day].sort(key=lambda x: datetime.strptime(x.start_time, "%H:%M"))
        return schedule

class SchoolScheduleManager:
    def __init__(self, data_file: str = "school_data.json"):
        self.data_file = data_file
        self.students: Dict[str, Student] = {}
        self.load_data()
    
    def add_student(self, student_id: str, name: str, grade: int):
        if student_id in self.students:
            raise ValueError(f"Student with ID {student_id} already exists")
        self.students[student_id] = Student(id=student_id, name=name, grade=grade, classes=[])
        self.save_data()
    
    def remove_student(self, student_id: str):
        if student_id not in self.students:
            raise ValueError(f"Student with ID {student_id} not found")
        del self.students[student_id]
        self.save_data()
    
    def get_student(self, student_id: str) -> Optional[Student]:
        return self.students.get(student_id)
    
    def get_all_students(self) -> List[Student]:
        return list(self.students.values())
    
    def add_class_to_student(self, student_id: str, class_name: str, teacher: str, 
                            room: str, start_time: str, end_time: str, day: DayOfWeek):
        student = self.get_student(student_id)
        if not student:
            raise ValueError(f"Student with ID {student_id} not found")
        
        new_class = Class(
            name=class_name,
            teacher=teacher,
            room=room,
            start_time=start_time,
            end_time=end_time,
            day=day
        )
        student.add_class(new_class)
        self.save_data()
    
    def remove_class_from_student(self, student_id: str, class_name: str):
        student = self.get_student(student_id)
        if not student:
            raise ValueError(f"Student with ID {student_id} not found")
        student.remove_class(class_name)
        self.save_data()
    
    def save_data(self):
        """Save all student data to JSON file"""
        data = {}
        for student_id, student in self.students.items():
            data[student_id] = {
                "id": student.id,
                "name": student.name,
                "grade": student.grade,
                "classes": [
                    {
                        "name": c.name,
                        "teacher": c.teacher,
                        "room": c.room,
                        "start_time": c.start_time,
                        "end_time": c.end_time,
                        "day": c.day.value
                    }
                    for c in student.classes
                ]
            }
        
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_data(self):
        """Load student data from JSON file"""
        if not os.path.exists(self.data_file):
            return
        
        with open(self.data_file, 'r') as f:
            data = json.load(f)
        
        for student_id, student_data in data.items():
            classes = [
                Class(
                    name=c["name"],
                    teacher=c["teacher"],
                    room=c["room"],
                    start_time=c["start_time"],
                    end_time=c["end_time"],
                    day=DayOfWeek(c["day"])
                )
                for c in student_data["classes"]
            ]
            
            self.students[student_id] = Student(
                id=student_data["id"],
                name=student_data["name"],
                grade=student_data["grade"],
                classes=classes
            )

# Initialize session state
def init_session_state():
    if 'manager' not in st.session_state:
        st.session_state.manager = SchoolScheduleManager()
    if 'selected_student' not in st.session_state:
        st.session_state.selected_student = None

def main():
    st.set_page_config(
        page_title="Student Schedule Management System",
        page_icon="📚",
        layout="wide"
    )
    
    init_session_state()
    manager = st.session_state.manager
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        .schedule-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            border-left: 4px solid #2a5298;
        }
        .class-time {
            font-weight: bold;
            color: #1e3c72;
        }
        .day-header {
            background: #e9ecef;
            padding: 0.5rem;
            border-radius: 5px;
            margin-top: 1rem;
        }
        .stButton > button {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>📚 Student Schedule Management System</h1>
            <p>Efficiently manage student schedules, classes, and timetables</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", 
        "👨‍🎓 Manage Students", 
        "📅 Manage Classes",
        "📖 View Schedule",
        "📊 Reports"
    ])
    
    with tab1:
        display_dashboard(manager)
    
    with tab2:
        manage_students(manager)
    
    with tab3:
        manage_classes(manager)
    
    with tab4:
        view_schedule(manager)
    
    with tab5:
        generate_reports(manager)

def display_dashboard(manager):
    st.header("📊 Dashboard Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Students", len(manager.students))
    
    with col2:
        total_classes = sum(len(student.classes) for student in manager.students.values())
        st.metric("Total Classes", total_classes)
    
    with col3:
        if manager.students:
            avg_classes = total_classes / len(manager.students)
            st.metric("Average Classes per Student", f"{avg_classes:.1f}")
    
    # Recent activity or quick stats
    if manager.students:
        st.subheader("📋 Student Overview")
        data = []
        for student in manager.get_all_students():
            data.append({
                "ID": student.id,
                "Name": student.name,
                "Grade": student.grade,
                "Number of Classes": len(student.classes)
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

def manage_students(manager):
    st.header("👨‍🎓 Student Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add New Student")
        with st.form("add_student_form"):
            student_id = st.text_input("Student ID")
            name = st.text_input("Full Name")
            grade = st.selectbox("Grade", list(range(1, 13)))
            
            submitted = st.form_submit_button("Add Student")
            if submitted:
                try:
                    if not student_id or not name:
                        st.error("Please fill all fields")
                    else:
                        manager.add_student(student_id, name, grade)
                        st.success(f"✅ Student {name} added successfully!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.subheader("Student List")
        students = manager.get_all_students()
        
        if not students:
            st.info("No students registered yet. Add a student using the form.")
        else:
            # Display students in a table
            data = []
            for student in students:
                data.append({
                    "ID": student.id,
                    "Name": student.name,
                    "Grade": student.grade,
                    "Classes": len(student.classes),
                    "Action": student.id
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df[["ID", "Name", "Grade", "Classes"]], use_container_width=True)
            
            # Remove student section
            st.subheader("Remove Student")
            student_to_remove = st.selectbox(
                "Select student to remove",
                options=[(s.id, s.name) for s in students],
                format_func=lambda x: f"{x[1]} ({x[0]})"
            )
            
            if st.button("Remove Student", type="secondary"):
                try:
                    manager.remove_student(student_to_remove[0])
                    st.success(f"✅ Student removed successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def manage_classes(manager):
    st.header("📅 Class Management")
    
    students = manager.get_all_students()
    if not students:
        st.warning("⚠️ Please add students first before managing classes.")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Add Class to Student")
        with st.form("add_class_form"):
            selected_student = st.selectbox(
                "Select Student",
                options=[(s.id, s.name) for s in students],
                format_func=lambda x: f"{x[1]} ({x[0]})"
            )
            
            class_name = st.text_input("Class Name")
            teacher = st.text_input("Teacher Name")
            room = st.text_input("Room Number")
            
            col_time1, col_time2 = st.columns(2)
            with col_time1:
                start_time = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
            with col_time2:
                end_time = st.time_input("End Time", value=datetime.strptime("10:30", "%H:%M").time())
            
            day = st.selectbox(
                "Day of Week",
                options=list(DayOfWeek),
                format_func=lambda x: x.value
            )
            
            submitted = st.form_submit_button("Add Class")
            if submitted:
                try:
                    start_str = start_time.strftime("%H:%M")
                    end_str = end_time.strftime("%H:%M")
                    
                    manager.add_class_to_student(
                        selected_student[0],
                        class_name,
                        teacher,
                        room,
                        start_str,
                        end_str,
                        day
                    )
                    st.success(f"✅ Class {class_name} added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.subheader("Remove Class from Student")
        
        # Select student to view their classes
        student_for_remove = st.selectbox(
            "Select Student",
            options=[(s.id, s.name) for s in students],
            format_func=lambda x: f"{x[1]} ({x[0]})",
            key="remove_class_student"
        )
        
        student_obj = manager.get_student(student_for_remove[0])
        if student_obj and student_obj.classes:
            classes_list = [(c.name, c) for c in student_obj.classes]
            class_to_remove = st.selectbox(
                "Select Class to Remove",
                options=classes_list,
                format_func=lambda x: f"{x[0]} - {x[1].teacher} ({x[1].day.value})"
            )
            
            if st.button("Remove Class", type="secondary"):
                try:
                    manager.remove_class_from_student(student_for_remove[0], class_to_remove[0])
                    st.success(f"✅ Class removed successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.info("No classes for this student")

def view_schedule(manager):
    st.header("📖 View Student Schedule")
    
    students = manager.get_all_students()
    if not students:
        st.warning("⚠️ No students registered.")
        return
    
    selected_student = st.selectbox(
        "Select Student to View Schedule",
        options=[(s.id, s.name) for s in students],
        format_func=lambda x: f"{x[1]} ({x[0]})"
    )
    
    student_obj = manager.get_student(selected_student[0])
    if student_obj:
        st.subheader(f"📅 Weekly Schedule for {student_obj.name} (Grade {student_obj.grade})")
        
        # Create a weekly schedule view
        schedule = student_obj.get_weekly_schedule()
        
        # Display schedule in a nice format
        for day in DayOfWeek:
            classes = schedule[day]
            if classes:
                with st.expander(f"📌 {day.value} ({len(classes)} classes)", expanded=True):
                    for cls in classes:
                        st.markdown(f"""
                            <div class="schedule-card">
                                <strong>{cls.name}</strong><br>
                                👨‍🏫 Teacher: {cls.teacher}<br>
                                🏫 Room: {cls.room}<br>
                                ⏰ <span class="class-time">{cls.start_time} - {cls.end_time}</span>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style="color: #6c757d; padding: 0.5rem;">
                        {day.value}: No classes scheduled
                    </div>
                """, unsafe_allow_html=True)

def generate_reports(manager):
    st.header("📊 Reports & Analytics")
    
    students = manager.get_all_students()
    if not students:
        st.info("No data available for reports.")
        return
    
    report_type = st.selectbox(
        "Select Report Type",
        ["Class Distribution", "Teacher Workload", "Student Class Summary"]
    )
    
    if report_type == "Class Distribution":
        st.subheader("Class Distribution by Day")
        
        # Count classes by day
        day_counts = {day: 0 for day in DayOfWeek}
        for student in students:
            for cls in student.classes:
                day_counts[cls.day] += 1
        
        # Create dataframe for visualization
        data = {
            "Day": [day.value for day in DayOfWeek],
            "Number of Classes": [day_counts[day] for day in DayOfWeek]
        }
        df = pd.DataFrame(data)
        
        st.bar_chart(df.set_index("Day"))
        st.dataframe(df, use_container_width=True)
    
    elif report_type == "Teacher Workload":
        st.subheader("Teacher Workload Analysis")
        
        teacher_classes = {}
        for student in students:
            for cls in student.classes:
                if cls.teacher not in teacher_classes:
                    teacher_classes[cls.teacher] = []
                teacher_classes[cls.teacher].append(cls.name)
        
        data = {
            "Teacher": list(teacher_classes.keys()),
            "Number of Classes": [len(classes) for classes in teacher_classes.values()],
            "Classes": [", ".join(classes[:3]) + ("..." if len(classes) > 3 else "") 
                       for classes in teacher_classes.values()]
        }
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    
    else:  # Student Class Summary
        st.subheader("Student Class Summary")
        
        data = []
        for student in students:
            data.append({
                "Student": student.name,
                "Grade": student.grade,
                "Total Classes": len(student.classes),
                "Classes": ", ".join([c.name for c in student.classes])
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()