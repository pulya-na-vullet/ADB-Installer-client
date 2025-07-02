import customtkinter as ctk
import threading
from tkinter import messagebox
from datetime import datetime
from functools import partial
from queue import Queue
from adb_controller import ADBController
from apk_processor import APKProcessor

class APKInstallerApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.adb = ADBController(self)
        self.apk_processor = APKProcessor(self)
        self.setup_ui()
        self.apk_path = ""
        self.selected_packages = set()
        self.checkbox_vars = {}
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
        self.left_frame = ctk.CTkFrame(self.app)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.left_frame, text="Installed Packages", font=("Arial", 14)).pack(pady=5)
        self.packages_frame = ctk.CTkScrollableFrame(self.left_frame)
        self.packages_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.uninstall_btn = ctk.CTkButton(
            self.left_frame, 
            text="Uninstall Selected", 
            command=self.uninstall_selected,
            fg_color="#8b2e2e",
            hover_color="#b33c3c"
        )
        self.uninstall_btn.pack(fill="x", pady=5)

        self.right_frame = ctk.CTkFrame(self.app)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.right_frame, text="APK Installer", font=("Arial", 14)).pack(pady=5)
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

        self.status_var = ctk.StringVar(value="Ready")
        self.status_bar = ctk.CTkLabel(self.app, textvariable=self.status_var, 
                                     anchor="w", height=20)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10)

    def on_close(self):
        self.scanning_active = False
        if hasattr(self, 'scan_thread'):
            self.scan_thread.join(timeout=1)
        if hasattr(self, 'ui_thread'):
            self.ui_thread.join(timeout=1)
        self.app.destroy()

    def start_background_tasks(self):
        self.scan_thread = threading.Thread(target=self.adb.background_scanner, daemon=True)
        self.scan_thread.start()
        self.ui_thread = threading.Thread(target=self.process_ui_queue, daemon=True)
        self.ui_thread.start()
        self.app.after(100, self.check_ui_updates)

    def process_ui_queue(self):
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
        try:
            self.app.after(100, self.check_ui_updates)
        except Exception:
            pass

    def update_packages_display(self, packages):
        try:
            self.selected_packages.clear()
            for widget in self.packages_frame.winfo_children():
                widget.destroy()
            
            self.checkbox_vars = {}
            for pkg in packages:
                var = ctk.StringVar(value="off")
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
        if var.get() == "on":
            self.selected_packages.add(package)
        elif package in self.selected_packages:
            self.selected_packages.remove(package)

    def select_apk_file(self):
        file_path = ctk.filedialog.askopenfilename(
            title="Select APK File",
            filetypes=[("APK files", "*.apk")]
        )
        if file_path:
            self.apk_path = file_path
            threading.Thread(target=self.apk_processor.process_apk_file, args=(file_path,), daemon=True).start()

    def install_apk(self):
        if not self.apk_path:
            messagebox.showerror("Error", "Please select an APK file first")
            return
        threading.Thread(target=self.adb.install_apk_thread, args=(self.apk_path,), daemon=True).start()

    def uninstall_selected(self):
        if not self.selected_packages:
            messagebox.showwarning("Error", "Select packages to uninstall")
            return
            
        confirm = messagebox.askyesno("Confirm", f"Uninstall {len(self.selected_packages)} packages?")
        if not confirm:
            return
            
        threading.Thread(
            target=self.adb.uninstall_thread,
            args=(list(self.selected_packages),),
            daemon=True
        ).start()

    def log_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"[{timestamp}] {message}")

    def run(self):
        self.app.mainloop()