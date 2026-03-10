import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="CramNow", layout="wide")

conn = sqlite3.connect("cramnow.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS tasks(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user TEXT,
task TEXT,
priority TEXT,
due_date TEXT,
star INTEGER,
notes TEXT
)
""")

conn.commit()

if "login" not in st.session_state:
    st.session_state.login = False
if "user" not in st.session_state:
    st.session_state.user = ""

if not os.path.exists("profile_pics"):
    os.makedirs("profile_pics")

if not st.session_state.login:
    option = st.selectbox("Select Option", ["Login", "Sign Up"])

    if option == "Sign Up":
        with st.form("signup_form", clear_on_submit=True):
            username = st.text_input("Username")
            password = st.text_input(
                "Password (Must contain 1 Capital Letter and 1 Number)",
                type="password"
            )
            profile_pic = st.file_uploader("Upload Profile Picture (PNG/JPG)", type=["png","jpg","jpeg"])
            submit_signup = st.form_submit_button("Create Account")

            if submit_signup:
                if username == "" or password == "":
                    st.warning("Please fill in all fields")
                elif not re.search(r"[A-Z]", password):
                    st.error("Password must contain a CAPITAL letter")
                elif not re.search(r"[0-9]", password):
                    st.error("Password must contain a NUMBER")
                elif profile_pic is None:
                    st.warning("Please upload a profile picture")
                else:
                    
                    pic_path = f"profile_pics/{username}.png"
                    with open(pic_path, "wb") as f:
                        f.write(profile_pic.getbuffer())
                    
                    c.execute("INSERT INTO users (username,password) VALUES (?,?)", (username,password))
                    conn.commit()
                    st.success("Account created! Please login.")

    if option == "Login":
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")

            if submit_login:
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password))
                user = c.fetchone()
                if user:
                    st.session_state.login = True
                    st.session_state.user = username
                    st.rerun()
                else:
                    st.error("Invalid login")

if st.session_state.login:
    st.sidebar.title("Cram Control")
    page = st.sidebar.radio(
        "Go to",
        ["Dashboard","Add Task","Task List","Calendar","About","Help & Resources"]
    )

    if st.sidebar.button("Logout"):
        st.session_state.login = False
        st.session_state.user = ""
        st.rerun()

    if page == "Dashboard":
        st.title("📊 Dashboard - CramNow")
        pic_path = f"profile_pics/{st.session_state.user}.png"
        if os.path.exists(pic_path):
            st.image(pic_path, width=100)
        st.write(f"Welcome, *{st.session_state.user}*!")

        c.execute("SELECT * FROM tasks WHERE user=?", (st.session_state.user,))
        data = c.fetchall()
        df = pd.DataFrame(data, columns=["ID","User","Task","Priority","Due","Star","Notes"])
        df["Due_dt"] = pd.to_datetime(df["Due"], errors='coerce')

        now = datetime.now()
        notif_tasks = df[df["Due_dt"].notnull() & (df["Due_dt"] - now <= timedelta(hours=24)) & (df["Due_dt"] >= now)]
        if not notif_tasks.empty:
            st.warning("⚠️ Upcoming Tasks within 24 hours:")
            for i,row in notif_tasks.iterrows():
                st.write(f"- {row['Task']} (Due: {row['Due']})")

        total = len(df)
        high = len(df[df["Priority"]=="High"])
        starred = len(df[df["Star"]==1])

        col1,col2,col3 = st.columns(3)
        col1.metric("Total Tasks", total)
        col2.metric("High Priority", high)
        col3.metric("Starred Tasks ⭐", starred)
        st.progress(min(total/10,1.0))

    if page == "Add Task":
        st.title("➕ Add Task")
        task = st.text_input("Task")
        priority = st.radio("Priority", ["Low","Medium","High"])
        due = st.date_input("Due Date")
        star = st.checkbox("Star this task ⭐")
        notes = st.text_area("Notes")
        reminder = st.slider("Reminder Hours Before",1,24,6)

        if st.button("Save Task"):
            c.execute("""
            INSERT INTO tasks(user,task,priority,due_date,star,notes)
            VALUES(?,?,?,?,?,?)
            """,(st.session_state.user,task,priority,due,int(star),notes))
            conn.commit()
            st.success("Task Added!")
            st.balloons()

    if page == "Task List":
        st.title("📋 Task List")
        search_query = st.text_input("Search Tasks by Name")
        filter_option = st.selectbox("Filter", ["All Tasks","Starred","High Priority"])

        c.execute("SELECT * FROM tasks WHERE user=?", (st.session_state.user,))
        data = c.fetchall()
        df = pd.DataFrame(data, columns=["ID","User","Task","Priority","Due","Star","Notes"])
        if filter_option == "Starred":
            df = df[df["Star"]==1]
        if filter_option == "High Priority":
            df = df[df["Priority"]=="High"]
        if search_query:
            df = df[df["Task"].str.contains(search_query, case=False, na=False)]

        if not df.empty:
            for i,row in df.iterrows():
                with st.expander(row["Task"]):
                    st.write("Priority:", row["Priority"])
                    st.write("Due:", row["Due"])
                    if row["Star"] == 1:
                        st.write("⭐ Starred")
                    st.write("Notes:", row["Notes"])
                    if st.button("Delete", key=row["ID"]):
                        c.execute("DELETE FROM tasks WHERE id=?", (row["ID"],))
                        conn.commit()
                        st.rerun()
        else:
            st.info("No tasks found")

    if page == "Calendar":
        st.title("📅 Calendar")
        selected = st.date_input("Select Date")
        c.execute("SELECT * FROM tasks WHERE user=?", (st.session_state.user,))
        data = c.fetchall()
        df = pd.DataFrame(data, columns=["ID","User","Task","Priority","Due","Star","Notes"])
        today_tasks = df[df["Due"] == str(selected)]
        st.dataframe(today_tasks)

    if page == "About":
        st.title("About CramNow")

        st.header("What the App Does")
        st.write("""
CramNow is a task management system designed for students who need to organize 
their assignments, projects, and study sessions efficiently, especially for last-minute 
studying (cramming). It helps users track tasks, set priorities, monitor due dates, 
and highlight urgent or starred tasks, making sure they stay on top of deadlines.
        """)

        st.header("Target Users")
        st.write("""
The main users are high school and college students who often need to study 
for exams at the last minute or manage multiple assignments. 
CramNow helps them stay organized and focused, even under tight schedules.
        """)

        st.header("Inputs Collected")
        st.write("""
• Username and Password (for login and profile)  
• Profile Picture (for personalization)  
• Task Name  
• Priority Level (Low, Medium, High)  
• Due Date  
• Starred Status (⭐ for important tasks)  
• Notes for additional information  
• Optional reminder time before the task is due
        """)

        st.header("Outputs Displayed")
        st.write("""
• Dashboard overview with total tasks, high priority tasks, and starred tasks  
• Notifications for tasks due within 24 hours  
• Task List with search and filters  
• Calendar view showing tasks by date  
• Detailed task information including notes and priority  
• Visual indicators for urgent or important tasks
        """)

    if page == "Help & Resources":
        st.title("🆘 Help & Resources")
        st.header("How to Use CramNow")
        st.write("""
1. Sign Up to create an account and upload your profile picture.
2. Login using your username and password.
3. Add Task to create new tasks, set priority, due date, notes, and optionally star important tasks.
4. Task List lets you view all tasks, filter by starred/high priority, and search tasks by name.
5. Calendar shows tasks due on a specific date.
6. Dashboard gives an overview of your tasks and notifications.
7. Logout when done to secure your account.
        """)
        st.header("Tips for Managing Tasks")
        st.write("""
• Use High Priority for urgent tasks.  
• Star tasks ⭐ that you don’t want to miss.  
• Set reminders if you need alerts before due dates.  
• Regularly check your calendar to stay on top of deadlines.
        """)
        st.header("Additional Resources")
        st.write("""
• [Streamlit Documentation](https://docs.streamlit.io)  
• [Productivity Tips for Students](https://www.lifehack.org/articles/productivity/25-tips-for-students.html)  
• [Task Management Strategies](https://todoist.com/productivity-methods)
        """)