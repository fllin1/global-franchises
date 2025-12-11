#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to run HTML to Markdown conversion and display results.
"""

from loguru import logger

from src.api.config.supabase_config import supabase_client
from src.data.functions.extract import Extractor
from src.data.storage.storage_client import StorageClient


def main():
    logger.info("Starting HTML to Markdown conversion script...")

    # 1. Run Conversion
    extractor = Extractor()
    logger.info(f"Initialized Extractor. Today's prefix: {extractor.today_str}")

    try:
        logger.info("Executing HTML to Markdown conversion...")
        extractor.convert_html_to_markdown_and_upload()
        logger.success("Conversion execution finished.")
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        # We continue to try to show results even if it failed,
        # as partial results might be available.

    # 2. Display Results

    # A. Statistics from Database
    logger.info("\n--- Markdown Conversion Run Statistics ---")
    try:
        supabase = supabase_client()
        prefix = extractor.today_str
        
        # Get the most recent run for this prefix
        response = (
            supabase.table("scraping_runs")
            .select("*")
            .eq("storage_path_prefix", prefix)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        if response.data:
            run_data = response.data[0]
            print(f"Run ID: {run_data.get('id')}")
            print(f"Storage Prefix: {run_data.get('storage_path_prefix')}")
            print(f"\nMarkdown Conversion Status: {run_data.get('markdown_conversion_status', 'N/A')}")
            print(f"Markdown Conversions Completed: {run_data.get('markdown_conversions_completed', 0)}")
            print(f"Markdown Conversions Failed: {run_data.get('markdown_conversions_failed', 0)}")
            print(f"Markdown Conversions Skipped: {run_data.get('markdown_conversions_skipped', 0)}")
            
            started_at = run_data.get('markdown_conversion_started_at')
            completed_at = run_data.get('markdown_conversion_completed_at')
            if started_at:
                print(f"Conversion Started At: {started_at}")
            if completed_at:
                print(f"Conversion Completed At: {completed_at}")
            
            # Show converted files from metadata if available
            metadata = run_data.get('metadata')
            if metadata and isinstance(metadata, dict):
                converted_count = metadata.get('markdown_converted_files_count', 0)
                converted_files = metadata.get('markdown_converted_files', [])
                if converted_count > 0:
                    print(f"\nConverted Files: {converted_count} total")
                    if converted_files:
                        print(f"Sample Converted Files (showing last {min(10, len(converted_files))}):")
                        for filename in converted_files[-10:]:
                            print(f"  - {filename}")
        else:
            logger.warning(f"No scraping run record found for prefix '{prefix}'.")

    except Exception as e:
        logger.error(f"Failed to retrieve run statistics: {e}")

    # B. File Listing from Storage
    html_files = []
    markdown_files = []
    logger.info("\n--- Storage File Listing ---")
    try:
        storage_client = StorageClient()
        prefix = extractor.today_str
        files = storage_client.list_files(prefix)
        
        # Filter for HTML and Markdown files
        html_files = [f for f in files if f.get("name", "").endswith(".html")]
        markdown_files = [f for f in files if f.get("name", "").endswith(".md")]
        
        print(f"Total HTML files found in storage '{prefix}': {len(html_files)}")
        print(f"Total Markdown files found in storage '{prefix}': {len(markdown_files)}")
        
        if html_files:
            print("\nFirst 10 HTML files:")
            for i, file_obj in enumerate(html_files[:10]):
                size_kb = file_obj.get('metadata', {}).get('size', 0) / 1024
                print(f"{i+1}. {file_obj.get('name')} ({size_kb:.2f} KB)")
            
            if len(html_files) > 10:
                print(f"... and {len(html_files) - 10} more HTML files.")
        
        if markdown_files:
            print("\nFirst 10 Markdown files:")
            for i, file_obj in enumerate(markdown_files[:10]):
                size_kb = file_obj.get('metadata', {}).get('size', 0) / 1024
                print(f"{i+1}. {file_obj.get('name')} ({size_kb:.2f} KB)")
            
            if len(markdown_files) > 10:
                print(f"... and {len(markdown_files) - 10} more Markdown files.")
        
        # Show conversion ratio
        if html_files:
            conversion_ratio = len(markdown_files) / len(html_files) * 100
            print(f"\nConversion Ratio: {conversion_ratio:.1f}% ({len(markdown_files)}/{len(html_files)})")

    except Exception as e:
        logger.error(f"Failed to list files from storage: {e}")

    # C. Sample Markdown Display
    if markdown_files:
        logger.info("\n--- Sample Markdown Content ---")
        try:
            # Pick the first markdown file
            sample_file_name = markdown_files[0].get("name")
            sample_path = f"{prefix}/{sample_file_name}"
            
            print(f"Downloading sample file: {sample_path}")
            content = storage_client.download_markdown(sample_path)
            
            print(f"\nContent Preview (first 500 chars):")
            print("-" * 50)
            print(content[:500])
            print("...")
            print("-" * 50)
            print(f"Total content length: {len(content)} characters")
            
        except Exception as e:
            logger.error(f"Failed to download/display sample file: {e}")


if __name__ == "__main__":
    main()























