# -*- coding: utf-8 -*-
"""
Generate franchise data from HTML using Gemini API in batch mode.

This module processes multiple HTML files simultaneously using the Gemini API
batch mode for cost-effective and efficient processing.
"""

import json
from pathlib import Path
from datetime import date
import json
from pathlib import Path
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from loguru import logger

from src.api.config.genai_gemini_config import (
    CLIENT,
    MODEL_FLASH_LITE,
    get_generate_content_config_franserve_data,
)
from src.api.genai_gemini_batch import (
    create_batch_file,
    create_batch_request,
    download_batch_results,
    monitor_batch_job,
    process_batch_workflow,
    split_into_batches,
    submit_batch_job,
)
from src.config import CONFIG_DIR, RAW_DATA_DIR
from src.data.franserve.html_to_prompt import (
    create_gemini_parts,
    format_html_for_llm,
)
from src.data.storage.storage_client import StorageClient


def create_franchise_data_batch_requests(
    storage_files: List[str], prompt: str, storage_client: StorageClient
) -> List[Dict]:
    """
    Create batch requests for all HTML files from Storage.

    Args:
        storage_files: List of HTML file paths in Storage to process
        prompt: The prompt template for franchise data extraction
        storage_client: StorageClient instance

    Returns:
        List of batch request dictionaries
    """
    batch_requests = []

    for file_path in storage_files:
        file_name = file_path.split("/")[-1]
        logger.debug(f"Preparing batch request for {file_name}")

        try:
            # Read and process HTML from Storage
            html_content = storage_client.download_html(file_path)

            # Format HTML for LLM
            formatted_html = format_html_for_llm(html_content)

            # Create parts
            parts = create_gemini_parts(
                prompt=prompt,
                formatted_html=formatted_html,
            )

            # Create batch request
            # Use filename without extension as key, ensuring unique keys if files are from different folders
            request_key = Path(file_name).stem

            batch_request = create_batch_request(
                key=request_key,
                parts=parts,
                generate_content_config=get_generate_content_config_franserve_data(seed=0),
            )

            batch_requests.append(batch_request)
        except Exception as e:
            logger.error(f"Error preparing request for {file_path}: {e}")

    logger.info(f"Created {len(batch_requests)} batch requests")
    return batch_requests


def process_batch_results(
    results: Dict[str, Dict], storage_files: List[str], storage_client: StorageClient
) -> Dict[str, str]:
    """
    Process batch results and save individual JSON files.

    Args:
        results: Dictionary mapping request keys to API responses
        storage_files: Original list of HTML file paths in Storage
        storage_client: StorageClient instance

    Returns:
        Dictionary mapping keys to processing status
    """
    # Create lookup for HTML file paths by stem (key)
    # storage_files contains full paths like "2025-01-01/abc.html"
    # We assume keys are stems like "abc"
    html_files_by_key = {Path(f).stem: f for f in storage_files}

    processing_status = {}
    output_dir = RAW_DATA_DIR / "franserve"
    output_dir.mkdir(parents=True, exist_ok=True)

    for request_key, response in results.items():
        try:
            # Get the original HTML file path
            html_file_path = html_files_by_key.get(request_key)
            if not html_file_path:
                logger.error(f"Could not find HTML file path for key: {request_key}")
                processing_status[request_key] = "error_no_html_file"
                continue

            # Extract response text and clean it
            response_text = (
                response.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            if not response_text:
                logger.error(f"No response text for {request_key}")
                processing_status[request_key] = "error_no_response"
                continue

            # Clean and parse JSON response
            response_text = response_text.replace("```json", "").replace("```", "").strip()

            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {request_key}: {e}")
                processing_status[request_key] = "error_json_decode"
                continue

            # Extract source_id from original HTML in Storage
            try:
                html_content = storage_client.download_html(html_file_path)
                soup = BeautifulSoup(html_content, "html.parser")
                fran_id_tag = soup.find("input", {"name": "ZorID"})

                if fran_id_tag and fran_id_tag.get("value"):
                    response_json["source_id"] = int(fran_id_tag["value"])
                else:
                    logger.warning(f"Could not extract source_id for {request_key}")
            except Exception as e:
                logger.error(f"Error extracting source_id for {request_key}: {e}")

            # Save to JSON file
            output_file = output_dir / f"{request_key}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(response_json, f, indent=4)

            logger.success(f"Processed {request_key} -> {output_file}")
            processing_status[request_key] = "success"

        except Exception as e:
            logger.error(f"Error processing {request_key}: {e}")
            processing_status[request_key] = f"error_{type(e).__name__}"

    return processing_status


def main_batch(
    batch_size: Optional[int] = None,
    poll_interval: int = 300,  # 5 minutes
    max_wait_time: int = 86400,  # 24 hours
):
    """
    Main function to run the franchise data extraction in batch mode from Storage.

    Args:
        batch_size: Number of files per batch. None = process all files in one batch
        poll_interval: How often to check batch job status (seconds)
        max_wait_time: Maximum time to wait for batch completion (seconds)
    """
    # Load prompt
    prompt_franserve_data = (CONFIG_DIR / "franserve" / "data_prompt.txt").read_text()

    # Initialize Storage Client
    storage_client = StorageClient()
    today_prefix = date.today().isoformat()
    
    # List files from Storage (defaulting to today's folder for now)
    storage_files_objs = storage_client.list_files(today_prefix)
    
    # Convert to full paths
    storage_files = []
    for f in storage_files_objs:
        name = f.get("name")
        if name and name.endswith(".html"):
            storage_files.append(f"{today_prefix}/{name}")

    if not storage_files:
        logger.warning(f"No HTML files found in Storage ({today_prefix}) to process.")
        return

    # Split files into batches
    file_batches = split_into_batches(storage_files, batch_size)

    if batch_size:
        logger.info(f"Batch size: {batch_size} files per batch")

    all_processing_status = {}

    # Process each batch
    for batch_num, file_batch in enumerate(file_batches, 1):
        logger.info(f"Processing batch {batch_num}/{len(file_batches)} ({len(file_batch)} files)")

        # Create batch requests for this batch
        batch_requests = create_franchise_data_batch_requests(
            file_batch, prompt_franserve_data, storage_client
        )

        # Set up batch job
        job_name = f"franchise_data_extraction_batch{batch_num}_{len(batch_requests)}_files"
        results_dir = RAW_DATA_DIR / "batch_results" / "franchise_data"

        logger.info(f"Starting batch job: {job_name}")

        # Process batch workflow
        results = process_batch_workflow(
            client=CLIENT,
            model=MODEL_FLASH_LITE,
            batch_requests=batch_requests,
            job_name=job_name,
            results_dir=results_dir,
            poll_interval=poll_interval,
            max_wait_time=max_wait_time,
        )

        if not results:
            logger.error(f"Batch {batch_num} failed or timed out.")
            continue

        # Process and save results for this batch
        batch_processing_status = process_batch_results(results, file_batch, storage_client)
        all_processing_status.update(batch_processing_status)

        # Report batch results
        batch_successful = sum(
            1 for status in batch_processing_status.values() if status == "success"
        )

        logger.info(
            f"Batch {batch_num} completed: {batch_successful}/{len(file_batch)} successful"
        )

    # Report final results
    successful = sum(1 for status in all_processing_status.values() if status == "success")
    failed = len(all_processing_status) - successful

    logger.success("All batches completed:")
    logger.info(f"  Total successful: {successful}/{len(storage_files)}")
    logger.info(f"  Total failed: {failed}/{len(storage_files)}")

    if failed > 0:
        logger.warning("Failed files:")
        for key, status in all_processing_status.items():
            if status != "success":
                logger.warning(f"  {key}: {status}")


# --- Asynchronous version ---


def main_batch_async():
    """
    Asynchronous version that submits the batch job and returns immediately.
    Use this if you want to submit the job and check results later.
    """
    # Load prompt
    prompt_franserve_data = (CONFIG_DIR / "franserve" / "data_prompt.txt").read_text()

    # Get all HTML files
    html_files = list(EXTERNAL_DATA_DIR.glob("*.html"))

    if not html_files:
        logger.warning("No HTML files found to process.")
        return None

    # Create batch requests
    batch_requests = create_franchise_data_batch_requests(html_files, prompt_franserve_data)

    # Set up batch job
    job_name = f"franchise_data_extraction_{len(batch_requests)}_files"
    results_dir = RAW_DATA_DIR / "batch_results" / "franchise_data"

    # Create batch file
    batch_file_path = results_dir / f"{job_name}_requests.jsonl"
    create_batch_file(batch_requests, batch_file_path)

    # Submit batch job
    batch_job_name = submit_batch_job(CLIENT, MODEL_FLASH_LITE, batch_file_path, job_name)

    logger.success(f"Batch job submitted: {batch_job_name}")

    return batch_job_name


def check_batch_results(batch_job_name: str):
    """
    Check the status of a batch job and process results if completed.

    Args:
        batch_job_name: The batch job name to check
    """
    # Check job status (non-blocking)
    result_file_name = monitor_batch_job(CLIENT, batch_job_name, poll_interval=0, max_wait_time=1)

    if result_file_name:
        # Job completed, download and process results
        results_dir = RAW_DATA_DIR / "batch_results" / "franchise_data"
        results_file_path = results_dir / f"results_{batch_job_name}.jsonl"

        results = download_batch_results(CLIENT, result_file_name, results_file_path)

        # Get original HTML files for processing
        html_files = list(EXTERNAL_DATA_DIR.glob("*.html"))
        processing_status = process_batch_results(results, html_files)

        # Report results
        successful = sum(1 for status in processing_status.values() if status == "success")
        failed = len(processing_status) - successful

        logger.success("Batch results processed:")
        logger.info(f"  Successful: {successful}/{len(html_files)}")
        logger.info(f"  Failed: {failed}/{len(html_files)}")

        print("\n")

        return processing_status

    logger.info("Batch job still in progress or failed.")
    return None


if __name__ == "__main__":
    # Run batch mode with monitoring
    main_batch()
