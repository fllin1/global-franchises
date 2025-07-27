# -*- coding: utf-8 -*-
"""
Extract keywords from franchise data using Gemini API in batch mode.

This module processes multiple franchise data files simultaneously using the Gemini API
batch mode for cost-effective and efficient keyword extraction.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Optional

from google.genai import types
from loguru import logger
import pandas as pd

from src.api.config.genai_gemini_config import (
    CLIENT,
    MODEL_FLASH,
    MODEL_FLASH_LITE,
    get_generate_content_config_keywords,
    get_thinking_config,
    get_tools,
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
from src.data.nlp.genai_keywords import create_summary_for_keyword_extraction


def create_keywords_batch_requests(
    franchise_data_paths: List[Path], prompt_keywords: str
) -> List[Dict]:
    """
    Create batch requests for all franchise data files.

    Args:
        franchise_data_paths: List of franchise JSON file paths to process
        prompt_keywords: The prompt template for keyword extraction

    Returns:
        List of batch request dictionaries
    """
    batch_requests = []

    for franchise_data_path in franchise_data_paths:
        # Load franchise data
        with open(franchise_data_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)

        franchise_data = raw_data["franchise_data"]
        source_id = raw_data.get("source_id")

        # Create summary for keyword extraction
        franchise_summary = create_summary_for_keyword_extraction(franchise_data)

        # Create parts
        parts = [
            types.Part(text=prompt_keywords),
            types.Part(text="\n--- FRANCHISE SUMMARY ---\n"),
            types.Part(text=franchise_summary),
        ]

        # Create batch request with full configuration
        request_key = f"source_{source_id}" if source_id else franchise_data_path.stem

        batch_request = create_batch_request(
            key=request_key,
            parts=parts,
            generate_content_config=get_generate_content_config_keywords(
                # thinking_config=get_thinking_config(thinking_budget=-1),
                # tools=get_tools(google_search=True),
            ),
        )

        batch_requests.append(batch_request)
    return batch_requests


def process_keywords_batch_results(
    results: Dict[str, Dict], franchise_data_paths: List[Path]
) -> pd.DataFrame:
    """
    Process batch results and create keywords DataFrame.

    Args:
        results: Dictionary mapping request keys to API responses
        franchise_data_paths: Original list of franchise data files

    Returns:
        DataFrame with source_id and keywords columns
    """
    # Create lookup for franchise files by source_id
    source_id_to_path = {}
    for path in franchise_data_paths:
        with open(path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
            source_id = raw_data.get("source_id")
            if source_id:
                source_id_to_path[f"source_{source_id}"] = path
            else:
                source_id_to_path[path.stem] = path

    processed_data = []

    for request_key, response in results.items():
        try:
            # Get the original franchise file
            franchise_path = source_id_to_path.get(request_key)

            # Load source_id from original file
            with open(franchise_path, "r", encoding="utf-8") as file:
                raw_data = json.load(file)
                source_id = raw_data.get("source_id")

            # Extract response text
            response_text = (
                response.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            if not response_text:
                logger.error(f"No response text for {request_key}")
                continue

            keywords = ast.literal_eval(response_text)

            if not isinstance(keywords, list):
                raise ValueError("Response is not a list")

            # Limit keywords to 10
            if len(keywords) > 10:
                logger.warning(f"Too many keywords found for {source_id}, limiting to 10")
                keywords = keywords[:10]

            if len(keywords) == 0:
                logger.warning(f"No keywords found for {source_id}")
                continue

            # Add to processed data
            processed_data.append({"source_id": source_id, "keywords": ", ".join(keywords)})

        except Exception as e:
            logger.error(f"Error processing {request_key}: {e}")
            continue

    # Create DataFrame
    df_keywords = pd.DataFrame(processed_data)
    logger.info(f"Successfully processed {len(df_keywords)} keyword entries")

    return df_keywords


def main_batch(
    batch_size: Optional[int] = None,
    poll_interval: int = 300,  # 5 minutes
    max_wait_time: int = 86400,  # 24 hours
):
    """
    Main function to run the keyword extraction in batch mode.

    Args:
        batch_size: Number of files per batch. None = process all files in one batch
        poll_interval: How often to check batch job status (seconds)
        max_wait_time: Maximum time to wait for batch completion (seconds)
    """
    output_path = RAW_DATA_DIR / "keywords.csv"

    # Load existing data for upsert
    if output_path.exists():
        df_existing = pd.read_csv(output_path)
    else:
        df_existing = pd.DataFrame(columns=["source_id", "keywords"])

    # Load prompt
    prompt_path = CONFIG_DIR / "franserve" / "keywords_prompt.txt"
    with open(prompt_path, "r", encoding="utf-8") as file:
        prompt_keywords = file.read()

    # Get all franchise data files
    franchise_data_paths = list((RAW_DATA_DIR / "franserve").glob("*.json"))
    logger.info(f"Found {len(franchise_data_paths)} franchise files to process in batch mode.")

    # Split files into batches
    file_batches = split_into_batches(franchise_data_paths, batch_size)

    all_new_keywords = []

    # Process each batch
    for batch_num, franchise_batch in enumerate(file_batches, 1):
        logger.info(
            f"Processing batch {batch_num}/{len(file_batches)} ({len(franchise_batch)} files)"
        )

        # Create batch requests for this batch
        batch_requests = create_keywords_batch_requests(franchise_batch, prompt_keywords)

        # Set up batch job
        job_name = f"keywords_extraction_batch{batch_num}_{len(batch_requests)}_files"
        results_dir = RAW_DATA_DIR / "batch_results" / "keywords"

        logger.info(f"Starting batch job: {job_name}")

        # Process batch workflow
        results = process_batch_workflow(
            client=CLIENT,
            model=MODEL_FLASH,
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
        logger.info(f"Processing batch {batch_num} results...")
        df_batch_keywords = process_keywords_batch_results(results, franchise_batch)

        if not df_batch_keywords.empty:
            all_new_keywords.append(df_batch_keywords)
            logger.info(
                f"Batch {batch_num} completed: {len(df_batch_keywords)} keywords extracted"
            )

    # Combine all batch results
    if all_new_keywords:
        df_new_keywords = pd.concat(all_new_keywords, ignore_index=True)
    else:
        df_new_keywords = pd.DataFrame(columns=["source_id", "keywords"])

    if df_new_keywords.empty:
        logger.warning("No keywords were successfully extracted.")
        return

    # Upsert: Remove existing entries and add new ones
    logger.info("Performing upsert operation...")

    for _, row in df_new_keywords.iterrows():
        source_id = row["source_id"]
        # Remove any existing row with this source_id
        df_existing = df_existing[df_existing["source_id"] != source_id]

    # Append new data
    df_final = pd.concat([df_existing, df_new_keywords], ignore_index=True)

    # Save to CSV
    df_final.to_csv(output_path, index=False)

    # Report results
    logger.success("All keyword extraction batches completed:")
    logger.info(f"  Successfully processed: {len(df_new_keywords)} franchises")
    logger.info(f"  Total keywords in database: {len(df_final)} franchises")
    logger.info(f"  Saved to: {output_path}")


# --- Asynchronous version ---


def main_batch_async():
    """
    Asynchronous version that submits the batch job and returns immediately.
    Use this if you want to submit the job and check results later.
    """
    # Load prompt
    prompt_path = CONFIG_DIR / "franserve" / "keywords_prompt.txt"
    with open(prompt_path, "r", encoding="utf-8") as file:
        prompt_keywords = file.read()

    # Get all franchise data files
    franchise_data_paths = list((RAW_DATA_DIR / "franserve").glob("*.json"))
    logger.info(f"Found {len(franchise_data_paths)} franchise files to process in batch mode.")

    if not franchise_data_paths:
        logger.warning("No franchise data files found to process.")
        return None

    # Create batch requests
    batch_requests = create_keywords_batch_requests(franchise_data_paths, prompt_keywords)

    # Set up batch job
    job_name = f"keywords_extraction_{len(batch_requests)}_files"
    results_dir = RAW_DATA_DIR / "batch_results" / "keywords"

    batch_file_path = results_dir / f"{job_name}_requests.jsonl"
    create_batch_file(batch_requests, batch_file_path)

    # Submit batch job
    batch_job_name = submit_batch_job(CLIENT, MODEL_FLASH_LITE, batch_file_path, job_name)

    logger.success(f"Keywords batch job submitted: {batch_job_name}")
    logger.info(
        "Job will complete within 24 hours. Use check_keywords_batch_results() to monitor progress."
    )

    return batch_job_name


def check_keywords_batch_results(batch_job_name: str):
    """
    Check the status of a keywords batch job and process results if completed.

    Args:
        batch_job_name: The batch job name to check
    """
    # Check job status (non-blocking)
    result_file_name = monitor_batch_job(CLIENT, batch_job_name, poll_interval=0, max_wait_time=1)

    if result_file_name:
        # Job completed, download and process results
        results_dir = RAW_DATA_DIR / "batch_results" / "keywords"
        results_file_path = results_dir / f"results_{batch_job_name}.jsonl"

        results = download_batch_results(CLIENT, result_file_name, results_file_path)

        # Get original franchise data files for processing
        franchise_data_paths = list((RAW_DATA_DIR / "franserve").glob("*.json"))
        df_new_keywords = process_keywords_batch_results(results, franchise_data_paths)

        if not df_new_keywords.empty:
            # Perform upsert operation
            output_path = RAW_DATA_DIR / "keywords.csv"

            if output_path.exists():
                df_existing = pd.read_csv(output_path)
            else:
                df_existing = pd.DataFrame(columns=["source_id", "keywords"])

            # Remove existing entries and add new ones
            for _, row in df_new_keywords.iterrows():
                source_id = row["source_id"]
                df_existing = df_existing[df_existing["source_id"] != source_id]

            df_final = pd.concat([df_existing, df_new_keywords], ignore_index=True)
            df_final.to_csv(output_path, index=False)

            logger.info("Keywords batch results processed:")
            logger.info(f"  Successfully processed: {len(df_new_keywords)} franchises")
            logger.info(f"  Total in database: {len(df_final)} franchises")

            return df_final
        else:
            logger.warning("No keywords were successfully extracted from batch results.")
            return None
    else:
        logger.info("Keywords batch job still in progress or failed.")
        return None


if __name__ == "__main__":
    # Run batch mode with monitoring
    main_batch()
