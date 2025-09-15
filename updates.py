import requests
import platform
import os
import shutil
import tempfile
import logging
from packaging import version

# Configure logging
logger = logging.getLogger(__name__)


class UpdateManager:
    """
    Manages application updates by checking a GitHub repository for new releases.
    This class is UI-agnostic and returns structured data (dictionaries)
    to be interpreted by the UI layer (e.g., Flet).
    """

    def __init__(self, current_version: str, repo_url: str):
        self.current_version = version.parse(current_version)
        self.repo_url = repo_url.replace(
            "https://github.com/", "https://api.github.com/repos/")
        self.platform = platform.system().lower()

        # Determine the expected executable name based on the OS
        if self.platform == "windows":
            self.executable_name = "loteria-gerador.exe"
            self.current_executable_path = os.path.realpath(
                os.path.join(os.getcwd(), self.executable_name))
        else:  # linux, darwin (macOS)
            self.executable_name = "loteria-gerador-linux"
            self.current_executable_path = os.path.realpath(
                os.path.join(os.getcwd(), self.executable_name))

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
        Downloads the new executable and replaces the current one.
        Returns a dictionary indicating success or failure.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_executable_path = os.path.join(temp_dir, self.executable_name)

            # 1. Download the file
            try:
                logger.info(
                    f"Downloading from {download_url} to {temp_executable_path}")
                response = requests.get(download_url, stream=True, timeout=30)
                response.raise_for_status()
                with open(temp_executable_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info("Download complete.")
            except requests.RequestException as e:
                logger.error(f"Failed to download file: {e}")
                return {"success": False, "error": f"Download failed: {e}"}

            # Make executable on Linux/macOS
            if self.platform != "windows":
                os.chmod(temp_executable_path, 0o755)

            # 2. Replace the old executable
            try:
                logger.info(
                    f"Replacing old executable at {self.current_executable_path}")
                # Use shutil.move for robustness, especially across different filesystems
                shutil.move(temp_executable_path, self.current_executable_path)
                logger.info("Executable replaced successfully.")
                return {"success": True, "error": None}
            except (OSError, shutil.Error) as e:
                logger.error(f"Failed to replace executable: {e}")
                return {"success": False, "error": f"Could not replace the application file. Please check permissions. Error: {e}"}
