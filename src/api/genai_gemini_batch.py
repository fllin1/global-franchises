# -*- coding: utf-8 -*-
"""
Batch mode utilities for the Gemini API.

This module provides utilities for creating and processing batch jobs
with the Gemini API, allowing for cost-effective processing of large datasets.
"""

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types
from loguru import logger


def split_into_batches(items: List[Any], batch_size: Optional[int] = None) -> List[List[Any]]:
    """
    Split a list of items into smaller batches.

    Args:
        items: List of items to split
        batch_size: Maximum items per batch. If None, return all items in one batch

    Returns:
        List of batches, where each batch is a list of items
    """
    if batch_size is None or batch_size <= 0:
        return [items]

    batches = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        batches.append(batch)

    return batches


def create_batch_request(
    key: str,
    parts: List[types.Part],
    generate_content_config: types.GenerateContentConfig,
) -> Dict[str, Any]:
    """
    Create a single batch request for the Gemini API.

    Args:
        key: Unique identifier for this request
        parts: The parts to include in the request
        generate_content_config: The generation configuration

    Returns:
        A dictionary representing a single batch request
    """
    # Convert parts to the format expected by batch API
    contents = [{"parts": [{"text": part.text} for part in parts]}]

    # Build the request object
    request_obj = {"contents": contents}

    # Add generation config
    generation_config = {
        "temperature": generate_content_config.temperature,
        "top_p": generate_content_config.top_p,
        "max_output_tokens": generate_content_config.max_output_tokens,
    }

    if hasattr(generate_content_config, "seed") and generate_content_config.seed:
        generation_config["seed"] = generate_content_config.seed

    if generate_content_config.response_mime_type:
        generation_config["response_mime_type"] = generate_content_config.response_mime_type

    if generate_content_config.response_schema:
        generation_config["response_schema"] = generate_content_config.response_schema

    request_obj["generation_config"] = generation_config

    # Add tools if present (batch mode supports tools!)
    if hasattr(generate_content_config, "tools") and generate_content_config.tools:
        tools_list = []
        for tool in generate_content_config.tools:
            if hasattr(tool, "google_search") and tool.google_search:
                tools_list.append({"google_search": {}})
            elif hasattr(tool, "code_execution") and tool.code_execution:
                tools_list.append({"code_execution": {}})
            elif hasattr(tool, "url_context") and tool.url_context:
                tools_list.append({"url_context": {}})
        if tools_list:
            request_obj["tools"] = tools_list

    # Add thinking config if present
    if (
        hasattr(generate_content_config, "thinking_config")
        and generate_content_config.thinking_config
    ):
        if hasattr(generate_content_config.thinking_config, "thinking_budget"):
            request_obj["generation_config"]["thinking_config"] = {
                "thinking_budget": generate_content_config.thinking_config.thinking_budget
            }

    return {"key": key, "request": request_obj}


def create_batch_file(batch_requests: List[Dict[str, Any]], batch_file_path: Path) -> Path:
    """
    Create a JSONL file containing all batch requests.

    Args:
        batch_requests: List of batch request dictionaries
        batch_file_path: Path where to save the batch file

    Returns:
        Path to the created batch file
    """
    batch_file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(batch_file_path, "w", encoding="utf-8") as f:
        for request in batch_requests:
            f.write(json.dumps(request) + "\n")

    return batch_file_path


def submit_batch_job(
    client: genai.Client, model: str, batch_file_path: Path, job_name: str
) -> str:
    """
    Submit a batch job to the Gemini API.

    Args:
        client: The Gemini client
        model: The model to use for the batch job
        batch_file_path: Path to the batch requests file
        job_name: Display name for the batch job

    Returns:
        The batch job name/ID
    """
    # Upload the batch file with correct MIME type
    uploaded_file = client.files.upload(
        file=str(batch_file_path),
        config=types.UploadFileConfig(display_name=str(batch_file_path), mime_type="jsonl"),
    )

    # Create the batch job
    batch_job = client.batches.create(
        model=model,
        src=uploaded_file.name,
        config={
            "display_name": job_name,
        },
    )

    logger.info(f"Batch job created: {batch_job.name}")
    return batch_job.name


def monitor_batch_job(
    client: genai.Client,
    batch_job_name: str,
    poll_interval: int = 300,
    max_wait_time: int = 86400,  # 24 hours
) -> Optional[str]:
    """
    Monitor a batch job until completion.

    Args:
        client: The Gemini client
        batch_job_name: The batch job name to monitor
        poll_interval: How often to check job status (seconds)
        max_wait_time: Maximum time to wait (seconds)

    Returns:
        Result file name if successful, None if failed or timed out
    """
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        time.sleep(poll_interval)

        batch_job = client.batches.get(name=batch_job_name)
        status = batch_job.state.name

        if status == "JOB_STATE_SUCCEEDED":
            logger.success("Batch job completed successfully")
            return batch_job.dest.file_name
        if status in ["JOB_STATE_FAILED", "JOB_STATE_CANCELLED"]:
            logger.error(f"Batch job failed with status: {status}")
            return None
        logger.debug(f"{batch_job_name}: {status}")

        # Wait before next check
        time.sleep(poll_interval)

    logger.error(f"Batch job timed out after {max_wait_time} seconds")
    return None


def download_batch_results(
    client: genai.Client, result_file_name: str, output_path: Path
) -> Dict[str, Any]:
    """
    Download and parse batch job results.

    Args:
        client: The Gemini client
        result_file_name: Name of the result file to download
        output_path: Path to save the results

    Returns:
        Dictionary mapping request keys to responses
    """
    logger.info(f"Downloading batch results: {result_file_name}")

    # Download the results file
    file_content_bytes = client.files.download(file=result_file_name)
    file_content = file_content_bytes.decode("utf-8")

    # Save raw results for debugging
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(file_content)

    # Parse results
    results = {}
    for line in file_content.splitlines():
        if line.strip():
            result = json.loads(line)
            key = result.get("key")
            response = result.get("response")

            if key and response:
                results[key] = response
            else:
                logger.warning(f"Invalid result line: {line}")

    logger.success(f"Downloaded {len(results)} batch results to {output_path}")
    return results


def process_batch_workflow(
    client: genai.Client,
    model: str,
    batch_requests: List[Dict[str, Any]],
    job_name: str,
    results_dir: Path,
    poll_interval: int = 300,  # 5 minutes
    max_wait_time: int = 86400,  # 24 hours
) -> Optional[Dict[str, Any]]:
    """
    Complete batch workflow: create file, submit job, monitor, and download results.

    Args:
        client: The Gemini client
        model: The model to use
        batch_requests: List of batch request dictionaries
        job_name: Display name for the batch job
        results_dir: Directory to save results
        poll_interval: How often to check job status (seconds)
        max_wait_time: Maximum time to wait (seconds)

    Returns:
        Dictionary mapping request keys to responses, or None if failed
    """
    # Create batch file
    batch_file_path = results_dir / f"{job_name}_requests.jsonl"
    create_batch_file(batch_requests, batch_file_path)

    # Submit batch job
    batch_job_name = submit_batch_job(client, model, batch_file_path, job_name)

    # Monitor job
    result_file_name = monitor_batch_job(client, batch_job_name, poll_interval, max_wait_time)

    if not result_file_name:
        return None

    # Download results
    results_file_path = results_dir / f"{job_name}_results.jsonl"
    results = download_batch_results(client, result_file_name, results_file_path)

    return results
