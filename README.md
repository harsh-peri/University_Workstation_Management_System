University Workstation Management System
A Streamlit + MySQL based administration system for managing faculty, rooms, departments, and campus infrastructure. This system centralizes workstation allocation and administrative workflows into one unified dashboard.

Features
Authentication
- Login using MySQL credentials
- Role based access (Admin/User)

Faculty Management
- Add, edit, delete faculty
- Assign and update rooms
- Search by name
- Filter by department
- Auto update of room allocation status

Room Management
- View all rooms
- Full hierarchy support: campus, block, building, floor
- Add new rooms with auto generated short location codes
- Edit room details
- Delete rooms with confirmation
- Live room allocation status

Department Management
- Add departments
- HOD selection limited to faculty who are not HODs elsewhere
- Edit department name and HOD
- Delete departments with confirmation
- Faculty count per department

Campus Hierarchy
- Campus
- Block
- Building
- Floor
- Room
Rooms are mapped completely through this hierarchy.

Room Allocation
- Assign available rooms to faculty without rooms
- Only unallocated rooms appear in dropdowns
- Database updates instantly

Dashboard and Reports
- Faculty count
- Room count
- Allocated vs available rooms
- Department count
- Campus count
- Recent allocations table
- Exportable reports (CSV)

Tech Stack
- Python
- Streamlit
- MySQL
- Pandas

Folder Structure
university-workstation-management/
 app.py
 README.txt
 requirements.txt
 database.sql

Installation
1. Clone repository:
   git clone https://github.com/harsh-peri/University_Workstation_Management_System.git
   cd University_Workstation_Management_System

2. Optional: create virtual environment
   python -m venv venv
   source venv/bin/activate   (Mac/Linux)
   venv\Scripts\activate      (Windows)

3. Install dependencies:
   pip install -r requirements.txt

4. Import MySQL schema:
   SOURCE database.sql;

6. Update credentials in app.py:
   host="localhost"
   database="university_workstation"

7. Run the application:
   streamlit run app.py

How It Works
- Admin logs in using MySQL username and password
- Gains access to faculty, departments, rooms, allocations, and reports
- All CRUD operations update MySQL instantly
- Full hierarchy ensures consistent room location mapping

Future Improvements
- Audit logs
- Multi-admin roles
- Bulk CSV import
- Asset tracking
- Automated timetable integration
