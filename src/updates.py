import requests
import platform
import os
import logging
from packaging import version
import sys
import subprocess

# Configure logging
logger = logging.getLogger(__name__)

class UpdateManager:
    """
    Manages application updates by checking a GitHub repository for new releases.
    """

    def __init__(self, current_version: str, repo_url: str):
        self.current_version = version.parse(current_version)
        self.repo_url = repo_url.replace("https://github.com/", "https://api.github.com/repos/")
        self.platform = platform.system().lower()

        # --- LÓGICA INFALÍVEL PARA ACHAR O EXECUTÁVEL ---
        # Quando compilado com Flet/PyInstaller, sys.frozen é True e sys.executable aponta pro arquivo real
        if getattr(sys, 'frozen', False):
            self.current_executable_path = os.path.abspath(sys.executable)
        else:
            self.current_executable_path = os.path.abspath(sys.argv[0])

        self.base_dir = os.path.dirname(self.current_executable_path)
        
        # Nomes dos arquivos de release no Github
        if self.platform == "windows":
            self.executable_name = "loteria-gerador.exe"
        else:
            self.executable_name = "loteria-gerador-linux"

    def _get_latest_release_data(self):
        try:
            api_url = f"{self.repo_url}/releases/latest"
            logger.info(f"Checking for updates at: {api_url}")
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching latest release data: {e}")
            return {"error": str(e)}

    def check_for_updates(self):
        release_data = self._get_latest_release_data()

        if release_data.get("error"):
            return {"update_available": False, "error": f"Could not connect to the update server: {release_data['error']}"}

        latest_version_str = release_data.get("tag_name", "0.0.0").lstrip("v")
        latest_version = version.parse(latest_version_str)

        if latest_version > self.current_version:
            logger.info(f"New version found: {latest_version}")
            download_url = None
            for asset in release_data.get("assets", []):
                if self.executable_name in asset.get("name", ""):
                    download_url = asset.get("browser_download_url")
                    break

            if not download_url:
                return {"update_available": False, "error": f"Update found, but no download file available for your platform ({self.platform})."}

            return {
                "update_available": True,
                "version": str(latest_version),
                "notes": release_data.get("body", "No release notes provided."),
                "download_url": download_url
            }
        else:
            logger.info("Application is up to date.")
            return {"update_available": False, "error": None}

    def download_and_install(self, download_url: str):
        try:
            update_filename = self.current_executable_path + ".new"
            logger.info(f"Downloading update to {update_filename}")

            response = requests.get(download_url, stream=True, timeout=60)
            response.raise_for_status()
            with open(update_filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("Download complete.")

            if self.platform != "windows":
                os.chmod(update_filename, 0o755)

            # --- CRIAÇÃO DOS SCRIPTS COM CAMINHOS ABSOLUTOS ---
            if self.platform == "windows":
                script_path = os.path.join(self.base_dir, "update.bat")
                script_content = f"""@echo off
echo Atualizando o Loterias Pro... aguarde.
timeout /t 3 /nobreak > nul
del /f /q "{self.current_executable_path}"
move /y "{update_filename}" "{self.current_executable_path}"
start "" "{self.current_executable_path}"
del "%~f0"
"""
            else:  # Linux/macOS
                script_path = os.path.join(self.base_dir, "update.sh")
                script_content = f"""#!/bin/bash
echo "Atualizando o Loterias Pro... aguarde."
sleep 3
rm -f "{self.current_executable_path}"
mv -f "{update_filename}" "{self.current_executable_path}"
chmod +x "{self.current_executable_path}"
nohup "{self.current_executable_path}" > /dev/null 2>&1 &
rm -f "$0"
"""

            with open(script_path, "w") as f:
                f.write(script_content)

            if self.platform != "windows":
                os.chmod(script_path, 0o755)

            logger.info(f"Executing updater script: {script_path}")
            
            # Executa o script desacoplado do processo atual
            if self.platform == "windows":
                subprocess.Popen([script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([script_path], start_new_session=True)

            return True

        except Exception as e:
            logger.error(f"An error occurred during update: {e}")
            return False