# -*- coding: utf-8 -*-
"""
Config for Gemini API batch mode.
"""

# Batch job settings
DEFAULT_POLL_INTERVAL = 300  # 5 minutes
DEFAULT_MAX_WAIT_TIME = 86400  # 24 hours
MAX_BATCH_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# Batch size settings
DEFAULT_BATCH_SIZE = None  # None = process all files in one batch
MAX_FILES_PER_BATCH = 20  # Recommended maximum for performance

# Job naming templates
DATA_EXTRACTION_JOB_NAME = "franchise_data_extraction_batch{batch_num}_{count}_files"
KEYWORDS_EXTRACTION_JOB_NAME = "keywords_extraction_batch{batch_num}_{count}_files"
