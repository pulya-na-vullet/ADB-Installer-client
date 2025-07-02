import subprocess
import threading
from datetime import datetime

class ADBController:
    def __init__(self, ui):
        self.ui = ui
        self.device_list = []
        self.package_list = []
        self.last_scan_time = 0
        self.scan_interval = 5

    def background_scanner(self):
        while self.ui.scanning_active:
            try:
                current_time = datetime.now().timestamp()
                if current_time - self.last_scan_time >= self.scan_interval:
                    self.scan_devices()
                    self.last_scan_time = current_time
                threading.Event().wait(0.5)
            except Exception as e:
                self.ui.ui_queue.put(("error", f"Scanner error: {str(e)}"))

    def scan_devices(self):
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
            devices = [
                line.split('\t')[0] 
                for line in result.stdout.split('\n')[1:] 
                if line.strip() and 'device' in line
            ]
            
            if devices != self.device_list:
                self.device_list = devices
                self.get_packages_info(force_update=True)
            else:
                self.get_packages_info()
        except subprocess.TimeoutExpired:
            self.ui.ui_queue.put(("error", "ADB timeout during devices scan"))
        except Exception as e:
            self.ui.ui_queue.put(("error", f"Device scan error: {str(e)}"))

    def get_packages_info(self, force_update=False):
        try:
            packages = set()
            for device in self.device_list:
                result = subprocess.run(
                    ['adb', '-s', device, 'shell', 'pm', 'list', 'packages', '-3'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                for line in result.stdout.splitlines():
                    if line:
                        packages.add(line.split(':')[-1])
            
            if force_update or packages != set(self.package_list):
                self.package_list = sorted(packages)
                self.ui.ui_queue.put(("update_packages", self.package_list))
        except subprocess.TimeoutExpired:
            self.ui.ui_queue.put(("error", "ADB timeout during packages scan"))
        except Exception as e:
            self.ui.ui_queue.put(("error", f"Package scan error: {str(e)}"))

    def install_apk_thread(self, apk_path):
        self.ui.log_status("Starting installation...")
        try:
            for device in self.device_list:
                self.ui.log_status(f"Installing on {device}...")
                result = subprocess.run(
                    ['adb', '-s', device, 'install', '-r', apk_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    self.ui.log_status(f"Successfully installed on {device}")
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip()
                    self.ui.log_status(f"Failed to install on {device}: {error_msg}")
            self.get_packages_info(force_update=True)
        except Exception as e:
            self.ui.log_status(f"Installation error: {str(e)}")
        finally:
            self.ui.log_status("Installation process completed")

    def uninstall_thread(self, packages):
        self.ui.log_status(f"Starting uninstall of {len(packages)} packages...")
        try:
            success_count = 0
            fail_count = 0
            for device in self.device_list:
                for package in packages:
                    self.ui.log_status(f"Uninstalling {package} from {device}...")
                    result = subprocess.run(
                        ['adb', '-s', device, 'uninstall', package],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        success_count += 1
                        self.ui.log_status(f"Successfully uninstalled {package}")
                    else:
                        fail_count += 1
                        error_msg = result.stderr.strip() or result.stdout.strip()
                        self.ui.log_status(f"Failed to uninstall {package}: {error_msg}")
            
            self.get_packages_info(force_update=True)
            self.ui.selected_packages.clear()
            for var in self.ui.checkbox_vars.values():
                var.set("off")
            
            self.ui.log_status(f"Uninstall complete. Success: {success_count}, Failed: {fail_count}")
        except Exception as e:
            self.ui.log_status(f"Uninstall error: {str(e)}")
        finally:
            self.ui.log_status("Uninstall process completed")