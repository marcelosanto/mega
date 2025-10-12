import requests
import platform
import os
import shutil
import tempfile
import logging
from packaging import version
import sys

# Configure logging
logger = logging.getLogger(__name__)


class UpdateManager:
    """
    Manages application updates by checking a GitHub repository for new releases.
    """

    def __init__(self, current_version: str, repo_url: str):
        self.current_version = version.parse(current_version)
        self.repo_url = repo_url.replace(
            "https://github.com/", "https://api.github.com/repos/")
        self.platform = platform.system().lower()

        # --- NOMES AJUSTADOS PARA COMPATIBILIDADE ---
        if self.platform == "windows":
            self.executable_name = "loteria-gerador.exe"
        else:  # linux, darwin (macOS)
            self.executable_name = "loteria-gerador-linux"

        # Lógica para encontrar o caminho do executável original (e não o temporário do PyInstaller)
        self.current_executable_path = os.path.join(
            os.getcwd(), self.executable_name)
        # Uma verificação extra para o caso de o nome do arquivo ser diferente de sys.argv[0]
        if not os.path.exists(self.current_executable_path) and hasattr(sys, 'argv'):
            self.current_executable_path = os.path.join(
                os.getcwd(), os.path.basename(sys.argv[0]))

    # ... (o resto da sua classe não precisa de alterações) ...

    def _get_latest_release_data(self):
        """Fetches the latest release data from the GitHub API."""
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
        """
        Checks for a new version and returns a dictionary with the result.
        """
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
        """
        Downloads the new executable, creates an updater script,
        and returns instructions for the UI to exit the application.
        """
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

            if self.platform == "windows":
                script_path = os.path.join(os.getcwd(), "update.bat")
                script_content = f"""
@echo off
echo Updating application... please wait.
timeout /t 2 /nobreak > nul
del "{self.current_executable_path}"
move "{update_filename}" "{self.current_executable_path}"
start "" "{self.current_executable_path}"
del "{script_path}"
"""
            else:  # Linux/macOS
                script_path = os.path.join(os.getcwd(), "update.sh")
                script_content = f"""
#!/bin/bash
echo "Updating application... please wait."
sleep 2
rm "{self.current_executable_path}"
mv "{update_filename}" "{self.current_executable_path}"
chmod +x "{self.current_executable_path}"
nohup "{self.current_executable_path}" &
rm -- "$0"
"""

            with open(script_path, "w") as f:
                f.write(script_content)

            if self.platform != "windows":
                os.chmod(script_path, 0o755)

            import subprocess
            logger.info(f"Executing updater script: {script_path}")
            if self.platform == "windows":
                subprocess.Popen(
                    [script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([script_path], preexec_fn=os.setpgrp)

            return {"success": True, "error": None, "action": "restart"}

        except Exception as e:
            logger.error(f"An error occurred during update: {e}")
            return {"success": False, "error": f"An unexpected error occurred: {e}", "action": None}
