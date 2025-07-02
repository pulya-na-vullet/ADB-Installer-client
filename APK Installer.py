import os
import subprocess
import customtkinter as ctk
import threading
from tkinter import messagebox
from datetime import datetime
from functools import partial
from queue import Queue

class APKInstallerApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.setup_ui()
        
        self.apk_path = ""
        self.selected_packages = set()
        self.checkbox_vars = {}
        self.device_list = []
        self.package_list = []
        self.last_scan_time = 0
        self.scan_interval = 5
        
        # Для Windows укажите полный путь к aapt, если он не в PATH
        self.AAPT_PATH = 'aapt'  # Или r'C:\path\to\aapt.exe'
        
        self.ui_queue = Queue()
        self.scanning_active = True
        self.start_background_tasks()
        
    def setup_ui(self):
        self.app.title("APK Installer")
        self.app.geometry("1200x800")
        self.app.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.app.grid_columnconfigure(0, weight=1)
        self.app.grid_columnconfigure(1, weight=1)
        self.app.grid_rowconfigure(0, weight=1)
        
        # Left frame with packages list
        self.left_frame = ctk.CTkFrame(self.app)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.left_frame, text="Installed Packages", 
                    font=("Arial", 14)).pack(pady=5)
        
        self.packages_frame = ctk.CTkScrollableFrame(self.left_frame)
        self.packages_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Uninstall button
        self.uninstall_btn = ctk.CTkButton(
            self.left_frame, 
            text="Uninstall Selected", 
            command=self.uninstall_selected,
            fg_color="#8b2e2e",
            hover_color="#b33c3c"
        )
        self.uninstall_btn.pack(fill="x", pady=5)
        
        # Right frame with APK controls
        self.right_frame = ctk.CTkFrame(self.app)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.right_frame, text="APK Installer", 
                    font=("Arial", 14)).pack(pady=5)
        
        self.apk_info_text = ctk.CTkTextbox(self.right_frame, wrap="none")
        self.apk_info_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.select_apk_btn = ctk.CTkButton(
            self.right_frame, 
            text="Select APK File", 
            command=self.select_apk_file
        )
        self.select_apk_btn.pack(fill="x", pady=5)
        
        self.install_btn = ctk.CTkButton(
            self.right_frame, 
            text="Install APK", 
            command=self.install_apk,
            fg_color="#2e8b57"
        )
        self.install_btn.pack(fill="x", pady=5)
        
        # Status bar
        self.status_var = ctk.StringVar(value="Ready")
        self.status_bar = ctk.CTkLabel(self.app, textvariable=self.status_var, 
                                     anchor="w", height=20)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10)
        
    def on_close(self):
        """Handle application close event"""
        self.scanning_active = False
        if hasattr(self, 'scan_thread'):
            self.scan_thread.join(timeout=1)
        if hasattr(self, 'ui_thread'):
            self.ui_thread.join(timeout=1)
        self.app.destroy()
        
    def start_background_tasks(self):
        """Start background threads"""
        self.scan_thread = threading.Thread(
            target=self.background_scanner,
            daemon=True
        )
        self.scan_thread.start()
        
        self.ui_thread = threading.Thread(
            target=self.process_ui_queue,
            daemon=True
        )
        self.ui_thread.start()
        
        self.app.after(100, self.check_ui_updates)
    
    def background_scanner(self):
        """Background device and package scanner"""
        while self.scanning_active:
            try:
                current_time = datetime.now().timestamp()
                if current_time - self.last_scan_time >= self.scan_interval:
                    self.scan_devices()
                    self.last_scan_time = current_time
                
                threading.Event().wait(0.5)
                
            except Exception as e:
                self.ui_queue.put(("error", f"Scanner error: {str(e)}"))
    
    def scan_devices(self):
        """Scan for connected devices"""
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
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
            self.ui_queue.put(("error", "ADB timeout during devices scan"))
        except Exception as e:
            self.ui_queue.put(("error", f"Device scan error: {str(e)}"))
    
    def get_packages_info(self, force_update=False):
        """Get package information from devices"""
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
                        pkg_name = line.split(':')[-1]
                        packages.add(pkg_name)
            
            if force_update or packages != set(self.package_list):
                self.package_list = sorted(packages)
                self.ui_queue.put(("update_packages", self.package_list))
                
        except subprocess.TimeoutExpired:
            self.ui_queue.put(("error", "ADB timeout during packages scan"))
        except Exception as e:
            self.ui_queue.put(("error", f"Package scan error: {str(e)}"))
    
    def process_ui_queue(self):
        """Process UI update queue"""
        while self.scanning_active:
            try:
                item = self.ui_queue.get(timeout=1)
                if item[0] == "update_packages":
                    self.app.after(0, self.update_packages_display, item[1])
                elif item[0] == "error":
                    self.app.after(0, self.log_status, item[1])
                    
            except Exception:
                pass
    
    def check_ui_updates(self):
        """Check for UI updates periodically"""
        try:
            self.app.after(100, self.check_ui_updates)
        except Exception:
            pass
    
    def update_packages_display(self, packages):
        """Update the packages list display"""
        try:
            # Полностью очищаем текущий выбор
            self.selected_packages.clear()
            
            # Очищаем фрейм
            for widget in self.packages_frame.winfo_children():
                widget.destroy()
            
            self.checkbox_vars = {}
            
            # Добавляем чекбоксы для каждого пакета
            for pkg in packages:
                var = ctk.StringVar(value="off")  # Все чекбоксы по умолчанию выключены
                self.checkbox_vars[pkg] = var
                
                chk = ctk.CTkCheckBox(
                    self.packages_frame,
                    text=pkg,
                    variable=var,
                    onvalue="on",
                    offvalue="off",
                    command=partial(self.handle_checkbox_change, pkg, var)
                )
                chk.pack(anchor="w", padx=5, pady=2)
                
        except Exception as e:
            self.log_status(f"UI update error: {str(e)}")
    
    def handle_checkbox_change(self, package, var):
        """Обработчик изменения состояния чекбокса"""
        current_value = var.get()
        print(f"Чекбокс {package} изменил состояние на: {current_value}")
        
        if current_value == "on":
            self.selected_packages.add(package)
        else:
            if package in self.selected_packages:
                self.selected_packages.remove(package)
        
        print(f"Текущее количество выбранных пакетов: {len(self.selected_packages)}")
        print(f"Выбранные пакеты: {self.selected_packages}")
    
    def select_apk_file(self):
        """Select an APK file"""
        file_path = ctk.filedialog.askopenfilename(
            title="Select APK File",
            filetypes=[("APK files", "*.apk")]
        )
        
        if file_path:
            self.apk_path = file_path
            threading.Thread(
                target=self.process_apk_file,
                args=(file_path,),
                daemon=True
            ).start()
    
    def process_apk_file(self, file_path):
        """Упрощенная обработка APK файла"""
        def update_ui():
            self.apk_info_text.configure(state="normal")
            self.apk_info_text.delete("1.0", "end")
            
            package_name = self.get_package_name(file_path)
            info = f"APK Path: {file_path}\n"
            
            if package_name:
                info += f"Package Name: {package_name}"
                self.log_status(f"APK selected: {package_name}")
            else:
                info += "Package Name: (will install anyway)"
                self.log_status("APK selected (unknown package)")
            
            self.apk_info_text.insert("1.0", info)
            self.apk_info_text.configure(state="disabled")
        
        self.app.after(0, update_ui)
    
    def get_package_name(self, apk_path):
        """Упрощенный метод извлечения package name из APK"""
        try:
            # Пробуем использовать aapt (должен быть в PATH)
            result = subprocess.run(
                ['aapt', 'dump', 'badging', apk_path],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW  # Только для Windows
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('package: name='):
                        return line.split("'")[1]
            return None
        except:
            return None

    
    def check_aapt_available(self):
        """Проверяет доступность aapt в системе"""
        try:
            result = subprocess.run([self.AAPT_PATH, 'version'],
                                 capture_output=True,
                                 text=True,
                                 timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def install_apk(self):
        """Установка APK"""
        if not self.apk_path:
            messagebox.showerror("Error", "Please select an APK file first")
            return
            
        # Пропускаем проверку package name перед установкой
        threading.Thread(
            target=self._install_apk_thread,
            daemon=True
        ).start()
    
    def _install_apk_thread(self):
        """Thread for APK installation"""
        self.log_status("Starting installation...")
        
        try:
            for device in self.device_list:
                self.log_status(f"Installing on {device}...")
                result = subprocess.run(
                    ['adb', '-s', device, 'install', '-r', self.apk_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    self.log_status(f"Successfully installed on {device}")
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip()
                    self.log_status(f"Failed to install on {device}: {error_msg}")
            
            # Force immediate rescan after installation
            self.get_packages_info(force_update=True)
                    
        except Exception as e:
            self.log_status(f"Installation error: {str(e)}")
        finally:
            self.log_status("Installation process completed")
    
    def uninstall_selected(self):
        """Uninstall selected packages"""
        print(f"Перед удалением выбрано пакетов: {len(self.selected_packages)}")
        
        if not self.selected_packages:
            messagebox.showwarning("Ошибка", "Выберите пакеты для удаления (поставьте галочки)")
            return
            
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Удалить {len(self.selected_packages)} пакет(ов)?"
        )
        if not confirm:
            return
            
        # Создаем копию списка для удаления
        packages_to_uninstall = list(self.selected_packages)
        threading.Thread(
            target=self._uninstall_thread,
            args=(packages_to_uninstall,),
            daemon=True
        ).start()
    
    def _uninstall_thread(self, packages):
        """Thread for package uninstallation"""
        self.log_status(f"Starting uninstall of {len(packages)} packages...")
        
        try:
            success_count = 0
            fail_count = 0
            
            for device in self.device_list:
                for package in packages:
                    self.log_status(f"Uninstalling {package} from {device}...")
                    result = subprocess.run(
                        ['adb', '-s', device, 'uninstall', package],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        self.log_status(f"Successfully uninstalled {package}")
                        success_count += 1
                    else:
                        error_msg = result.stderr.strip() or result.stdout.strip()
                        self.log_status(f"Failed to uninstall {package}: {error_msg}")
                        fail_count += 1
            
            # Force immediate rescan after uninstallation
            self.get_packages_info(force_update=True)
            
            # Clear selection and update checkboxes
            self.selected_packages.clear()
            for var in self.checkbox_vars.values():
                var.set("off")
            
            self.log_status(
                f"Uninstall complete. Success: {success_count}, Failed: {fail_count}"
            )
                        
        except Exception as e:
            self.log_status(f"Uninstall error: {str(e)}")
        finally:
            self.log_status("Uninstall process completed")
    
    def log_status(self, message):
        """Log status messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"[{timestamp}] {message}")
    
    def run(self):
        """Run the application"""
        self.app.mainloop()

if __name__ == "__main__":
    app = APKInstallerApp()
    app.run()