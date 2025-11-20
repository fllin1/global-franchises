# -*- coding: utf-8 -*-
"""
File Manager Functions 101. The universal pain.
"""

from datetime import date
import hashlib
from pathlib import Path
import re
import shutil
from typing import List

from src.config import EXTERNAL_DATA_DIR, PROJ_ROOT
from src.data.storage.storage_client import StorageClient

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ExtractFileManager:
    """
    A class to manage file extraction operations.

    From the External Data Directory, it can extract the scrapped HTML files
    to the External Data Directory, and create a log file with the date of the scraping.

    To keep track of the latest version of the data, it also copies the files
    to the External Latest Data Directory, called "EXTERNAL_DATA_DIR/latest/".

    Structure:
    - EXTERNAL_DATA_DIR/
        - logs/
        - latest/
        - YYYY-MM-DD/
            - file1.html
            - file2.html
    """

    def __init__(self, external_data_dir: Path = EXTERNAL_DATA_DIR):
        """
        Initializes the ExtractFileManager with the specified directories.
        """
        self.today_str = date.today().isoformat()

        self.external_data_dir = external_data_dir
        self.logs_dir = self.external_data_dir / "logs"
        self.modified_dir = self.external_data_dir / "modified"

    def get_html_files(self, date_str: str) -> List[Path]:
        """
        Get all HTML files from the external data directory.

        Args:
            date_str (str): The date in 'YYYY-MM-DD' format to filter files,
                or 'new" to get new files.

        Returns:
            List[Path]: A list of HTML file paths.
        """
        data_dir = self.external_data_dir / date_str
        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory {data_dir} does not exist.")
        data_paths = [path.relative_to(PROJ_ROOT) for path in data_dir.glob("*.html")]
        return data_paths

    def get_storage_files(self, prefix: str) -> List[dict]:
        """
        Get all files from Supabase Storage with a given prefix.

        Args:
            prefix (str): The prefix (folder) to list files from.

        Returns:
            List[dict]: A list of file objects from Supabase Storage.
        """
        client = StorageClient()
        return client.list_files(prefix)

    def create_log_file(self, updates: List[str], log_path: Path = None) -> Path:
        """
        Create a log file in the raw data directory. It contains the data that was updated
        at the date of the last scraping.

        Args:
            updates (List[str]): A list of updates to log.
            log_path (Path, optional): The path to save the log file.
                If None, uses the default path.

        Returns:
            Path: The path to the created log file.
        """
        if log_path is None:
            log_path = self.logs_dir / f"{self.today_str}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(log_path, "w", encoding="utf-8") as file_handle:
            for item in updates:
                file_handle.write(f"{item}\n")

        return log_path

    def read_log_file(self, log_path: Path = None) -> List[str]:
        """
        Read the latest log file and return its contents as a dictionary.

        Args:
            log_path (Path, optional): The path to the log file. If None, reads

        Returns:
            List[str]: A list with log entries.
        """
        if log_path is None:
            log_files = list(self.logs_dir.glob("*.log"))
        else:
            log_files = [log_path]
        if not log_files:
            return []

        latest_log = max(log_files, key=lambda f: f.stem)
        history = []
        with open(latest_log, "r", encoding="utf-8") as f:
            for line in f:
                history.append(line.strip())
        return history

    def copy_modified_external_files(self) -> None:
        """
        Get all modified files in the external data directory.
        """
        # Clean up the modified directory
        modified_files = []
        if self.modified_dir.exists() and self.modified_dir.is_dir():
            shutil.rmtree(self.modified_dir)
        self.modified_dir.mkdir(parents=True, exist_ok=True)

        # The latest version of the data
        html_date_folders = [
            d for d in self.external_data_dir.iterdir() if d.is_dir() and DATE_RE.match(d.name)
        ]

        # Handle the case of the first run
        if not html_date_folders:
            # If no previous data exists, copy all new files in the modified directory
            for folder in self.external_data_dir.iterdir():
                if folder.is_dir() and folder.name.startswith("new_"):
                    for file in folder.glob("*.html"):
                        shutil.copy(file, self.modified_dir / file.name)
                        modified_files.append(file.relative_to(PROJ_ROOT))
            self.create_log_file(modified_files)
            return  # Exit the method early

        latest_html_folder = max(html_date_folders, key=lambda d: d.name)
        latest_date_str = latest_html_folder.name
        latest_data_paths = self.get_html_files(date_str=latest_date_str)
        latest_data_names = [file.name for file in latest_data_paths]

        # The new data which was just scraped
        for folder in self.external_data_dir.iterdir():
            if folder.is_dir() and folder.name.startswith("new_"):
                new_data_dir = folder
                break
        else:
            raise FileNotFoundError("No new data directory found in the external data directory.")
        new_data_paths = list(new_data_dir.glob("*.html"))

        for file in new_data_paths:
            new_file_name = file.name

            # If it's a new page on franserve
            if new_file_name not in latest_data_names:
                shutil.copy(file, self.modified_dir / new_file_name)
                modified_files.append(file.relative_to(PROJ_ROOT))
                continue

            # If the file already exists in the latest scraped data
            # We compare it with the new one
            new_data_hash = self.checksum(file)
            latest_data_hash = self.checksum(latest_html_folder / new_file_name)

            if new_data_hash != latest_data_hash:
                shutil.copy(file, self.modified_dir / new_file_name)
                modified_files.append(file.relative_to(PROJ_ROOT))

        # Update the log file with the new history
        self.create_log_file(modified_files)

    @staticmethod
    def checksum(path: Path) -> str:
        """
        Calculate the SHA-256 checksum of a file.
        Args:
            path (Path): The path to the file.
        Returns:
            str: The SHA-256 checksum of the file.
        """
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
