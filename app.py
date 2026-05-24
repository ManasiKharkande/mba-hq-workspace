import streamlit as st
import google.generativeai as genai
from datetime import datetime

# 1. Setup Master Keys & Security Passwords
MASTER_PASSWORD = "HUSTLE"  # 👈 Set whatever shared password you want here!

if "GEMINI_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GEMINI_KEY"]
else:
    GOOGLE_API_KEY = "YOUR_SECRET_GEMINI_KEY_HERE"  # Keep your key here for local testing

genai.configure(api_key=GOOGLE_API_KEY)

# 2. Page Configuration
st.set_page_config(
    page_title="MBA HQ Workspace",
    page_icon="⚡",
    layout="wide"
)

# 3. Initialize Databases
if "custom_pages" not in st.session_state:
    st.session_state.custom_pages = ["📬 Master Feed & Scheduler"]
if "page_logs" not in st.session_state:
    st.session_state.page_logs = {"📬 Master Feed & Scheduler": []}
if "page_notes" not in st.session_state:
    st.session_state.page_notes = {"📬 Master Feed & Scheduler": []}

if "project_tasks" not in st.session_state or len(st.session_state.project_tasks) == 0:
    if "project_tasks" not in st.session_state:
        st.session_state.project_tasks = [
            {"title": "Corporate Finance Case Study Analysis", "priority": "🔴 High", "status": "📋 To Do"},
            {"title": "Marketing Strategy Team Presentation", "priority": "🟡 Medium", "status": "⚡ In Progress"},
            {"title": "Operations Management Framework Review", "priority": "🟢 Low", "status": "✅ Done"}
        ]

def create_ics_file(summary, description="Parsed by MBA Copilot"):
    current_year = datetime.now().year
    ics_string = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MBA HQ Copilot//Config 1.0//EN
BEGIN:VEVENT
SUMMARY:{summary}
DESCRIPTION:{description}
DTSTART:{current_year}0901T100000Z
DTEND:{current_year}0901T110000Z
END:VEVENT
END:VCALENDAR"""
    return ics_string

# ==========================================
# 4. SIDEBAR MENU & GATEKEEPER
# ==========================================
with st.sidebar:
    st.header("⚡ MBA HQ")
    st.caption("Your central schedule alignment & note command.")
    st.markdown("---")
    
    # Password Gate Input Box
    user_password = st.text_input("🔑 Enter Access Password:", type="password", placeholder="Ask admin for access")
    
    if user_password != MASTER_PASSWORD:
        st.warning("Please enter the correct workspace password in the box above to unlock your pages.")
        st.markdown("---")
        st.info("🔒 Secured via Group Workspace Protocol.")
        # Stops the script right here so unauthorized users see absolutely nothing below this
        st.stop()
        
    st.success("🔓 Access Granted!")
    st.markdown("---")
    
    # Navigation Selector (Only shows up if password matches!)
    all_available_pages = st.session_state.custom_pages + ["📋 Project Board Tracker"]
    page = st.radio("Go to App/Workspace Page:", all_available_pages)
    
    st.markdown("---")
    st.subheader("🛠️ Workspace Engine")
    
    with st.form("page_creator_form", clear_on_submit=True):
        new_page_name = st.text_input("New Page Name:", placeholder="e.g., Loan Tracker, Placement Prep")
        submit_create = st.form_submit_button("➕ Create Page", use_container_width=True)
        
        if submit_create and new_page_name:
            clean_name = f"📄 {new_page_name.strip()}"
            if clean_name not in st.session_state.custom_pages:
                st.session_state.custom_pages.append(clean_name)
                st.session_state.page_logs[clean_name] = []
                st.session_state.page_notes[clean_name] = []
                st.rerun()

    st.markdown("---")
    st.subheader("🔋 Energy Level")
    energy_score = st.slider("Set your current study vibe:", 1, 3, 2, format="", help="1=Exhausted, 2=Steady Focus, 3=High Energy")
    vibe_mapping = {1: "☕ Chill/Bite-sized", 2: "💼 Professional/Direct", 3: "🔥 Elite/Ultra-Productive"}
    st.caption(f"Current Vibe Mode: **{vibe_mapping[energy_score]}**")

# ==========================================
# DYNAMIC WORKSPACE PAGES
# ==========================================
if page in st.session_state.custom_pages:
    st.title(f"{page}")
    
    total_parsed = sum(len(logs) for logs in st.session_state.page_logs.values())
    todo_count = sum(1 for t in st.session_state.project_tasks if t["status"] == "📋 To Do")
    high_priority_todo = sum(1 for t in st.session_state.project_tasks if t["status"] == "📋 To Do" and t["priority"] == "🔴 High")
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("📂 Tracked Workspace Modules", f"{len(st.session_state.custom_pages)} Pages")
    metric_col2.metric("🎯 Active Tasks Pending", f"{todo_count} Deliverables")
    metric_col3.metric("🧠 Total AI-Parsed Announcements", f"{total_parsed} Logs")
    
    if high_priority_todo > 0:
        st.error(f"⚠️ **Urgent Action Required:** You have **{high_priority_todo} High Priority** task(s) languishing in your Project Board!")
    else:
        st.success("🎉 **Schedule Cleared:** No high-priority items are currently blocked.")
        
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("📥 Log New Information")
        log_type = st.selectbox("What format is this?", ["📆 Chaotic Schedule/Announcement", "📝 Quick Class Note"], key=f"log_type_{page}")
        
        color_choice = "🔵 Blue"
        if log_type == "📝 Quick Class Note":
            color_choice = st.selectbox("Choose Note Highlight Color:", ["🔵 Blue", "🟢 Emerald", "🟡 Amber", "🔴 Crimson"], key=f"color_{page}")
            st.caption("💡 **Formatting Tips:** Use `# Your Heading` for headings, or `* Item` for bullet points.")
        
        with st.form(key=f"input_form_{page}", clear_on_submit=True):
            raw_text = st.text_area(label="Input Content Box", placeholder="Paste updates or type formatting notes here...", height=150, label_visibility="collapsed")
            save_button = st.form_submit_button("🚀 Push to Page Database", type="primary")
        
        if save_button and raw_text:
            if log_type == "📆 Chaotic Schedule/Announcement":
                with st.spinner("AI Agent is adjusting parameters and parsing..."):
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
                        
                        new_entry = {
                            "time": datetime.now().strftime("%I:%M %p"),
                            "title": response.text.split('\n')[0].replace('**', '').strip(),
                            "content": response.text
                        }
                        st.session_state.page_logs[page].insert(0, new_entry)
                        st.toast("Parsed successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            elif log_type == "📝 Quick Class Note":
                new_note = {
                    "time": datetime.now().strftime("%b %d, %I:%M %p"),
                    "content": raw_text,
                    "color": color_choice
                }
                st.session_state.page_notes[page].insert(0, new_note)
                st.toast("Note securely added!")
                st.rerun()

    with col2:
        dash_tab1, dash_tab2 = st.tabs(["📅 Aligned Feed Tracker", "📋 Notebook Dashboard"])
        
        with dash_tab1:
            st.subheader("⏱️ Real-Time Structured Activity Feed")
            if not st.session_state.page_logs[page]:
                st.info("No timeline events parsed on this page yet.")
            else:
                for idx, item in enumerate(st.session_state.page_logs[page]):
                    with st.container():
                        st.caption(f"Logged at {item['time']}")
                        st.markdown(item['content'])
                        
                        sub1, sub2, sub3 = st.columns([1.5, 1, 1])
                        with sub1:
                            ics_data = create_ics_file(item['title'])
                            st.download_button("📅 Calendar Link", data=ics_data, file_name="event.ics", mime="text/calendar", key=f"dl_{page}_{idx}")
                        with sub2:
                            with st.expander("✏️ Edit"):
                                edited_content = st.text_area("Modify Content:", value=item['content'], key=f"edit_feed_txt_{page}_{idx}")
                                if st.button("Save", key=f"save_feed_edit_{page}_{idx}"):
                                    st.session_state.page_logs[page][idx]['content'] = edited_content
                                    st.rerun()
                        with sub3:
                            if st.button("🗑️ Wipe", key=f"del_feed_{page}_{idx}"):
                                st.session_state.page_logs[page].pop(idx)
                                st.rerun()
                        st.markdown("---")
                        
        with dash_tab2:
            st.subheader("📚 Saved Notebook Logs")
            if not st.session_state.page_notes[page]:
                st.info("Your notebook is blank for this section.")
            else:
                color_map = {"🔵 Blue": "info", "🟢 Emerald": "success", "🟡 Amber": "warning", "🔴 Crimson": "error"}
                for idx, note in enumerate(st.session_state.page_notes[page]):
                    chosen_banner = color_map.get(note.get('color', '🔵 Blue'), 'info')
                    
                    with st.container():
                        if chosen_banner == "success": st.success(f"🕒 **{note['time']}**\n\n{note['content']}")
                        elif chosen_banner == "warning": st.warning(f"🕒 **{note['time']}**\n\n{note['content']}")
                        elif chosen_banner == "error": st.error(f"🕒 **{note['time']}**\n\n{note['content']}")
                        else: st.info(f"🕒 **{note['time']}**\n\n{note['content']}")
                        
                        edit_col, del_col = st.columns([1, 1])
                        with edit_col:
                            with st.expander("✏️ Edit Note"):
                                edited_note_txt = st.text_area("Edit Text:", value=note['content'], key=f"edit_note_txt_{page}_{idx}")
                                if st.button("Save Changes", key=f"save_note_edit_{page}_{idx}"):
                                    st.session_state.page_notes[page][idx]['content'] = edited_note_txt
                                    st.rerun()
                        with del_col:
                            if st.button("🗑️ Delete Note", key=f"del_note_{page}_{idx}"):
                                st.session_state.page_notes[page].pop(idx)
                                st.rerun()
                        st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# PAGE 2: INTERACTIVE PROJECT BOARD
# ==========================================
elif page == "📋 Project Board Tracker":
    st.title("📋 Project & Case Study Board")
    st.write("Track your heavy deliverables by dragging status dropdowns.")
    st.markdown("---")
    
    with st.expander("➕ Create New Project Task / Deadline"):
        with st.form(key="new_task_form", clear_on_submit=True):
            new_task_title = st.text_input("Task/Case Study Title:")
            new_task_priority = st.selectbox("Priority Level:", ["🔴 High", "🟡 Medium", "🟢 Low"])
            submit_task = st.form_submit_button("Add Task to Board", type="primary")
            
            if submit_task and new_task_title:
                st.session_state.project_tasks.append({
                    "title": new_task_title,
                    "priority": new_task_priority,
                    "status": "📋 To Do"
                })
                st.rerun()
    
    st.markdown("### 🗺️ Project Board Columns")
    b_col1, b_col2, b_col3 = st.columns(3)
    
    def render_board_column(column_title, target_status, layout_column, border_color):
        with layout_column:
            st.markdown(f"### {column_title}")
            for idx, task in enumerate(st.session_state.project_tasks):
                if task["status"] == target_status:
                    with st.container():
                        st.markdown(f"**{task['title']}**")
                        st.caption(f"Priority: {task['priority']}")
                        
                        avail_statuses = ["📋 To Do", "⚡ In Progress", "✅ Done"]
                        curr_idx = avail_statuses.index(target_status)
                        new_status = st.selectbox("Move status:", avail_statuses, key=f"status_{target_status}_{idx}", index=curr_idx)
                        if new_status != task["status"]:
                            task["status"] = new_status
                            st.rerun()
                        
                        task_edit, task_del = st.columns(2)
                        with task_edit:
                            with st.expander("✏️ Rename"):
                                updated_title = st.text_input("Change title:", value=task['title'], key=f"ren_{target_status}_{idx}")
                                if st.button("Apply", key=f"btn_ren_{target_status}_{idx}"):
                                    task['title'] = updated_title
                                    st.rerun()
                        with task_del:
                            if st.button("🗑️ Drop", key=f"drop_{target_status}_{idx}", use_container_width=True):
                                st.session_state.project_tasks.pop(idx)
                                st.rerun()
                        st.markdown("---")

    render_board_column("🔴 TO DO", "📋 To Do", b_col1, "red")
    render_board_column("🟡 IN PROGRESS", "⚡ In Progress", b_col2, "orange")
    render_board_column("🟢 DONE", "✅ Done", b_col3, "green")
