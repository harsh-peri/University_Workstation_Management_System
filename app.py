# app.py
import streamlit as st 
import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import date

# -------------------------
# Page config + CSS theme
# -------------------------
st.set_page_config(page_title="University Workstation Management",
                   page_icon="🏛️",
                   layout="wide")

st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #ffffff; }
    h1, h2, h3 { color: white !important; }
    .login-box { background: rgba(255,255,255,0.03); padding: 18px; border-radius: 12px; }
    .muted { color: #f0f0f0; opacity: 0.9; }
    .small-muted { color: #e6e6e6; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Session Initialization
# -------------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.logged_in = False
    st.session_state.db_conn = None
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.login_error = None
    st.session_state._last_action = 0

# -------------------------
# DB helpers
# -------------------------
def connect_with_credentials(username: str, password: str):
    """Connect to MySQL using provided credentials."""
    conn = mysql.connector.connect(
        host="localhost",
        database="university_workstation",
        user=username,
        password=password,
        auth_plugin='mysql_native_password'
    )
    return conn


def _show_db_error(e: Exception):
    """Show DB error detail for admins, generic for other roles."""
    if st.session_state.get("role") == "admin":
        st.error(f"DB error: {e}")
    else:
        st.error("Database operation failed (insufficient privileges or error).")


def execute_query(query, params=None, fetch=True):
    """Execute SQL using active connection stored in session_state."""
    conn = st.session_state.get("db_conn")
    if conn is None:
        st.error("No DB connection. Please login.")
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        if fetch:
            rows = cursor.fetchall()
            return rows
        conn.commit()
        return True
    except Error as e:
        _show_db_error(e)
        return None
    finally:
        if cursor:
            cursor.close()


def call_procedure(proc_name, params=None, fetch=True):
    """Call stored procedure; returns list of rows (if any) or True."""
    conn = st.session_state.get("db_conn")
    if conn is None:
        st.error("No DB connection. Please login.")
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.callproc(proc_name, params or [])
        results = []
        for res in cursor.stored_results():
            results.extend(res.fetchall())
        conn.commit()
        if fetch:
            return results
        return True
    except Error as e:
        _show_db_error(e)
        return None
    finally:
        if cursor:
            cursor.close()

# -------------------------
# Login UI
# -------------------------
def show_login():
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.header("🔐 Login to University Workstation System")
    st.write("Enter MySQL username & password to login. Example: admin / <admin password>")
    if not st.session_state.logged_in:
        username = st.text_input("MySQL Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login", key="login_button"):
            try:
                conn = connect_with_credentials(username, password)
                if conn.is_connected():
                    st.session_state.db_conn = conn
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = "admin" if username == "admin" else "user"
                    st.session_state.login_error = None
                    st.session_state._last_action += 1
                else:
                    st.session_state.login_error = "Invalid username or password"
                    st.error("❌ Invalid username or password")
            except Error:
                st.session_state.login_error = "Invalid username or password"
                st.error("❌ Invalid username or password")
    else:
        st.success(f"✅ Logged in as **{st.session_state.username}** ({st.session_state.role})")
    st.markdown("</div>", unsafe_allow_html=True)


def do_logout():
    try:
        if st.session_state.get("db_conn"):
            try:
                st.session_state.db_conn.close()
            except:
                pass
    except Exception:
        pass

    st.session_state.logged_in = False
    st.session_state.db_conn = None
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.login_error = None
    st.session_state._last_action += 1

# -------------------------
# Utility helpers
# -------------------------
def get_all_campuses():
    rows = execute_query("SELECT campus_id, campus_name FROM campus ORDER BY campus_name")
    return rows or []


def get_blocks_by_campus(campus_id):
    rows = execute_query("SELECT block_id, block_name FROM block WHERE campus_id=%s ORDER BY block_name", (campus_id,))
    return rows or []


def get_buildings_by_block(block_id):
    rows = execute_query("SELECT building_id, build_name FROM building WHERE block_id=%s ORDER BY build_name", (block_id,))
    return rows or []


def get_floors_by_building(building_id):
    rows = execute_query("SELECT floor_no, floor_name FROM floor WHERE building_id=%s ORDER BY floor_no", (building_id,))
    return rows or []


def get_floor_path(floor_no):
    """Call MySQL function get_floor_path(floor_no) and return the string or None."""
    res = execute_query("SELECT get_floor_path(%s) AS path", (floor_no,))
    if res and len(res) > 0:
        return res[0].get('path')
    return None


def get_room_path(room_no):
    res = execute_query("SELECT get_room_path(%s) AS path", (room_no,))
    if res and len(res) > 0:
        return res[0].get('path')
    return None


def get_department_map():
    res = execute_query("SELECT dept_id, dept_name FROM department ORDER BY dept_name")
    return {r['dept_name']: r['dept_id'] for r in res} if res else {}


def get_available_rooms():
    res = execute_query("SELECT room_no FROM room WHERE is_allotted=0 ORDER BY room_no")
    return [r['room_no'] for r in res] if res else []

# -------------------------
# Dashboard
# -------------------------
def get_statistics():
    stats = {"faculty": 0, "rooms": 0, "allocated": 0, "available": 0, "departments": 0, "campuses": 0}
    try:
        r = execute_query("SELECT COUNT(*) AS c FROM faculty")
        stats['faculty'] = r[0]['c'] if r else 0
    except:
        stats['faculty'] = 0
    try:
        r = execute_query("SELECT COUNT(*) AS c FROM room")
        stats['rooms'] = r[0]['c'] if r else 0
    except:
        stats['rooms'] = 0
    try:
        r = execute_query("SELECT COUNT(*) AS c FROM room WHERE is_allotted=1")
        stats['allocated'] = r[0]['c'] if r else 0
    except:
        stats['allocated'] = 0
    try:
        r = execute_query("SELECT COUNT(*) AS c FROM room WHERE is_allotted=0")
        stats['available'] = r[0]['c'] if r else 0
    except:
        stats['available'] = 0
    try:
        r = execute_query("SELECT COUNT(*) AS c FROM department")
        stats['departments'] = r[0]['c'] if r else 0
    except:
        stats['departments'] = 0
    try:
        r = execute_query("SELECT COUNT(*) AS c FROM campus")
        stats['campuses'] = r[0]['c'] if r else 0
    except:
        stats['campuses'] = 0
    return stats


def show_dashboard():
    st.header("📊 Dashboard Overview")
    stats = get_statistics()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Faculty", stats['faculty'])
    c2.metric("Total Rooms", stats['rooms'])
    c3.metric("Allocated", stats['allocated'])
    c4.metric("Available", stats['available'])
    c5.metric("Departments", stats['departments'])
    c6.metric("Campuses", stats['campuses'])

    st.markdown("---")
    st.subheader("📌 Recent Allocations")
    allocs = execute_query("""
        SELECT f.faculty_id, f.faculty_name, f.post, f.room_no, d.dept_name
        FROM faculty f LEFT JOIN department d ON f.dept_id=d.dept_id
        WHERE f.room_no IS NOT NULL
        ORDER BY f.faculty_id DESC
        LIMIT 10
    """)
    if allocs:
        df = pd.DataFrame(allocs)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recent allocations")

# -------------------------
# Faculty Management
# -------------------------
def show_faculty_management():
    if st.session_state.role != "admin":
        st.error("❌ Access Denied — Admin only")
        return

    st.header("👨‍🏫 Faculty Management")
    tab1, tab2 = st.tabs(["View Faculty", "Add Faculty"])

    with tab1:
        st.subheader("All Faculty Members")
        data = execute_query("""
            SELECT f.faculty_id, f.faculty_name, f.post, d.dept_name, f.contact, f.date_of_join, f.room_no
            FROM faculty f
            LEFT JOIN department d ON f.dept_id = d.dept_id
            ORDER BY f.faculty_id
        """)
        if not data:
            st.info("No faculty records found.")
        else:
            df = pd.DataFrame(data)
            dept_map = get_department_map()
            dept_options = ["All"] + list(dept_map.keys())
            colf1, colf2 = st.columns(2)
            with colf1:
                dept_filter = st.selectbox("Filter by Department", dept_options, index=0)
            with colf2:
                search_name = st.text_input("Search name", key="fac_search")

            filtered = df.copy()
            if dept_filter and dept_filter != "All":
                filtered = filtered[filtered['dept_name'] == dept_filter]
            if search_name:
                filtered = filtered[filtered['faculty_name'].str.contains(search_name, case=False, na=False)]

            st.markdown("**Faculty List**")
            for rec in filtered.to_dict(orient="records"):
                fid = rec['faculty_id']
                cols = st.columns([3, 2, 1, 1])
                with cols[0]:
                    st.markdown(f"**{rec['faculty_name']}**  \n{rec['post']}  \nDept: {rec['dept_name']}")
                with cols[1]:
                    st.write(f"Contact: {rec.get('contact','-')}")
                with cols[2]:
                    st.write(f"Room: {rec['room_no'] if rec['room_no'] else '—'}")
                with cols[3]:
                    if st.button("✏️ Edit", key=f"edit_{fid}"):
                        st.session_state[f"show_edit_{fid}"] = not st.session_state.get(f"show_edit_{fid}", False)
                        st.session_state._last_action += 1

                    if st.button("🗑️ Delete", key=f"del_{fid}"):
                        st.session_state[f"to_delete_{fid}"] = True
                        st.session_state._last_action += 1

                if st.session_state.get(f"show_edit_{fid}", False):
                    with st.expander(f"Edit {rec['faculty_name']} (ID {fid})", expanded=True):
                        fresh = execute_query("SELECT * FROM faculty WHERE faculty_id=%s", (fid,))
                        if not fresh:
                            st.error("Record not found")
                        else:
                            fresh = fresh[0]
                            with st.form(key=f"edit_form_{fid}"):
                                name = st.text_input("Name", value=fresh.get('faculty_name') or "", key=f"name_{fid}")
                                post = st.selectbox("Post", ["Professor", "Associate Professor", "Assistant Professor", "Lecturer"],
                                                    index=0, key=f"post_{fid}")
                                dept_map_local = get_department_map()
                                dept_list = ["Select Department"] + list(dept_map_local.keys())
                                current_dept_name = None
                                if fresh.get('dept_id'):
                                    inv = {v: k for k, v in dept_map_local.items()}
                                    current_dept_name = inv.get(fresh.get('dept_id'), None)
                                dept_choice = st.selectbox("Department", dept_list,
                                                           index=0 if not current_dept_name else dept_list.index(current_dept_name),
                                                           key=f"dept_{fid}")
                                contact = st.text_input("Contact", value=fresh.get('contact') or "", key=f"contact_{fid}")

                                available = get_available_rooms()
                                room_options = ["None"]
                                cur_room = fresh.get('room_no')
                                if cur_room:
                                    room_options.insert(0, str(cur_room))
                                room_options.extend([str(r) for r in available if str(r) not in room_options])
                                room_choice = st.selectbox("Room", room_options, index=0, key=f"room_{fid}")

                                if st.form_submit_button("Save Changes", key=f"save_{fid}"):
                                    if not name or dept_choice == "Select Department":
                                        st.error("Name and Department required")
                                    else:
                                        dept_id = dept_map_local.get(dept_choice)
                                        new_room = None if room_choice == "None" else int(room_choice)
                                        try:
                                            ok = execute_query("""UPDATE faculty
                                                                  SET faculty_name=%s, post=%s, contact=%s, dept_id=%s, room_no=%s
                                                                  WHERE faculty_id=%s""",
                                                               (name, post, contact, dept_id, new_room, fid),
                                                               fetch=False)
                                            if ok:
                                                old_room = fresh.get('room_no')
                                                if old_room and old_room != new_room:
                                                    execute_query("UPDATE room SET is_allotted=0 WHERE room_no=%s", (old_room,), fetch=False)
                                                if new_room:
                                                    execute_query("UPDATE room SET is_allotted=1 WHERE room_no=%s", (new_room,), fetch=False)
                                                st.success("✅ Faculty updated successfully")
                                                st.session_state[f"show_edit_{fid}"] = False
                                                st.session_state._last_action += 1
                                            else:
                                                st.error("Failed to update faculty")
                                        except Exception as e:
                                            _show_db_error(e)

                if st.session_state.get(f"to_delete_{fid}", False):
                    st.warning(f"Are you sure you want to delete **{rec['faculty_name']}** (ID {fid})? This cannot be undone.")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Confirm Delete", key=f"confirm_del_{fid}"):
                            try:
                                rec_room = execute_query("SELECT room_no FROM faculty WHERE faculty_id=%s", (fid,))
                                room_no = rec_room[0]['room_no'] if rec_room and rec_room[0].get('room_no') else None
                                ok = execute_query("DELETE FROM faculty WHERE faculty_id=%s", (fid,), fetch=False)
                                if ok:
                                    if room_no:
                                        execute_query("UPDATE room SET is_allotted=0 WHERE room_no=%s", (room_no,), fetch=False)
                                    st.success("✅ Faculty deleted")
                                    st.session_state.pop(f"to_delete_{fid}", None)
                                    st.session_state._last_action += 1
                                else:
                                    st.error("Failed to delete")
                            except Exception as e:
                                _show_db_error(e)
                    with c2:
                        if st.button("Cancel", key=f"cancel_del_{fid}"):
                            st.session_state.pop(f"to_delete_{fid}", None)
                            st.session_state._last_action += 1

    with tab2:
        st.subheader("Add New Faculty")
        with st.form("add_faculty_form"):
            name = st.text_input("Faculty Name *", key="add_name")
            post = st.selectbox("Post *", ["Professor", "Associate Professor", "Assistant Professor", "Lecturer"], key="add_post")
            dept_map = get_department_map()
            dept_list = ["Select Department"] + list(dept_map.keys())
            dept_choice = st.selectbox("Department *", dept_list, key="add_dept")
            contact = st.text_input("Contact (digits)", key="add_contact")
            join_date = st.date_input("Date of Join", value=date.today(), key="add_join")
            room_options = ["None"] + [str(r) for r in get_available_rooms()]
            room_choice = st.selectbox("Assign Room (Optional)", room_options, key="add_room")
            submitted = st.form_submit_button("Add Faculty")
            if submitted:
                if not name or dept_choice == "Select Department":
                    st.error("Please fill required fields")
                else:
                    dept_id = dept_map.get(dept_choice)
                    room_no = None if room_choice == "None" else int(room_choice)
                    try:
                        proc_result = call_procedure('add_faculty', [name, join_date, post, contact if contact else None, room_no, dept_id])
                        if proc_result is not None:
                            if room_no:
                                execute_query("UPDATE room SET is_allotted=1 WHERE room_no=%s", (room_no,), fetch=False)
                            st.success("✅ Faculty added successfully")
                            for k in ("add_name", "add_contact", "add_room", "add_dept"):
                                st.session_state.pop(k, None)
                            st.session_state._last_action += 1
                        else:
                            ok = execute_query("INSERT INTO faculty (faculty_name, date_of_join, post, contact, room_no, dept_id) VALUES (%s,%s,%s,%s,%s,%s)",
                                               (name, join_date, post, contact if contact else None, room_no, dept_id), fetch=False)
                            if ok:
                                if room_no:
                                    execute_query("UPDATE room SET is_allotted=1 WHERE room_no=%s", (room_no,), fetch=False)
                                st.success("✅ Faculty added successfully")
                                st.session_state._last_action += 1
                            else:
                                st.error("Failed to add faculty")
                    except Exception as e:
                        _show_db_error(e)

# -------------------------
# Room Management
# -------------------------
def show_room_management():
    if st.session_state.role != "admin":
        st.error("❌ Access Denied — Admin only")
        return

    st.header("🏢 Room Management")

    # ------------------------------
    # Display existing rooms
    # ------------------------------
    rooms = execute_query("""
        SELECT r.room_no, r.location, r.type, r.is_allotted,
               f.floor_name, b.build_name, bl.block_name, c.campus_name
        FROM room r
        LEFT JOIN floor f ON r.floor_no = f.floor_no
        LEFT JOIN building b ON r.building_id = b.building_id
        LEFT JOIN block bl ON r.block_id = bl.block_id
        LEFT JOIN campus c ON r.campus_id = c.campus_id
        ORDER BY r.room_no
    """)

    if rooms:
        df = pd.DataFrame(rooms)
        df['is_allotted'] = df['is_allotted'].apply(
            lambda x: '✅ Allocated' if x and (x != 0) else '🟢 Available'
        )
        df['path'] = df['room_no'].apply(lambda rn: get_room_path(rn) or "")
        st.dataframe(df, use_container_width=True)

        st.markdown("**Manage Rooms**")
        for rec in df.to_dict(orient="records"):
            rn = rec['room_no']
            cols = st.columns([3,1,1])
            with cols[0]:
                st.markdown(f"**Room {rn}** — {rec['type']} — {rec['location']}  \n{rec.get('campus_name') or ''} / {rec.get('block_name') or ''} / {rec.get('build_name') or ''} / {rec.get('floor_name') or ''}")
            with cols[1]:
                if st.button("✏️ Edit", key=f"edit_room_{rn}"):
                    st.session_state[f"show_edit_room_{rn}"] = not st.session_state.get(f"show_edit_room_{rn}", False)
                    st.session_state._last_action += 1
            with cols[2]:
                if st.button("🗑️ Delete", key=f"del_room_{rn}"):
                    st.session_state[f"confirm_del_room_{rn}"] = True
                    st.session_state._last_action += 1

            # Confirm delete UI
            if st.session_state.get(f"confirm_del_room_{rn}", False):
                st.warning(f"Are you sure you want to delete Room **{rn}**? This cannot be undone.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Confirm Delete", key=f"confirm_del_room_yes_{rn}"):
                        try:
                            ok = execute_query("DELETE FROM room WHERE room_no=%s", (rn,), fetch=False)
                            if ok:
                                st.success(f"✅ Room {rn} deleted.")
                                st.session_state.pop(f"confirm_del_room_{rn}", None)
                                st.session_state._last_action += 1
                                st.rerun()
                            else:
                                st.error("Failed to delete room")
                        except Exception as e:
                            _show_db_error(e)
                with c2:
                    if st.button("Cancel", key=f"confirm_del_room_no_{rn}"):
                        st.session_state.pop(f"confirm_del_room_{rn}", None)
                        st.info("Cancelled deletion.")
                        st.session_state._last_action += 1

            # Edit UI
            if st.session_state.get(f"show_edit_room_{rn}", False):
                with st.expander(f"Edit Room {rn}", expanded=True):
                    fresh = execute_query("SELECT * FROM room WHERE room_no=%s", (rn,))
                    if not fresh:
                        st.error("Room not found")
                    else:
                        fresh = fresh[0]
                        with st.form(key=f"edit_room_form_{rn}"):
                            # Provide campus/block/building/floor selectors but default to current values
                            campuses = get_all_campuses()
                            campus_map = {c['campus_name']: c['campus_id'] for c in campuses}
                            current_campus_name = None
                            if fresh.get('campus_id'):
                                inv = {v:k for k,v in campus_map.items()}
                                current_campus_name = inv.get(fresh.get('campus_id'))
                            selected_campus = st.selectbox("Campus", ["Select Campus"] + list(campus_map.keys()),
                                                           index=0 if not current_campus_name else (["Select Campus"] + list(campus_map.keys())).index(current_campus_name),
                                                           key=f"edit_room_campus_{rn}")
                            campus_id = campus_map.get(selected_campus)

                            blocks = get_blocks_by_campus(campus_id) if campus_id else []
                            block_map = {b['block_name']: b['block_id'] for b in blocks}
                            current_block_name = None
                            if fresh.get('block_id'):
                                invb = {v:k for k,v in block_map.items()}
                                current_block_name = invb.get(fresh.get('block_id'))
                            selected_block = st.selectbox("Block", ["Select Block"] + list(block_map.keys()),
                                                          index=0 if not current_block_name else (["Select Block"] + list(block_map.keys())).index(current_block_name),
                                                          key=f"edit_room_block_{rn}")
                            block_id = block_map.get(selected_block)

                            buildings = get_buildings_by_block(block_id) if block_id else []
                            building_map = {b['build_name']: b['building_id'] for b in buildings}
                            current_building_name = None
                            if fresh.get('building_id'):
                                invbld = {v:k for k,v in building_map.items()}
                                current_building_name = invbld.get(fresh.get('building_id'))
                            selected_building = st.selectbox("Building", ["Select Building"] + list(building_map.keys()),
                                                             index=0 if not current_building_name else (["Select Building"] + list(building_map.keys())).index(current_building_name),
                                                             key=f"edit_room_building_{rn}")
                            building_id = building_map.get(selected_building)

                            floors = get_floors_by_building(building_id) if building_id else []
                            floor_map = {f['floor_name']: f['floor_no'] for f in floors}
                            current_floor_name = None
                            if fresh.get('floor_no'):
                                invfl = {v:k for k,v in floor_map.items()}
                                current_floor_name = invfl.get(fresh.get('floor_no'))
                            selected_floor = st.selectbox("Floor", ["Select Floor"] + list(floor_map.keys()),
                                                          index=0 if not current_floor_name else (["Select Floor"] + list(floor_map.keys())).index(current_floor_name),
                                                          key=f"edit_room_floor_{rn}")
                            floor_no = floor_map.get(selected_floor)

                            new_room_no = st.number_input("Room Number", min_value=1, value=int(fresh.get('room_no')), key=f"edit_room_no_{rn}")
                            room_type = st.selectbox("Room Type", ["Lab", "Lecture", "Office", "Conference Room"],
                                                     index=["Lab","Lecture","Office","Conference Room"].index(fresh.get('type')) if fresh.get('type') in ["Lab","Lecture","Office","Conference Room"] else 0,
                                                     key=f"edit_room_type_{rn}")
                            location = st.text_input("Location", value=fresh.get('location') or "", key=f"edit_room_location_{rn}")

                            if st.form_submit_button("Save Changes", key=f"save_room_{rn}"):
                                try:
                                    ok = execute_query("""UPDATE room SET room_no=%s, location=%s, type=%s, floor_no=%s,
                                                          block_id=%s, campus_id=%s, building_id=%s
                                                          WHERE room_no=%s""",
                                                       (int(new_room_no), location, room_type, int(floor_no) if floor_no else None,
                                                        int(block_id) if block_id else None,
                                                        int(campus_id) if campus_id else None,
                                                        int(building_id) if building_id else None,
                                                        rn),
                                                       fetch=False)
                                    if ok:
                                        st.success("✅ Room updated successfully.")
                                        st.session_state[f"show_edit_room_{rn}"] = False
                                        st.session_state._last_action += 1
                                        st.rerun()
                                    else:
                                        st.error("Failed to update room")
                                except Exception as e:
                                    _show_db_error(e)
    else:
        st.info("No rooms found")

    st.markdown("---")
    st.subheader("➕ Add New Room")

    # ------------------------------
    # Dropdowns for hierarchy (Add room)
    # ------------------------------
    campuses = get_all_campuses() or []
    campus_map = {c['campus_name']: c['campus_id'] for c in campuses}

    selected_campus = st.selectbox(
        "Campus *", ["Select Campus"] + list(campus_map.keys()),
        key="room_campus"
    )
    campus_id = campus_map.get(selected_campus)

    blocks = get_blocks_by_campus(campus_id) if campus_id else []
    block_map = {b['block_name']: b['block_id'] for b in blocks}

    selected_block = st.selectbox(
        "Block *", ["Select Block"] + list(block_map.keys()),
        key="room_block"
    )
    block_id = block_map.get(selected_block)

    buildings = get_buildings_by_block(block_id) if block_id else []
    building_map = {b['build_name']: b['building_id'] for b in buildings}

    selected_building = st.selectbox(
        "Building *", ["Select Building"] + list(building_map.keys()),
        key="room_building"
    )
    building_id = building_map.get(selected_building)

    floors = get_floors_by_building(building_id) if building_id else []
    floor_map = {f['floor_name']: f['floor_no'] for f in floors}

    selected_floor = st.selectbox(
        "Floor *", ["Select Floor"] + list(floor_map.keys()),
        key="room_floor"
    )
    floor_no = floor_map.get(selected_floor)

    room_no = st.number_input("Room Number *", min_value=1, step=1, value=1, key="room_no_add")
    room_type = st.selectbox("Room Type *", ["Lab", "Lecture", "Office", "Conference Room"], key="room_type")

    # ------------------------------
    # Generate short location code
    # ------------------------------
    if selected_campus and selected_block and selected_building:
        campus_short = selected_campus.split()[0][:2].upper()
        block_short = selected_block.replace("Block", "").strip()[:1].upper()
        building_short = selected_building.replace("Building", "").strip()[-1:]
        location = f"{campus_short}-{block_short}{building_short}"
    else:
        location = None

    # ------------------------------
    # Insert into DB
    # ------------------------------
    if st.button("✅ Add Room"):
        if not campus_id or not block_id or not building_id or not floor_no:
            st.error("❌ Please select all dropdowns.")
        elif room_no < 1:
            st.error("❌ Room number must be at least 1")
        elif not location:
            st.error("❌ Could not generate location code. Check selections.")
        else:
            try:
                result = execute_query(
                    """INSERT INTO room 
                       (room_no, location, type, is_allotted, floor_no, block_id, campus_id, building_id)
                       VALUES (%s,%s,%s,b'0',%s,%s,%s,%s)""",
                    (int(room_no), location, room_type,
                     int(floor_no), int(block_id), int(campus_id), int(building_id)),
                    fetch=False
                )
                if result:
                    st.success(f"✅ Room {room_no} added successfully as {location}!")
                    st.session_state._last_action += 1
                    st.rerun()
                else:
                    st.error("❌ Failed to add room. Room number may already exist.")
            except Exception as e:
                _show_db_error(e)


# -------------------------
# Allocations
# -------------------------
def show_allocations():
    if st.session_state.role != "admin":
        st.error("❌ Access Denied — Admin only")
        return

    st.header("📋 Room Allocations")
    available = get_available_rooms()
    faculty_no_room = execute_query("SELECT faculty_id, faculty_name FROM faculty WHERE room_no IS NULL ORDER BY faculty_name")

    col1, col2 = st.columns(2)
    with col1:
        if faculty_no_room:
            fdict = {f"{r['faculty_name']} (ID {r['faculty_id']})": r['faculty_id'] for r in faculty_no_room}
            sel_fac = st.selectbox("Select Faculty", ["Select Faculty"] + list(fdict.keys()), key="alloc_fac")
        else:
            st.info("All faculty have rooms")
            sel_fac = None
    with col2:
        if available:
            sel_room = st.selectbox("Select Room", ["Select Room"] + [str(r) for r in available], key="alloc_room")
        else:
            st.info("No available rooms")
            sel_room = None

    if st.button("Allocate Room"):
        if not sel_fac or sel_fac == "Select Faculty" or not sel_room or sel_room == "Select Room":
            st.error("Select both faculty and room")
        else:
            faculty_id = fdict[sel_fac]
            room_no = int(sel_room)
            try:
                ok1 = execute_query("UPDATE faculty SET room_no=%s WHERE faculty_id=%s", (room_no, faculty_id), fetch=False)
                ok2 = execute_query("UPDATE room SET is_allotted=1 WHERE room_no=%s", (room_no,), fetch=False)
                if ok1 and ok2:
                    st.success("✅ Room allocated")
                    st.session_state._last_action += 1
                else:
                    st.error("Allocation failed")
            except Exception as e:
                _show_db_error(e)

# -------------------------
# Departments
# -------------------------
def show_departments():
    if st.session_state.role != "admin":
        st.error("❌ Access Denied — Admin only")
        return

    st.header("🏛️ Departments")
    depts = execute_query("""
        SELECT d.dept_id, d.dept_name, f.faculty_name as hod_name,
               (SELECT COUNT(*) FROM faculty WHERE dept_id=d.dept_id) as faculty_count
        FROM department d
        LEFT JOIN faculty f ON d.dept_hod_id = f.faculty_id
        ORDER BY d.dept_id
    """)
    if depts:
        st.dataframe(pd.DataFrame(depts), use_container_width=True)
    else:
        st.info("No departments found")

    # Manage list (edit/delete inline)
    if depts:
        for rec in depts:
            dept_id = rec['dept_id']
            cols = st.columns([3,1,1])
            with cols[0]:
                st.markdown(f"**{rec['dept_name']}**  \nHOD: {rec['hod_name'] or 'None'}  \nFaculty Count: {rec['faculty_count']}")
            with cols[1]:
                if st.button("✏️ Edit", key=f"edit_dept_{dept_id}"):
                    st.session_state[f"show_edit_dept_{dept_id}"] = not st.session_state.get(f"show_edit_dept_{dept_id}", False)
                    st.session_state._last_action += 1
            with cols[2]:
                if st.button("🗑️ Delete", key=f"del_dept_{dept_id}"):
                    st.session_state[f"confirm_del_dept_{dept_id}"] = True
                    st.session_state._last_action += 1

            # Confirm delete UI
            if st.session_state.get(f"confirm_del_dept_{dept_id}", False):
                st.warning(f"Are you sure you want to delete Department **{rec['dept_name']}**? This cannot be undone.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Confirm Delete", key=f"confirm_del_dept_yes_{dept_id}"):
                        try:
                            ok = execute_query("DELETE FROM department WHERE dept_id=%s", (dept_id,), fetch=False)
                            if ok:
                                st.success(f"✅ Department {rec['dept_name']} deleted.")
                                st.session_state.pop(f"confirm_del_dept_{dept_id}", None)
                                st.session_state._last_action += 1
                                st.rerun()
                            else:
                                st.error("Failed to delete department")
                        except Exception as e:
                            _show_db_error(e)
                with c2:
                    if st.button("Cancel", key=f"confirm_del_dept_no_{dept_id}"):
                        st.session_state.pop(f"confirm_del_dept_{dept_id}", None)
                        st.info("Cancelled deletion.")
                        st.session_state._last_action += 1

            # Edit form
            if st.session_state.get(f"show_edit_dept_{dept_id}", False):
                with st.expander(f"Edit Department {rec['dept_name']}", expanded=True):
                    fresh = execute_query("SELECT * FROM department WHERE dept_id=%s", (dept_id,))
                    if not fresh:
                        st.error("Department not found")
                    else:
                        fresh = fresh[0]
                        with st.form(key=f"edit_dept_form_{dept_id}"):
                            new_name = st.text_input("Department Name", value=fresh.get('dept_name') or "", key=f"dept_name_{dept_id}")

                            # Professors/faculty who are not HODs anywhere (backend logic)
                            professors = execute_query("""
                                SELECT f.faculty_id, f.faculty_name
                                FROM faculty f
                                WHERE f.faculty_id NOT IN (
                                    SELECT COALESCE(dept_hod_id, 0)
                                    FROM department
                                    WHERE dept_hod_id IS NOT NULL
                                )
                                ORDER BY f.faculty_name
                            """)
                            hod_options = ["None"] + [f"{p['faculty_id']} - {p['faculty_name']}" for p in professors] if professors else ["None"]

                            # If the current HOD is set and not in the list (because it's the current dept's HOD),
                            # include them in the options so the admin can keep the same HOD.
                            current_hod_id = fresh.get('dept_hod_id')
                            if current_hod_id:
                                cur_hod = execute_query("SELECT faculty_id, faculty_name FROM faculty WHERE faculty_id=%s", (current_hod_id,))
                                if cur_hod and len(cur_hod) > 0:
                                    label = f"{cur_hod[0]['faculty_id']} - {cur_hod[0]['faculty_name']}"
                                    if label not in hod_options:
                                        hod_options.insert(1, label)  # insert after None

                            hod_choice = st.selectbox("Select HOD (optional)", hod_options,
                                                      index=0 if not fresh.get('dept_hod_id') else (hod_options.index(label) if fresh.get('dept_hod_id') and 'label' in locals() and label in hod_options else 0),
                                                      key=f"dept_hod_select_{dept_id}")

                            if st.form_submit_button("Save Changes", key=f"save_dept_{dept_id}"):
                                if not new_name:
                                    st.error("Department name required")
                                else:
                                    try:
                                        hod_id = None if hod_choice == "None" else int(hod_choice.split(" - ")[0])
                                        ok = execute_query("UPDATE department SET dept_name=%s, dept_hod_id=%s WHERE dept_id=%s",
                                                           (new_name, hod_id, dept_id), fetch=False)
                                        if ok:
                                            st.success("✅ Department updated successfully")
                                            st.session_state[f"show_edit_dept_{dept_id}"] = False
                                            st.session_state._last_action += 1
                                            st.rerun()
                                        else:
                                            st.error("Failed to update department")
                                    except Exception as e:
                                        _show_db_error(e)

    # Add Department block (with backend logic to show faculty not HODs)
    st.markdown("---")
    with st.expander("Add Department"):
        with st.form("add_dept_form"):
            dept_name = st.text_input("Department Name", key="new_dept_name")

            # Fetch faculty who are NOT HOD of any other department
            professors = execute_query("""
                SELECT f.faculty_id, f.faculty_name
                FROM faculty f
                WHERE f.faculty_id NOT IN (
                    SELECT COALESCE(dept_hod_id, 0)
                    FROM department
                    WHERE dept_hod_id IS NOT NULL
                )
                ORDER BY f.faculty_name
            """)

            hod_options = ["None"] + [f"{p['faculty_id']} - {p['faculty_name']}" for p in professors] if professors else ["None"]
            hod_choice = st.selectbox("Select HOD (optional)", hod_options, key="new_dept_hod")

            if st.form_submit_button("Add Department"):
                if not dept_name:
                    st.error("Department name required")
                else:
                    try:
                        hod_id = None if hod_choice == "None" else int(hod_choice.split(" - ")[0])
                        ok = execute_query("INSERT INTO department (dept_name, dept_hod_id) VALUES (%s,%s)", (dept_name, hod_id), fetch=False)
                        if ok:
                            st.success("✅ Department added")
                            st.session_state._last_action += 1
                            st.rerun()
                        else:
                            st.error("Failed to add department")
                    except Exception as e:
                        _show_db_error(e)

# -------------------------
# Reports (all users)
# -------------------------
def show_reports():
    st.header("📈 Reports & Analytics")
    report = execute_query("""
        SELECT f.faculty_id, f.faculty_name, f.post, d.dept_name,
               CASE WHEN f.room_no IS NULL THEN 'Not Allocated' ELSE 'Allocated' END as status,
               f.room_no
        FROM faculty f
        LEFT JOIN department d ON f.dept_id = d.dept_id
        ORDER BY f.faculty_name
    """)
    if report:
        df = pd.DataFrame(report)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False)
        st.download_button("📥 Download CSV", data=csv, file_name="faculty_report.csv", mime="text/csv")
    else:
        st.info("No data for reports")

# -------------------------
# Main controller
# -------------------------
def main():
    # Show login first; if login succeeds it sets st.session_state.logged_in = True in same run
    if not st.session_state.logged_in:
        # Minimal sidebar content before login
        st.sidebar.title("Go To")
        st.sidebar.write("Login to access the app")
        show_login()
        return

    # After login: sidebar + navigation
    st.sidebar.title("Navigation")
    if st.session_state.role == "admin":
        pages = ["📊 Dashboard", "👨‍🏫 Faculty", "🏢 Rooms", "📋 Allocations", "🏛️ Departments", "📈 Reports"]
    else:
        pages = ["📊 Dashboard", "📈 Reports"]

    page = st.sidebar.radio("Menu", pages)
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.username}  \n**Role:** {st.session_state.role}")
    if st.sidebar.button("Logout"):
        do_logout()
        return

    # Show page
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "👨‍🏫 Faculty":
        show_faculty_management()
    elif page == "🏢 Rooms":
        show_room_management()
    elif page == "📋 Allocations":
        show_allocations()
    elif page == "🏛️ Departments":
        show_departments()
    elif page == "📈 Reports":
        show_reports()
    else:
        st.info("Select a page from the sidebar.")

if __name__ == "__main__":
    main()
