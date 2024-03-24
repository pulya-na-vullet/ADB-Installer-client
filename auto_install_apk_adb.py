import os
import subprocess
import customtkinter
import threading
import time


empty_file = True
apk_folder_path = 'C:/apk/3391.apk'
apk_folder_path_alkor = "C:/Users/alkor/Desktop/auto_install_apk/apk/app-RuPreprodFcm-debug-develop-371.apk"
interval = 1
app_name_adb_list_test_letu = "ru.letu.preprod"
file_for_save_test_device_id = "test_device.txt"
app_versions_in_device = "app_versions_in_device.txt"



def scan_devices_id_and_safe_to_file():
    result = os.popen("adb devices").read().split('\n')
    with open(file_for_save_test_device_id, "w") as file:
        for device in result[1:-2]:
            if device.strip():
                file.write(device.split()[0] + "\n")

def get_app_versions():
    with open(file_for_save_test_device_id, "r") as file:
        devices = file.read().splitlines()
    with open(app_versions_in_device, "w") as output:
        for device_id in devices:
            result = os.popen(f"adb -s {device_id} shell dumpsys package {app_name_adb_list_test_letu} | grep versionName").read()
            if result:
                version_name = result.split("=")[1].strip()
                output.write(f"{device_id} versionName={version_name}\n")
            else:
                output.write(f"{device_id} versionName=N/A\n")

def uninstall_app_to_all_devices():
    with open(file_for_save_test_device_id, 'r') as file:
        for line in file:
            dev_id = line.strip()
            result = subprocess.run(['adb', '-s', dev_id, 'shell', 'pm', 'list', 'packages', '-3'], stdout=subprocess.PIPE)
            output = result.stdout.decode('utf-8')
            lines = output.splitlines()
            for line in lines:
                if app_name_adb_list_test_letu in line:
                    package_name = line.split(':')[-1].strip()
                    subprocess.run(['adb', '-s', dev_id, 'uninstall', package_name], stdout=subprocess.PIPE)

def install_apk_on_one_device(device_id):
    result = os.popen(f"adb -s {device_id} install {apk_folder_path}").read()

def install_apk_on_all_device():
    with open(file_for_save_test_device_id, "r") as file:
        devices = file.read().splitlines()
    for device_id in devices:
        result = os.popen(f"adb -s {device_id} install {apk_folder_path}").read()

def install_apk_on_all_device_async():
    threading.Thread(target=install_apk_on_all_device).start()

def scan_and_get_versions():
    scan_devices_id_and_safe_to_file()
    get_app_versions()

app = customtkinter.CTk()
app.title("Broadcast APK")
app.geometry("180x200")

button = customtkinter.CTkButton(app, text="Scan devices", command=scan_and_get_versions)
button.grid(row=0, column=1, padx=20, pady=20)

button = customtkinter.CTkButton(app, text="Uninstall for all", command=uninstall_app_to_all_devices)
button.grid(row=1, column=1, padx=20, pady=20)

button = customtkinter.CTkButton(app, text="Global Install", command=install_apk_on_all_device_async)
button.grid(row=2, column=1, padx=20, pady=20)

app.mainloop()