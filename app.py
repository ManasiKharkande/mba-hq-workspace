import streamlit as st
import google.generativeai as genai
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="MBA HQ Workspace",
    page_icon="⚡",
    layout="wide"
)

# ==========================================
# 2. SETUP GEMINI AI KEY SECURELY
# ==========================================
if "GEMINI_KEY" in st.secrets and st.secrets["GEMINI_KEY"]:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    ai_enabled = True
else:
    ai_enabled = False
    st.warning("⚠️ `GEMINI_KEY` not detected in Secrets. AI features will be disabled until configured.")

# ==========================================
# 3. AUTOMATIC SQLITE DATABASE ENGINE
# ==========================================
DB_FILE = "workspace.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Automatically creates database and tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page TEXT NOT NULL,
            time TEXT NOT NULL,
            content TEXT NOT NULL,
            color TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# --- DATABASE HELPER FUNCTIONS ---
def load_notes():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM notes", conn)
    conn.close()
    return df

def load_tasks():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM tasks", conn)
    conn.close()
    return df

def add_note(page, time_str, content, color):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (page, time, content, color) VALUES (?, ?, ?, ?)",
                   (page, time_str, content, color))
    conn.commit()
    conn.close()

def delete_note(note_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

def add_task(title, priority, status="📋 To Do"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, priority, status) VALUES (?, ?, ?)",
                   (title, priority, status))
    conn.commit()
    conn.close()

def update_task_status(task_id, new_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# ==========================================
# 4. LOAD WORKSPACE DATA
# ==========================================
df_notes = load_notes()
df_tasks = load_tasks()

user_notes = df_notes.to_dict('records') if not df_notes.empty else []
user_tasks = df_tasks.to_dict('records') if not df_tasks.empty else []

if "workspace_pages" not in st.session_state:
    st.session_state.workspace_pages = ["📬 Master Feed & Scheduler"]

for note in user_notes:
    page_val = str(note.get("page", "")).strip()
    if page_val and page_val not in st.session_state.workspace_pages:
        st.session_state.workspace_pages.append(page_val)

if "current_page" not in st.session_state or st.session_state.current_page not in (st.session_state.workspace_pages + ["📋 Project Board Tracker"]):
    st.session_state.current_page = st.session_state.workspace_pages[0]

# ==========================================
# 5. SIDEBAR NAVIGATION & PAGE CREATOR
# ==========================================
with st.sidebar:
    st.header("⚡ MBA HQ")
    st.caption("🚀 Database Engine Active")
    st.markdown("---")
    
    all_nav_options = st.session_state.workspace_pages + ["📋 Project Board Tracker"]
    
    selected_nav = st.radio(
        "Go to App/Workspace Page:", 
        all_nav_options, 
        index=all_nav_options.index(st.session_state.current_page) if st.session_state.current_page in all_nav_options else 0,
        key="nav_radio"
    )
    st.session_state.current_page = selected_nav
    page = st.session_state.current_page

    st.markdown("---")
    st.subheader("🛠️ Workspace Engine")
    
    with st.form("page_creator_form", clear_on_submit=True):
        new_page_name = st.text_input("New Page Name:", placeholder="e.g., Placement Prep")
        submit_create = st.form_submit_button("➕ Create Page", use_container_width=True)
        
        if submit_create:
            if new_page_name.strip():
                clean_name = f"📄 {new_page_name.strip()}"
                
                if clean_name not in st.session_state.workspace_pages:
                    st.session_state.workspace_pages.append(clean_name)
                    st.session_state.current_page = clean_name
                    
                    add_note(
                        page=clean_name,
                        time_str=datetime.now().strftime("%b %d, %I:%M %p"),
                        content="🚀 Welcome to your new dynamic page canvas!",
                        color="🔵 Blue"
                    )
                    st.toast(f"Page '{clean_name}' created!")
                    st.rerun()
                else:
                    st.warning("That page name already exists.")
            else:
                st.warning("Please enter a valid page name.")

    st.markdown("---")
    st.subheader("🔋 Energy Level")
    energy_score = st.slider("Set your current study vibe:", 1, 3, 2, format="", help="1=Exhausted, 2=Steady Focus, 3=High Energy")
    vibe_mapping = {1: "☕ Chill/Bite-sized", 2: "💼 Professional/Direct", 3: "🔥 Elite/Ultra-Productive"}
    st.caption(f"Current Vibe Mode: **{vibe_mapping[energy_score]}**")

# ==========================================
# 6. DYNAMIC WORKSPACE NOTEBOOK PAGES
# ==========================================
if page in st.session_state.workspace_pages:
    st.title(f"{page}")
    
    todo_count = sum(1 for t in user_tasks if t.get("status") == "📋 To Do")
    high_priority_todo = sum(1 for t in user_tasks if t.get("status") == "📋 To Do" and t.get("priority") == "🔴 High")
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("📂 Custom Workspace Pages", f"{len(st.session_state.workspace_pages)} Modules")
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
            save_button = st.form_submit_button("🚀 Push to Database", type="primary")
        
        if save_button and raw_text:
            if log_type == "📆 Chaotic Schedule/Announcement":
                if not ai_enabled:
                    st.error("AI service is unconfigured. Set `GEMINI_KEY` in secrets.")
                else:
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
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            response = model.generate_content(prompt)
                            
                            add_note(page, datetime.now().strftime("%I:%M %p"), response.text, "🔵 Blue")
                            st.toast("AI Parsed and Synced!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error parsing schedule: {e}")
            
            elif log_type == "📝 Quick Class Note":
                add_note(page, datetime.now().strftime("%b %d, %I:%M %p"), raw_text, color_choice)
                st.toast("Note secured to database!")
                st.rerun()

    with col2:
        st.subheader("📚 Saved Notebook & Timeline Logs")
        current_page_notes = [n for n in user_notes if str(n.get("page", "")).strip() == page]
        
        if not current_page_notes:
            st.info("Your notebook is blank for this section.")
        else:
            color_map = {"🔵 Blue": "info", "🟢 Emerald": "success", "🟡 Amber": "warning", "🔴 Crimson": "error"}
            for note in reversed(current_page_notes):
                chosen_banner = color_map.get(note.get('color', '🔵 Blue'), 'info')
                
                with st.container():
                    if chosen_banner == "success": st.success(f"🕒 **{note['time']}**\n\n{note['content']}")
                    elif chosen_banner == "warning": st.warning(f"🕒 **{note['time']}**\n\n{note['content']}")
                    elif chosen_banner == "error": st.error(f"🕒 **{note['time']}**\n\n{note['content']}")
                    else: st.info(f"🕒 **{note['time']}**\n\n{note['content']}")
                    
                    if st.button("🗑️ Delete Item", key=f"del_note_{note['id']}"):
                        delete_note(note['id'])
                        st.rerun()
                    st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 7. INTERACTIVE PROJECT BOARD TRACKER
# ==========================================
elif page == "📋 Project Board Tracker":
    st.title("📋 Database Sync Project & Case Study Board")
    st.write("Track deliverables by dragging status dropdowns. Changes persist instantly!")
    st.markdown("---")
    
    with st.expander("➕ Create New Project Task / Deadline"):
        with st.form(key="new_task_form", clear_on_submit=True):
            new_task_title = st.text_input("Task/Case Study Title:")
            new_task_priority = st.selectbox("Priority Level:", ["🔴 High", "🟡 Medium", "🟢 Low"])
            submit_task = st.form_submit_button("Add Task to Board", type="primary")
            
            if submit_task and new_task_title:
                add_task(new_task_title, new_task_priority, "📋 To Do")
                st.rerun()
    
    st.markdown("### 🗺️ Project Board Columns")
    b_col1, b_col2, b_col3 = st.columns(3)
    
    def render_board_column(column_title, target_status, layout_column):
        with layout_column:
            st.markdown(f"### {column_title}")
            for task in user_tasks:
                if task.get("status") == target_status:
                    with st.container():
                        st.markdown(f"**{task['title']}**")
                        st.caption(f"Priority: {task['priority']}")
                        
                        avail_statuses = ["📋 To Do", "⚡ In Progress", "✅ Done"]
                        curr_idx = avail_statuses.index(target_status) if target_status in avail_statuses else 0
                        new_status = st.selectbox("Move status:", avail_statuses, key=f"status_{task['id']}", index=curr_idx)
                        
                        if new_status != task["status"]:
                            update_task_status(task['id'], new_status)
                            st.rerun()
                        
                        if st.button("🗑️ Drop Task", key=f"drop_{task['id']}", use_container_width=True):
                            delete_task(task['id'])
                            st.rerun()
                        st.markdown("---")

    render_board_column("🔴 TO DO", "📋 To Do", b_col1)
    render_board_column("🟡 IN PROGRESS", "⚡ In Progress", b_col2)
    render_board_column("🟢 DONE", "✅ Done", b_col3)
