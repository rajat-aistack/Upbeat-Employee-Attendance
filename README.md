# Upbeat Employee Attendance Management System

A professional, desktop-based attendance management system built for **Upbeat Exposition Company**. The solution is designed to be user-friendly, secure, robust, and require no programming knowledge for day-to-day operations.

## Architecture

The system consists of four independent modules:
1. **REST API**: Built with FastAPI. Serves as the central backend connecting all devices.
2. **Database**: SQLite (local file database, designed for easy migration to MySQL/PostgreSQL).
3. **Employee Application**: Desktop attendance application built with CustomTkinter.
4. **Admin Application**: Desktop management panel built with CustomTkinter.

---

## Features

### REST API & Database
- **Secure Authentication**: Hashed administrator passwords using bcrypt, secure JWT tokens for admin sessions, and request header verification via API Key.
- **Auto-Seeding**: The API creates the database schemas and seeds the default admin user and default settings automatically on the first run.
- **Robust Sync**: Supports local offline attendance storage and background synchronization using unique idempotency identifiers.

### Employee Application
- **Zero-Configuration**: The app remains identical for all employee computers and never needs to be rebuilt when new employees join.
- **Hardware Fingerprint**: Dynamically registers computers using a unique SHA256 hardware identifier.
- **WiFi Restriction**: Ensures attendance can only be punched when connected to the official office WiFi network (validating BSSID, Gateway MAC, and SSID).
- **Offline Punches**: Stores attendance punches locally if the office internet goes down, and syncs automatically in the background once online.

### Admin Application
- **Dashboard**: Real-time stats of employees checked-in, late arrivals, checked-out, and pending registrations.
- **Employee CRUD**: Easily add, edit, activate, deactivate, or permanently delete employees.
- **Device Management**: View registered computers, approve pending device registrations with one click, and replace/retire devices.
- **Export Reports**: Generate detailed reports by date range or department, and export to **Excel (.xlsx)**, **CSV**, or **PDF**.
- **Settings configuration**: Update office hours, grace periods, and WiFi parameters, or auto-detect network properties with a single click.

---

## Installation & Setup

### Prerequisites
- Python 3.9+ installed on your system.

### 1. Install Dependencies
Clone this repository and install the required dependencies using pip:
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```

### 2. Running the REST API Backend
Start the FastAPI server using Uvicorn:
```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Swagger Documentation**: View interactive API docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
- **Default Credentials**: 
  - Username: `admin`
  - Password: `admin123`

### 3. Running the Employee Application
Launch the Employee app from the command line:
```bash
python employee_app/main.py
```

### 4. Running the Admin Application
Launch the Admin app from the command line:
```bash
python admin_app/main.py
```

---

## Packaging to Executables (.exe)

You can package both applications into standalone single-file executables using PyInstaller. A utility build script is provided at the root:

```bash
python build.py
```

This will generate two executables inside the `dist/` directory:
1. `Upbeat_Attendance.exe` (Employee App)
2. `Upbeat_Admin.exe` (Admin App)

These executables are fully standalone and can be copied directly to employee and administrator computers.

---

## System Workflow Guide

### Step 1: Initial Launch on Employee Computer
1. Open the compiled `Upbeat_Attendance.exe` on an employee's computer.
2. The application will detect that the computer is not registered and display a unique **Registration Code** (e.g. `ABC-123-XYZ`).
3. Copy the code and provide it to the office administrator.

### Step 2: Approve the Computer in Admin App
1. Open `Upbeat_Admin.exe` on the administrator's PC and log in.
2. Go to the **Devices** section. You will see the new computer listed in the **Pending** state.
3. Click **Register** on that computer, select the employee from the dropdown list, and save.

### Step 3: Recording Attendance
1. Restart the Employee Application. It will now show the check-in and check-out screen.
2. When connected to the office network, the employee can click **Punch In** to record their attendance.
3. Before leaving the office, they can click **Punch Out** to check out.
