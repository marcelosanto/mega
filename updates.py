import os
import sys
import requests
import tempfile
import shutil
import subprocess
import stat
from tkinter import messagebox


class UpdateManager:
    def __init__(self, version, update_base_url, root):
        self.version = version
        self.update_base_url = update_base_url
        self.root = root

    def get_resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        else:
            return os.path.join(os.path.dirname(__file__), relative_path)

    def check_for_updates(self, show_message=True):
        try:
            response = requests.get(
                f"{self.update_base_url}version.txt", timeout=5)
            response.raise_for_status()
            latest_version = response.text.strip()
            if latest_version > self.version:
                if messagebox.askyesno("📥 Atualização Disponível", f"Versão {latest_version} disponível (atual: {self.version}). Deseja atualizar agora?"):
                    self.download_and_update(latest_version)
            elif show_message:
                messagebox.showinfo(
                    "✅ Atualizado", "Você está usando a versão mais recente!")
        except requests.RequestException as e:
            if show_message:
                messagebox.showwarning(
                    "⚠️ Atenção", f"Erro ao verificar atualizações: {e}")

    def download_and_update(self, latest_version):
        try:
            executable_name = 'loteria-gerador.exe' if sys.platform.startswith(
                'win') else 'loteria-gerador-linux'
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"{executable_name}.new")
            response = requests.get(
                f"{self.update_base_url}{executable_name}", stream=True)
            response.raise_for_status()
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            if not sys.platform.startswith('win'):
                os.chmod(temp_path, stat.S_IRWXU | stat.S_IRWXG |
                         stat.S_IROTH | stat.S_IXOTH)
            current_path = sys.executable
            shutil.move(temp_path, current_path)
            subprocess.Popen([current_path])
            self.root.quit()
        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao atualizar: {e}")
