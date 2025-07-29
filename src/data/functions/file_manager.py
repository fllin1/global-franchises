# -*- coding: utf-8 -*-
"""
File Manager Functions 101. The universal pain.
"""

from datetime import date
from pathlib import Path
import shutil
from typing import Dict, List

from src.config import EXTERNAL_DATA_DIR, PROJ_ROOT, RAW_DATA_DIR


class ExtractFileManager:
    """
    A class to manage file extraction operations.
    """

    def __init__(
        self, external_data_dir: Path = EXTERNAL_DATA_DIR, raw_data_dir: Path = RAW_DATA_DIR
    ):
        self.external_data_dir = external_data_dir
        self.external_logs_dir = self.external_data_dir / "logs"
        self.external_latest_data_dir = self.external_data_dir / "latest"
        self.raw_data_dir = raw_data_dir

    def get_html_files(self, date_str: str) -> List[Path]:
        """
        Get all HTML files from the external data directory.

        Args:
            date_str (str): The date in 'YYYY-MM-DD' format to filter files.

        Returns:
            List[Path]: A list of HTML file paths.
        """
        data_dir = self.external_data_dir / date_str
        if not data_dir.exists():
            raise FileNotFoundError(f"Data directory {data_dir} does not exist.")
        data_paths = [path.relative_to(PROJ_ROOT) for path in data_dir.glob("*.html")]
        return data_paths

    def get_json_files(self) -> List[Path]:
        """
        Get all JSON files from the raw data directory.

        Returns:
            List[Path]: A list of JSON file paths.
        """
        return list(self.raw_data_dir.glob("*.json"))

    def create_log_file(self, updates: Dict[str, str]) -> Path:
        """
        Create a log file in the raw data directory. It contains the data that was updated
        at the date of the last scraping.

        Args:
            updates (Dict[str, str]): A dictionary of updates to log.
                {"name_of_html_file": "date_of_html_file"}

        Returns:
            Path: The path to the created log file.
        """
        today_str = date.today().isoformat()
        log_file = self.external_logs_dir / f"{today_str}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "w", encoding="utf-8") as f:
            for key, value in updates.items():
                f.write(f"{key}: {value}\n")

        return log_file

    def read_log_file(self) -> Dict[str, str]:
        """
        Read the latest log file and return its contents as a dictionary.

        Returns:
            Dict[str, str]: A dictionary with log entries.
        """
        log_files = list(self.external_logs_dir.glob("*.log"))
        if not log_files:
            return {}

        latest_log = max(log_files, key=lambda f: f.stem)
        history = {}
        with open(latest_log, "r", encoding="utf-8") as f:
            for line in f:
                if ": " in line:
                    key, value = line.strip().split(": ", 1)
                    history[key] = value

        return history

    def modified_external_files(self):
        """
        Get all modified files in the external data directory.
        """
        logs = self.read_log_file()
        modified_files = []

        # The new data
        html_folders = [d for d in self.external_data_dir.iterdir() if d.is_dir()]
        new_html_folder = max(html_folders, key=lambda d: d.name)
        new_date_str = new_html_folder.name
        new_data_dir = self.get_html_files(date_str=new_date_str)

        # The latest version data
        self.external_latest_data_dir.mkdir(parents=True, exist_ok=True)

        for file in new_data_dir.glob("*.html"):
            new_file_name = file.name

            # If it's a new page on franserve
            if new_file_name not in logs:
                modified_files.append(file)
                shutil.copy(file, self.external_latest_data_dir / new_file_name)
                logs[new_file_name] = new_date_str
                continue

            # If the file already exists in the latest version
            # We read it and compare with the new one
            with open(file, "r", encoding="utf-8") as f:
                new_data = f.read()
            with open(self.external_latest_data_dir / new_file_name, "r", encoding="utf-8") as f:
                latest_data = f.read()

            if new_data != latest_data:
                modified_files.append(file)
                shutil.copy(file, self.external_latest_data_dir / new_file_name)
                logs[new_file_name] = new_date_str

        # Update the log file with the new history
        self.create_log_file(logs)
