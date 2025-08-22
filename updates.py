import requests
import platform
import os
import shutil
import tempfile
import subprocess
import tkinter.messagebox as messagebox
from utils import get_resource_path


class UpdateManager:
    def __init__(self, current_version, repo_url):
        self.current_version = current_version
        self.repo_url = repo_url
        self.temp_dir = tempfile.mkdtemp()
        self.platform = platform.system().lower()
        self.executable_name = "loteria-gerador.exe" if self.platform == "windows" else "loteria-gerador-linux"

    def get_latest_version(self):
        try:
            response = requests.get(
                f"{self.repo_url}/releases/latest", timeout=10)
            response.raise_for_status()
            latest_release = response.json()
            latest_version = latest_release["tag_name"].lstrip("v")
            return latest_version
        except requests.RequestException as e:
            print(f"Erro ao verificar versão mais recente: {e}")
            return None

    def get_download_url(self, latest_version):
        try:
            response = requests.get(
                f"{self.repo_url}/releases/latest", timeout=10)
            response.raise_for_status()
            release_data = response.json()
            for asset in release_data.get("assets", []):
                if self.executable_name in asset["name"]:
                    return asset["browser_download_url"]
            print(
                f"Asset para {self.executable_name} não encontrado na release.")
            return None
        except requests.RequestException as e:
            print(f"Erro ao obter URL de download: {e}")
            return None

    def download_file(self, url, dest_path):
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"Arquivo baixado para {dest_path}")
            return True
        except requests.RequestException as e:
            print(f"Erro ao baixar arquivo: {e}")
            return False

    def replace_executable(self, new_executable_path):
        current_executable = get_resource_path(self.executable_name)
        try:
            if os.path.exists(current_executable):
                # Garante permissões no Linux
                os.chmod(current_executable, 0o755)
            temp_executable = os.path.join(self.temp_dir, self.executable_name)
            shutil.move(new_executable_path, temp_executable)
            shutil.copy2(temp_executable, current_executable)
            if self.platform != "windows":
                # Garante permissões no Linux
                os.chmod(current_executable, 0o755)
            print(f"Executável substituído: {current_executable}")
            return True
        except (OSError, shutil.Error) as e:
            print(f"Erro ao substituir executável: {e}")
            return False

    def check_for_updates(self, show_message=True):
        latest_version = self.get_latest_version()
        if not latest_version:
            if show_message:
                messagebox.showerror(
                    "❌ Erro", "Não foi possível verificar atualizações. Verifique sua conexão com a internet.")
            return False
        if self._is_newer_version(latest_version):
            if show_message:
                messagebox.showinfo(
                    "🔄 Nova Versão", f"Nova versão {latest_version} disponível! Iniciando atualização...")
            download_url = self.get_download_url(latest_version)
            if not download_url:
                if show_message:
                    messagebox.showerror(
                        "❌ Erro", "Não foi possível encontrar o arquivo de atualização para sua plataforma.")
                return False
            temp_executable = os.path.join(self.temp_dir, self.executable_name)
            if self.download_file(download_url, temp_executable):
                if self.replace_executable(temp_executable):
                    if show_message:
                        messagebox.showinfo(
                            "✅ Sucesso", "Atualização concluída! Reinicie o aplicativo.")
                    return True
                else:
                    if show_message:
                        messagebox.showerror(
                            "❌ Erro", "Falha ao substituir o executável. Verifique permissões ou se o aplicativo está em uso.")
            else:
                if show_message:
                    messagebox.showerror(
                        "❌ Erro", "Falha ao baixar a nova versão.")
            return False
        else:
            if show_message:
                messagebox.showinfo(
                    "ℹ️ Info", "Você já está na versão mais recente.")
            return False

    def _is_newer_version(self, latest_version):
        try:
            current_parts = [int(x) for x in self.current_version.split(".")]
            latest_parts = [int(x) for x in latest_version.split(".")]
            return latest_parts > current_parts
        except ValueError:
            print("Erro ao comparar versões: formato inválido.")
            return False
