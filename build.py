import subprocess
import sys

def build_exe():
    # Menentukan perintah PyInstaller
    pyinstaller_command = [
        "pyinstaller",
        # "--noconsole",
        "--add-data", "config.ini;.",
        "--add-data", "epm_responsive.ui;.",
        # "--add-data", "epm_ui.py;.",
        "--add-data", "epm_form.ui;.",
        "--add-data", "epm_form_ui.py;.",
        "--add-data", "models/mouse-yolov8.pt;models",
        "--add-data", "lib/counting.py;lib",
        "--add-data", "lib/detection.py;lib",
        "--add-data", "lib/recorder.py;lib",
        "--add-data", "lib/tracking.py;lib",
        "--add-data", "lib/utils.py;lib",
        "--add-data", "C:\\Users\\ACER\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\ultralytics\\cfg\\default.yaml;ultralytics/cfg", 
        "main.py"  
    ]
    
    # Menjalankan perintah PyInstaller
    try:
        subprocess.run(pyinstaller_command, check=True)
        print("Build berhasil!")
    except subprocess.CalledProcessError as e:
        print(f"Terjadi kesalahan saat menjalankan PyInstaller: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()
