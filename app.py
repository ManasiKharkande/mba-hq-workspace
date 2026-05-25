import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import json
import os
import gspread
from google.oauth2.service_account import Credentials

# 1. Setup Master AI Keys
if "GEMINI_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GEMINI_KEY"]
else:
    GOOGLE_API_KEY = "YOUR_FALLBACK_KEY"

genai.configure(api_key=GOOGLE_API_KEY)

# 2. Page Configuration
st.set_page_config(
    page_title="MBA HQ Workspace",
    page_icon="⚡",
    layout="wide"
)

# 3. Securely Connect to Your Google Sheet Database via Raw Gspread Client
SHEET_URL = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet", "")
if not SHEET_URL:
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1516BWshyUPZlhQ1Oz4Epum3PQAp7hin81_eP3eERO0Q/edit?usp=sharing"

@st.cache_resource
def get_gc_client():
    if os.path.exists("google_creds.json"):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file("google_creds.json", scopes=scopes)
        return gspread.authorize(creds)
    return None

gc = get_gc_client()

# --- BULLETPROOF DATA WRITE HELPERS ---
def get_sheet_data(worksheet_name, fallback_cols):
    try:
        if gc:
            sh = gc.open_by_url(SHEET_URL)
            worksheet = sh.worksheet(worksheet_name)
            records = worksheet.get_all_records()
            if not records:
                return pd.DataFrame(columns=fallback_cols)
            return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Error reading {worksheet_name}: {e}")
    return pd.DataFrame(columns=fallback_cols)

def save_sheet_data(worksheet_name, df):
    try:
        if gc:
            sh = gc.open_by_url(SHEET_URL)
            worksheet = sh.worksheet(worksheet_name)
            worksheet.clear()
            # Convert dataframe to nested lists including headers
            data_to_write = [df.columns.values.tolist()] + df.fillna("").astype(str).values.tolist()
            worksheet.update(data_to_write)
            return True
    except Exception as e:
        st.error(f"Database Write Error on {worksheet_name}: {e}")
    return False

# ==========================================
# 4. SIGN-IN & REGISTRATION SYSTEM
# ==========================================
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if st.session_state.logged_in_user is None:
    st.title("⚡ Welcome to MBA HQ Workspace")
    st.write("A cloud-synced, AI-assisted central dashboard for your tasks and notes.")
    st.markdown("---")
    
    col_login, col_info = st.columns([1, 1.2])
    
    with col_login:
        st.subheader("🔑 Account Authentication")
        input_user = st.text_input("Username / Email:", placeholder="Enter your name or email").strip().lower()
        input_pass = st.text_input("Password:", type="password", placeholder="Enter your password")
        
        if input_user and input_pass:
            users_df = get_sheet_data("Users", ["username", "password"])
            
            if not users_df.empty and "username" in users_df.columns:
                user_exists = input_user in users_df["username"].astype(str).values
            else:
                user_exists = False
            
            if user_exists:
                correct_pass = str(users_df[users_df["username"].astype(str) == input_user]["password"].values[0])
                if input_pass == correct_pass:
                    if st.button("🔓 Log In", type="primary", use_container_width=True):
                        st.session_state.logged_in_user = input_user
                        st.rerun()
                else:
                    st.error("❌ Incorrect password. Please try again.")
            else:
                st.info("ℹ️ This username doesn't exist yet. Would you like to register it?")
                if st.button("✨ Register New Account", type="primary", use_container_width=True):
                    new_user_row = pd.DataFrame([{"username": input_user, "password": input_pass}])
                    updated_users = pd.concat([users_df, new_user_row], ignore_index=True)
                    if save_sheet_data("Users", updated_users):
                        st.success("🎉 Registration successful! Click 'Log In' above to access your space.")
                        st.rerun()
                    
    with col_info:
        st.info("""
        ### 🚀 Features Included:
        * **Permanent Device Cloud Sync:** Add items on your laptop, look at them on your mobile phone instantly.
        * **Personalized Dashboard:** Your workspace items are kept completely secure and isolated from other users.
        * **AI Fast Parsing Engine:** Instantly convert disorganized schedule text into structured action-items.
        """)
    st.stop()

# ==========================================
# 5. AUTHENTICATED SINGLE-USER RUN ENVIRONMENT
# ==========================================
current_user = st.session_state.logged_in_user

all_tasks = get_sheet_data("Tasks", ["username", "title", "priority", "status"])
if not all_tasks.empty and "username" in all_tasks.columns:
    user_tasks = all_tasks[all_tasks["username"] == current_user].to_dict('records')
else:
    user_tasks = []

all_notes = get_sheet_data("Notes", ["username", "page", "time", "content", "color"])
if not all_notes.empty and "username" in all_notes.columns:
    user_notes = all_notes[all_notes["username"] == current_user].to_dict('records')
else:
    user_notes = []

user_pages = ["📬 Master Feed & Scheduler"]
for note in user_notes:
    if note.get("page") and note["page"] not in user_pages:
        user_pages.append(note["page"])

with st.sidebar:
    st.header("⚡ MBA HQ")
    st.caption(f"👤 Logged in as: **{current_user}**")
    
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()
        
    st.markdown("---")
    all_available_pages = user_pages + ["📋 Project Board Tracker"]
    page = st.radio("Go to App/Workspace Page:", all_available_pages)
    
    st.markdown("---")
    st.subheader("🛠️ Workspace Engine")
    
    with st.form("page_creator_form", clear_on_submit=True):
        new_page_name = st.text_input("New Page Name:", placeholder="e.g., Loan Tracker, Placement Prep")
        submit_create = st.form_submit_button("➕ Create Page", use_container_width=True)
        
        if submit_create and new_page_name:
            clean_name = f"📄 {new_page_name.strip()}"
            if clean_name not in user_pages:
                new_note_row = pd.DataFrame([{
                    "username": current_user, "page": clean_name, "time": datetime.now().strftime("%b %d, %I:%M %p"),
                    "content": "🚀 Welcome to your new dynamic page canvas!", "color": "🔵 Blue"
                }])
                updated_notes = pd.concat([all_notes, new_note_row], ignore_index=True)
                save_sheet_data("Notes", updated_notes)
                st.rerun()

    st.markdown("---")
    st.subheader("🔋 Energy Level")
    energy_score = st.slider("Set your current study vibe:", 1, 3, 2, format="", help="1=Exhausted, 2=Steady Focus, 3=High Energy")
    vibe_mapping = {1: "☕ Chill/Bite-sized", 2: "💼 Professional/Direct", 3: "🔥 Elite/Ultra-Productive"}
    st.caption(f"Current Vibe Mode: **{vibe_mapping[energy_score]}**")

# ==========================================
# 6. DYNAMIC WORKSPACE NOTEBOOK PAGES
# ==========================================
if page in user_pages:
    st.title(f"{page}")
    
    todo_count = sum(1 for t in user_tasks if t.get("status") == "📋 To Do")
    high_priority_todo = sum(1 for t in user_tasks if t.get("status") == "📋 To Do" and t.get("priority") == "🔴 High")
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("📂 Custom Workspace Pages", f"{len(user_pages)} Modules")
    metric_col2.metric("🎯 Tasks in To-Do", f"{todo_count} Deliverables")
    metric_col3.metric("📝 Saved Notebook Items", f"{len(user_notes)} Notes/Logs")
    
    if high_priority_todo > 0:
        st.error(f"⚠️ **Urgent Action Required:** You have **{high_priority_todo} High Priority** task(s) languishing in your Project Board!")
    else:
        st.success("🎉 **Schedule Cleared:** No high-priority items are currently blocked.")
        
    st.markdown("---")
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("📥 Log New Information")
        log_type = st.selectbox("What format is this?", ["📝 Quick Class Note", "📆 Chaotic Schedule/Announcement"], key=f"log_type_{page}")
        
        color_choice = "🔵 Blue"
        if log_type == "📝 Quick Class Note":
            color_choice = st.selectbox("Choose Note Highlight Color:", ["🔵 Blue", "🟢 Emerald", "🟡 Amber", "🔴 Crimson"], key=f"color_{page}")
        
        with st.form(key=f"input_form_{page}", clear_on_submit=True):
            raw_text = st.text_area(label="Input Content Box", placeholder="Type or paste information here...", height=150, label_visibility="collapsed")
            save_button = st.form_submit_button("🚀 Push to Page Database", type="primary")
        
        if save_button and raw_text:
            if log_type == "📆 Chaotic Schedule/Announcement":
                with st.spinner("AI Agent is parsing..."):
                    try:
                        prompt = f"""
                        You are an expert executive academic coordinator. Analyze the text below and extract the core details.
                        Adopt a tone that matches this vibe: '{vibe_mapping[energy_score]}'.
                        Provide your response strictly in exactly two clean markdown lines:
                        Line 1: Start with an emoji. Bold title of the event or item, followed by any date/time.
                        Line 2: A short bullet point specifying the venue/location or any immediate action items.
                        Text: "{raw_text}"
                        """
                        model = genai.GenerativeModel('gemini-3.5-flash')
                        response = model.generate_content(prompt)
                        
                        new_note_row = pd.DataFrame([{
                            "username": current_user, "page": page, "time": datetime.now().strftime("%I:%M %p"),
                            "content": response.text, "color": "🔵 Blue"
                        }])
                        updated_notes = pd.concat([all_notes, new_note_row], ignore_index=True)
                        save_sheet_data("Notes", updated_notes)
                        st.toast("AI Parsed and Synced!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            elif log_type == "📝 Quick Class Note":
                new_note_row = pd.DataFrame([{
                    "username": current_user, "page": page, "time": datetime.now().strftime("%b %d, %I:%M %p"),
                    "content": raw_text, "color": color_choice
                }])
                updated_notes = pd.concat([all_notes, new_note_row], ignore_index=True)
                save_sheet_data("Notes", updated_notes)
                st.toast("Note secured to Cloud Google Sheet!")
                st.rerun()

    with col2:
        st.subheader("📚 Saved Notebook & Timeline Logs")
        current_page_notes = [n for n in user_notes if n.get("page") == page]
        
        if not current_page_notes:
            st.info("Your notebook is blank for this section.")
        else:
            color_map = {"🔵 Blue": "info", "🟢 Emerald": "success", "🟡 Amber": "warning", "🔴 Crimson": "error"}
            for idx, note in enumerate(reversed(current_page_notes)):
                chosen_banner = color_map.get(note.get('color', '🔵 Blue'), 'info')
                
                with st.container():
                    if chosen_banner == "success": st.success(f"🕒 **{note['time']}**\n\n{note['content']}")
                    elif chosen_banner == "warning": st.warning(f"🕒 **{note['time']}**\n\n{note['content']}")
                    elif chosen_banner == "error": st.error(f"🕒 **{note['time']}**\n\n{note['content']}")
                    else: st.info(f"🕒 **{note['time']}**\n\n{note['content']}")
                    
                    if st.button("🗑️ Delete Item", key=f"del_note_{page}_{idx}"):
                        actual_idx = all_notes[(all_notes["username"] == current_user) & (all_notes["page"] == page) & (all_notes["content"] == note["content"])].index[-1]
                        all_notes = all_notes.drop(actual_idx)
                        save_sheet_data("Notes", all_notes)
                        st.rerun()
                    st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 7. INTERACTIVE CLOUD PROJECT BOARD
# ==========================================
elif page == "📋 Project Board Tracker":
    st.title("📋 Cloud Sync Project & Case Study Board")
    st.write("Track deliverables by dragging status dropdowns. Changes persist instantly across devices!")
    st.markdown("---")
    
    with st.expander("➕ Create New Project Task / Deadline"):
        with st.form(key="new_task_form", clear_on_submit=True):
            new_task_title = st.text_input("Task/Case Study Title:")
            new_task_priority = st.selectbox("Priority Level:", ["🔴 High", "🟡 Medium", "🟢 Low"])
            submit_task = st.form_submit_button("Add Task to Board", type="primary")
            
            if submit_task and new_task_title:
                new_task_row = pd.DataFrame([{
                    "username": current_user, "title": new_task_title,
                    "priority": new_task_priority, "status": "📋 To Do"
                }])
                updated_tasks = pd.concat([all_tasks, new_task_row], ignore_index=True)
                save_sheet_data("Tasks", updated_tasks)
                st.rerun()
    
    st.markdown("### 🗺️ Project Board Columns")
    b_col1, b_col2, b_col3 = st.columns(3)
    
    def render_board_column(column_title, target_status, layout_column):
        global all_tasks
        with layout_column:
            st.markdown(f"### {column_title}")
            for idx, task in enumerate(user_tasks):
                if task.get("status") == target_status:
                    with st.container():
                        st.markdown(f"**{task['title']}**")
                        st.caption(f"Priority: {task['priority']}")
                        
                        avail_statuses = ["📋 To Do", "⚡ In Progress", "✅ Done"]
                        curr_idx = avail_statuses.index(target_status)
                        new_status = st.selectbox("Move status:", avail_statuses, key=f"status_{target_status}_{idx}", index=curr_idx)
                        
                        if new_status != task["status"]:
                            master_idx = all_tasks[(all_tasks["username"] == current_user) & (all_tasks["title"] == task["title"])].index[-1]
                            all_tasks.at[master_idx, "status"] = new_status
                            save_sheet_data("Tasks", all_tasks)
                            st.rerun()
                        
                        if st.button("🗑️ Drop Task", key=f"drop_{target_status}_{idx}", use_container_width=True):
                            master_idx = all_tasks[(all_tasks["username"] == current_user) & (all_tasks["title"] == task["title"])].index[-1]
                            all_tasks = all_tasks.drop(master_idx)
                            save_sheet_data("Tasks", all_tasks)
                            st.rerun()
                        st.markdown("---")

    render_board_column("🔴 TO DO", "📋 To Do", b_col1)
    render_board_column("🟡 IN PROGRESS", "⚡ In Progress", b_col2)
    render_board_column("🟢 DONE", "✅ Done", b_col3)
