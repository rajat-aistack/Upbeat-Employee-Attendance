"""
Packaging script to compile Employee App and Admin App into standalone executables using PyInstaller.
"""
import os
import sys
import subprocess
import shutil

def run_command(cmd, description):
    print(f"\n--- {description} ---")
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"Error: {description} failed with return code {result.returncode}")
        sys.exit(result.returncode)
    print("Success!")

def main():
    # 1. Ensure pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller is not installed in the virtual environment.")
        print("Installing pyinstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # 2. Get CustomTkinter directory to bundle its assets
    import customtkinter
    ctk_dir = os.path.dirname(customtkinter.__file__)
    print(f"CustomTkinter path: {ctk_dir}")

    # Clean up previous builds
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            print(f"Cleaning existing {folder} folder...")
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(f"Warning: Could not remove {folder}: {e}")
                print("Continuing anyway...")

    # Clean up any spec files
    for file in os.listdir("."):
        if file.endswith(".spec"):
            try:
                os.remove(file)
                print(f"Removed spec file: {file}")
            except Exception as e:
                print(f"Warning: Could not remove spec file {file}: {e}")

    # 3. Build Employee Attendance Application
    print("\n==========================================")
    print("BUILDING EMPLOYEE ATTENDANCE APPLICATION")
    print("==========================================")
    
    employee_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name=Upbeat_Attendance",
        f"--add-data={ctk_dir}{os.pathsep}customtkinter",
        f"--add-data=assets/icon.ico{os.pathsep}assets",
        "--icon=assets/icon.ico",
        "employee_app/main.py"
    ]
    
    run_command(employee_cmd, "Compiling Upbeat_Attendance.exe")

    # 4. Build Admin Application
    print("\n==========================================")
    print("BUILDING ADMIN MANAGEMENT APPLICATION")
    print("==========================================")
    
    admin_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name=Upbeat_Admin",
        f"--add-data={ctk_dir}{os.pathsep}customtkinter",
        f"--add-data=assets/icon.ico{os.pathsep}assets",
        "--icon=assets/icon.ico",
        "admin_app/main.py"
    ]
    
    run_command(admin_cmd, "Compiling Upbeat_Admin.exe")

    print("\n==========================================")
    print("BUILD COMPLETE!")
    print("Executables are available in the 'dist' folder:")
    print(f"1. Employee App: {os.path.abspath('dist/Upbeat_Attendance.exe')}")
    print(f"2. Admin App:    {os.path.abspath('dist/Upbeat_Admin.exe')}")
    print("==========================================")

if __name__ == "__main__":
    main()
