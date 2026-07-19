"""
Verification script to test end-to-end flow of REST API, Employee App services, and Admin App services.
"""
import sys
import os
import time
from datetime import datetime, date

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from admin_app.services.api_client import AdminAPIClient
from employee_app.services.api_client import APIClient as EmployeeAPIClient
from employee_app.services.fingerprint import generate_fingerprint

def test_flow():
    print("--- Starting End-to-End Verification Test ---")
    
    # 1. Initialize Clients
    admin_client = AdminAPIClient()
    emp_client = EmployeeAPIClient()
    
    # 2. Test Connection
    print("Checking API Health...")
    if not admin_client.check_health():
        print("Error: API Server is not running or unreachable!")
        return
    print("API Server is healthy.")
    
    # 3. Log in as Admin
    print("\nLogging in as admin...")
    try:
        admin_client.login("admin", "admin123")
        print("Admin login successful.")
    except Exception as e:
        print(f"Admin login failed: {e}")
        return
        
    # 4. Get Dashboard Stats (initial)
    print("\nFetching initial dashboard stats...")
    stats = admin_client.get_dashboard_stats()
    print(f"Stats: {stats}")
    
    # 5. Create a test employee
    print("\nCreating test employee...")
    emp_id = "EMP-TEST-99"
    try:
        # Check if already exists from previous runs, delete if so
        existing = admin_client.list_employees(search=emp_id)
        for e in existing.get("employees", []):
            print(f"Deleting existing test employee: {e['name']}")
            admin_client.delete_employee(e["id"])
            
        emp_data = {
            "employee_id": emp_id,
            "name": "Jane Test Doe",
            "department": "QA",
            "designation": "Automation Engineer",
            "mobile": "1234567890"
        }
        new_emp = admin_client.create_employee(emp_data)
        emp_db_id = new_emp["id"]
        print(f"Created employee: {new_emp['name']} (DB ID: {emp_db_id})")
    except Exception as e:
        print(f"Failed to create employee: {e}")
        return
        
    # 6. Generate Device Fingerprint & Request Registration (Employee App side)
    print("\nGenerating fingerprint...")
    fingerprint = generate_fingerprint()
    print(f"Fingerprint: {fingerprint}")
    
    # Check registration (should be false)
    print("Checking registration status via employee client...")
    lookup = emp_client.lookup_device(fingerprint)
    print(f"Lookup: {lookup}")
    
    # Request registration
    print("Requesting registration...")
    reg_req = emp_client.request_registration(
        fingerprint=fingerprint,
        hostname="TEST-HOST",
        machine_guid="TEST-GUID-1234",
        system_username="testuser",
        system_details={"os": "Windows-10", "script": "Verification"}
    )
    reg_code = reg_req["registration_code"]
    print(f"Registration code received: {reg_code}")
    
    # 7. Approve Registration via Admin Client
    print("\nListing pending devices via admin client...")
    pending = admin_client.list_pending_devices()
    print(f"Pending devices: {pending.get('devices')}")
    
    print(f"Assigning registration code {reg_code} to employee {emp_db_id}...")
    reg_res = admin_client.register_device(reg_code, emp_db_id)
    print(f"Registration Response: {reg_res}")
    
    # Re-check registration status via employee client (should now be true)
    print("Re-checking lookup status via employee client...")
    lookup = emp_client.lookup_device(fingerprint)
    print(f"Lookup (should be true/active): {lookup}")
    if not lookup.get("registered"):
        print("Error: Device lookup registration is still False!")
        return
        
    # 8. Punch In (Employee App side)
    print("\nPunching In...")
    punch_in_payload = {
        "device_fingerprint": fingerprint,
        "hostname": "TEST-HOST",
        "system_username": "testuser",
        "ip_address": "192.168.1.50",
        "mac_address": "00:11:22:33:44:55",
        "wifi_ssid": "UpbeatOffice",
        "wifi_bssid": "aa:bb:cc:dd:ee:ff",
        "gateway_mac": "00:aa:bb:cc:dd:ee",
        "gateway_ip": "192.168.1.1"
    }
    try:
        res = emp_client.punch_in(punch_in_payload)
        print(f"Punch In Result: {res}")
    except Exception as e:
        print(f"Punch In Failed: {e}")
        return
        
    # Check status
    status_res = emp_client.get_attendance_status(fingerprint)
    print(f"Today's Attendance Status: {status_res}")
    
    # 9. Punch Out (Employee App side)
    print("\nPunching Out...")
    try:
        res = emp_client.punch_out(punch_in_payload)
        print(f"Punch Out Result: {res}")
    except Exception as e:
        print(f"Punch Out Failed: {e}")
        return
        
    # Check status again
    status_res = emp_client.get_attendance_status(fingerprint)
    print(f"Today's Attendance Status after Punch Out: {status_res}")
    
    # 10. Admin view dashboard & reports
    print("\nFetching updated dashboard stats...")
    stats = admin_client.get_dashboard_stats()
    print(f"Updated Stats: {stats}")
    
    print("\nFetching attendance report...")
    today_str = date.today().isoformat()
    report = admin_client.get_attendance_report(today_str, today_str)
    print(f"Report Records: {report.get('records')}")
    
    print("\nExporting report to CSV/Excel...")
    from admin_app.services.export_service import export_to_csv, export_to_excel
    csv_path = export_to_csv(report.get("records", []), "test_report.csv")
    xlsx_path = export_to_excel(report.get("records", []), "test_report.xlsx")
    print(f"CSV exported to: {csv_path}")
    print(f"Excel exported to: {xlsx_path}")
    
    print("\n--- End-to-End Verification Test Successful! ---")

if __name__ == "__main__":
    test_flow()
