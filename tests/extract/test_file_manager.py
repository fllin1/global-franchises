# -- coding: utf-8 -*-
"""Test cases for the ExtractFileManager class.
This module contains unit tests for the ExtractFileManager class,
which manages file operations related to data extraction.
"""

from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from src.data.functions.file_manager import ExtractFileManager


class TestExtractFileManager(unittest.TestCase):
    """Unit tests for the ExtractFileManager class."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.test_dir = Path("test_temp_data").resolve()  # Use resolve for an absolute path
        self.test_proj_root = self.test_dir  # The "project root" for our test

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True)

    def tearDown(self):
        """Clean up the temporary directory after tests."""
        shutil.rmtree(self.test_dir)

    def test_create_and_read_log_file(self):
        """Tests creating and reading a log file."""
        fm = ExtractFileManager(external_data_dir=self.test_dir)
        updates = ["path/to/file1.html", "path/to/file2.html"]
        # Assuming you fixed the bug in the source file
        log_path = fm.create_log_file(updates)
        self.assertTrue(log_path.exists())
        read_content = fm.read_log_file()
        self.assertEqual(read_content, updates)

    def test_read_latest_log_file(self):
        """Tests that the correct (latest) log file is read when multiple exist."""
        fm = ExtractFileManager(external_data_dir=self.test_dir)
        logs_dir = self.test_dir / "logs"
        logs_dir.mkdir()

        (logs_dir / "2025-07-30.log").write_text("old_file.html\n")
        (logs_dir / "2025-07-31.log").write_text("new_file.html\n")

        fm.today_str = "2025-07-31"

        read_content = fm.read_log_file()
        self.assertEqual(read_content, ["new_file.html"])

    def test_copy_modified_files_first_run(self):
        """
        Tests the behavior when no previous data exists (first run).
        """
        # Use the 'with' statement to patch PROJ_ROOT just for this test
        with patch("src.data.functions.file_manager.PROJ_ROOT", self.test_proj_root):
            fm = ExtractFileManager(external_data_dir=self.test_dir)

            new_data_dir = self.test_dir / f"new_{fm.today_str}"
            new_data_dir.mkdir()
            (new_data_dir / "file1.html").write_text("data1")
            (new_data_dir / "file2.html").write_text("data2")

            # This call will now use the patched PROJ_ROOT
            fm.copy_modified_external_files()

            modified_dir = self.test_dir / "modified"
            self.assertTrue(modified_dir.exists())
            self.assertTrue((modified_dir / "file1.html").exists())
            self.assertTrue((modified_dir / "file2.html").exists())

    def test_copy_modified_files_subsequent_run(self):
        """
        Tests detecting new, modified, and unchanged files on a subsequent run.
        """
        # Use the 'with' statement to patch PROJ_ROOT just for this test
        with patch("src.data.functions.file_manager.PROJ_ROOT", self.test_proj_root):
            fm = ExtractFileManager(external_data_dir=self.test_dir)

            latest_dir = self.test_dir / "2025-07-30"
            latest_dir.mkdir()
            (latest_dir / "unchanged.html").write_text("same content")
            (latest_dir / "modified.html").write_text("old content")

            new_dir = self.test_dir / f"new_{fm.today_str}"
            new_dir.mkdir()
            (new_dir / "unchanged.html").write_text("same content")
            (new_dir / "modified.html").write_text("new content")
            (new_dir / "new_file.html").write_text("new file data")

            # This call will also use the patched PROJ_ROOT
            fm.copy_modified_external_files()

            modified_dir = self.test_dir / "modified"
            self.assertTrue(modified_dir.exists())
            self.assertTrue((modified_dir / "modified.html").exists())
            self.assertTrue((modified_dir / "new_file.html").exists())
            self.assertFalse((modified_dir / "unchanged.html").exists())


if __name__ == "__main__":
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
