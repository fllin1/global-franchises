#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI for Gemini API Batch Processing

Simple command-line interface for running franchise data processing
in batch mode with 50% cost savings and configurable batch sizes.
"""

import argparse
import sys

from src.data.nlp.genai_data_batch import main_batch as data_main_batch
from src.data.nlp.genai_keywords_batch import main_batch as keywords_main_batch


def main():
    """
    Main function to run the CLI.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_cli.py data                      # Process all HTML files in one batch
  python batch_cli.py data --batch-size 10      # Process HTML files in batches of 10
  python batch_cli.py keywords --batch-size 20  # Process JSON files in batches of 20
  python batch_cli.py data --poll-interval 600  # Check status every 10 minutes
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Data extraction command
    data_parser = subparsers.add_parser(
        "data", help="Run franchise data extraction from HTML files"
    )
    data_parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of files per batch (default: process all files in one batch)",
    )
    data_parser.add_argument(
        "--poll-interval", type=int, default=300, help="Polling interval in seconds (default: 300)"
    )
    data_parser.add_argument(
        "--max-wait-time",
        type=int,
        default=86400,
        help="Maximum wait time in seconds (default: 86400 = 24 hours)",
    )

    # Keywords extraction command
    keywords_parser = subparsers.add_parser(
        "keywords", help="Run keyword extraction from franchise data"
    )
    keywords_parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of files per batch (default: process all files in one batch)",
    )
    keywords_parser.add_argument(
        "--poll-interval", type=int, default=300, help="Polling interval in seconds (default: 300)"
    )
    keywords_parser.add_argument(
        "--max-wait-time",
        type=int,
        default=86400,
        help="Maximum wait time in seconds (default: 86400 = 24 hours)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "data":
            print("Running franchise data extraction in batch mode...")
            if args.batch_size:
                print(f"Batch size: {args.batch_size} files per batch")
            else:
                print("Batch size: All files in one batch")

            data_main_batch(
                batch_size=args.batch_size,
                poll_interval=args.poll_interval,
                max_wait_time=args.max_wait_time,
            )

        elif args.command == "keywords":
            print("Running keyword extraction in batch mode...")
            if args.batch_size:
                print(f"Batch size: {args.batch_size} files per batch")
            else:
                print("Batch size: All files in one batch")

            keywords_main_batch(
                batch_size=args.batch_size,
                poll_interval=args.poll_interval,
                max_wait_time=args.max_wait_time,
            )

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
