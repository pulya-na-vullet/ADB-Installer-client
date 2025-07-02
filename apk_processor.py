import subprocess

class APKProcessor:
    def __init__(self, ui):
        self.ui = ui
        self.AAPT_PATH = 'aapt'

    def process_apk_file(self, file_path):
        def update_ui():
            self.ui.apk_info_text.configure(state="normal")
            self.ui.apk_info_text.delete("1.0", "end")
            package_name = self.get_package_name(file_path)
            info = f"APK Path: {file_path}\n"
            if package_name:
                info += f"Package Name: {package_name}"
            self.ui.apk_info_text.insert("1.0", info)
            self.ui.apk_info_text.configure(state="disabled")
        self.ui.app.after(0, update_ui)

    def get_package_name(self, apk_path):
        try:
            result = subprocess.run(
                [self.AAPT_PATH, 'dump', 'badging', apk_path],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('package: name='):
                        return line.split("'")[1]
        except:
            return None