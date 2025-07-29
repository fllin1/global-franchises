# -*- coding: utf-8 -*-
"""
This module contains the functions to create a dataset from the raw data.
"""

import json
from pathlib import Path

from loguru import logger
import pandas as pd
import typer

from src.api.config.supabase_config import CONTACTS_TABLE, FRANCHISE_TABLE, supabase_client
from src.config import INTERIM_DATA_DIR, RAW_DATA_DIR
from src.data.utils import clean_contact_data, clean_franchise_data

app = typer.Typer(pretty_exceptions_enable=False)


@app.command()
def merge_data(
    input_dir: Path = RAW_DATA_DIR,
    output_dir: Path = INTERIM_DATA_DIR,
):
    """
    Create a dataset from the raw data.
    """

    logger.info("Creating dataset from raw data...")

    # Load keywords and embeddings
    keywords_path: Path = input_dir / "keywords.csv"
    if keywords_path.exists():
        df_keywords = pd.read_csv(keywords_path)[["source_id", "keywords"]]
    else:
        df_keywords = pd.DataFrame(columns=["source_id", "keywords"])

    embeddings_path: Path = input_dir / "embeddings.csv"
    if embeddings_path.exists():
        df_embeddings = pd.read_csv(embeddings_path)
    else:
        df_embeddings = pd.DataFrame(columns=["source_id", "franchise_embedding"])

    # Load franserve data
    franserve_data_dir: Path = input_dir / "franserve"
    franserve_data_files = list(franserve_data_dir.glob("*.json"))

    franchises_data = []
    contacts_data = []

    for file in franserve_data_files:
        with open(file, "r", encoding="utf-8") as f:
            franserve_data = json.load(f)
            franchise_info = franserve_data["franchise_data"]

            source_id = franserve_data["source_id"]

            # Add source_id to franchise data
            franchise_info["source_id"] = source_id
            franchises_data.append(franchise_info)

            # Handle contacts properly - add source_id to each contact
            try:
                franchise_contacts = franserve_data["contacts_data"]
                if franchise_contacts and isinstance(franchise_contacts, list):
                    for contact in franchise_contacts:
                        contact["source_id"] = source_id  # Link contact to franchise
                        contacts_data.append(contact)  # Append individual contact, not list
            except KeyError:
                logger.error(f"Error parsing contacts: {franserve_data}")
                continue

    df_franchises = pd.DataFrame(franchises_data)
    df_contacts = pd.DataFrame(contacts_data)

    df_franchises = df_franchises.merge(df_keywords, on="source_id", how="left")
    df_franchises = df_franchises.merge(df_embeddings, on="source_id", how="left")

    franchises_path = output_dir / "franchises.csv"
    contacts_path = output_dir / "contacts.csv"
    df_franchises.to_csv(franchises_path, index=False)
    df_contacts.to_csv(contacts_path, index=False)

    logger.success("Dataset created successfully.")


@app.command()
def update_supabase(
    input_dir: Path = INTERIM_DATA_DIR,
    test_mode: bool = typer.Option(
        False, "--test", help="Process only first 5 records for testing"
    ),
):
    """
    Update the Supabase database with the dataset using individual record processing.

    This function processes each franchise and contact individually to maximize
    data insertion success and provide detailed error reporting.
    """

    if test_mode:
        logger.info("🧪 TEST MODE: Processing only first 5 franchises for debugging")

    logger.info("Starting individual record Supabase update process...")

    franchises_path: Path = input_dir / "franchises.csv"
    contacts_path: Path = input_dir / "contacts.csv"

    # Validate input files exist
    if not franchises_path.exists():
        logger.error(f"Franchises file not found: {franchises_path}")
        return

    if not contacts_path.exists():
        logger.error(f"Contacts file not found: {contacts_path}")
        return

    # Read CSV files with explicit data type handling to prevent float conversion issues
    df_franchises = pd.read_csv(
        franchises_path, keep_default_na=False, na_values=["", "nan", "NaN", "null", "NULL"]
    )
    df_contacts = pd.read_csv(
        contacts_path, keep_default_na=False, na_values=["", "nan", "NaN", "null", "NULL"]
    )

    # Debug: Show data types to understand the CSV reading issue
    logger.debug("CSV Data Types Analysis:")
    integer_fields = [
        "founded_year",
        "franchised_year",
        "franchise_fee_usd",
        "required_cash_investment_usd",
        "required_net_worth_usd",
    ]
    for field in integer_fields:
        if field in df_franchises.columns:
            sample_values = df_franchises[field].head(3).tolist()
            data_type = df_franchises[field].dtype
            logger.debug(f"  {field}: dtype={data_type}, sample_values={sample_values}")

    # Clean data - remove rows with NaN in critical columns
    df_franchises = df_franchises.dropna(subset=["source_id"])
    df_contacts = df_contacts.dropna(subset=["name"])

    franchises_data = df_franchises.to_dict(orient="records")
    contacts_data = df_contacts.to_dict(orient="records")

    # Limit data for test mode
    if test_mode:
        franchises_data = franchises_data[:5]
        contacts_data = contacts_data[:10]  # More contacts to test relationship matching

    supabase = supabase_client()

    logger.info(
        f"Processing {len(franchises_data)} franchises "
        f"and {len(contacts_data)} contacts individually..."
    )

    # Process franchises individually
    franchise_success_count = 0
    franchise_fail_count = 0
    franchise_id_mapping = {}  # Map source_id to database id

    logger.info("=" * 60)
    logger.info("PROCESSING FRANCHISES INDIVIDUALLY")
    logger.info("=" * 60)

    for i, franchise in enumerate(franchises_data, 1):
        source_id = franchise.get("source_id")
        franchise_name = franchise.get("franchise_name", "Unknown")

        logger.info(
            f"[{i}/{len(franchises_data)}] Processing franchise: {franchise_name} (ID: {source_id})"
        )

        try:
            # Clean and validate franchise data before upserting
            cleaned_franchise = clean_franchise_data(franchise)

            # Check if source_id exists
            if not cleaned_franchise.get("source_id"):
                logger.error(f"  ❌ Skipping franchise {i}: Missing source_id")
                franchise_fail_count += 1
                continue

            # Log key data for debugging
            logger.debug(
                f"  📊 Key fields: source_id={cleaned_franchise.get('source_id')}, "
                f"name={cleaned_franchise.get('franchise_name')}, "
                f"founded_year={cleaned_franchise.get('founded_year')}"
            )

            # Upsert franchise with conflict resolution on source_id
            franchise_response = (
                supabase.table(FRANCHISE_TABLE)
                .upsert(cleaned_franchise, on_conflict="source_id")
                .execute()
            )

            if franchise_response.data and len(franchise_response.data) > 0:
                # Store mapping of source_id to database id for contacts
                db_record = franchise_response.data[0]
                franchise_id_mapping[str(cleaned_franchise["source_id"])] = db_record["id"]
                franchise_success_count += 1
                logger.info(
                    f"  ✅ SUCCESS: Upserted franchise {franchise_name} (DB ID: {db_record['id']})"
                )
            else:
                franchise_fail_count += 1
                logger.error(f"  ❌ FAILED: No data returned for franchise {source_id}")
                logger.error(f"  Response: {franchise_response}")

        except Exception as e:
            franchise_fail_count += 1
            logger.error(f"  ❌ ERROR: Failed to upsert franchise {source_id}: {str(e)}")
            logger.error(f"  Exception type: {type(e).__name__}")
            continue

    logger.info("=" * 60)
    logger.info(
        f"FRANCHISE PROCESSING COMPLETE: {franchise_success_count} success, {franchise_fail_count} failed"
    )
    logger.info("=" * 60)

    # Process contacts individually
    contact_success_count = 0
    contact_fail_count = 0
    contact_skip_count = 0

    logger.info("PROCESSING CONTACTS INDIVIDUALLY")
    logger.info("=" * 60)

    for i, contact in enumerate(contacts_data, 1):
        contact_name = contact.get("name", "Unknown")
        contact_source_id = str(contact.get("source_id", ""))

        logger.info(
            f"[{i}/{len(contacts_data)}] Processing contact: {contact_name} (Franchise ID: {contact_source_id})"
        )

        try:
            # Check if contact has source_id to link to franchises
            if not contact_source_id or contact_source_id not in franchise_id_mapping:
                contact_skip_count += 1
                logger.warning(
                    f"  ⚠️  SKIPPED: No matching franchise found for source_id {contact_source_id}"
                )
                continue

            # Prepare contact data
            contact_copy = contact.copy()
            contact_copy["franchise_id"] = franchise_id_mapping[contact_source_id]
            # Remove source_id from contact as it's not needed in the contacts table
            contact_copy.pop("source_id", None)

            # Clean contact data before upserting
            cleaned_contact = clean_contact_data(contact_copy)

            logger.debug(
                f"  📊 Key fields: name={cleaned_contact.get('name')}, "
                f"franchise_id={cleaned_contact.get('franchise_id')}, "
                f"email={cleaned_contact.get('email')}"
            )

            # Upsert contact
            contact_response = supabase.table(CONTACTS_TABLE).upsert(cleaned_contact).execute()

            if contact_response.data and len(contact_response.data) > 0:
                contact_success_count += 1
                logger.info(f"  ✅ SUCCESS: Upserted contact {contact_name}")
            else:
                contact_fail_count += 1
                logger.error(f"  ❌ FAILED: No data returned for contact {contact_name}")
                logger.error(f"  Response: {contact_response}")

        except Exception as e:
            contact_fail_count += 1
            logger.error(f"  ❌ ERROR: Failed to upsert contact {contact_name}: {str(e)}")
            logger.error(f"  Exception type: {type(e).__name__}")
            continue

    logger.info("=" * 60)
    logger.info(
        f"CONTACT PROCESSING COMPLETE: {contact_success_count} success, {contact_fail_count} failed, {contact_skip_count} skipped"
    )
    logger.info("=" * 60)

    # Final summary
    total_records = len(franchises_data) + len(contacts_data)
    total_success = franchise_success_count + contact_success_count
    total_failed = franchise_fail_count + contact_fail_count

    logger.success(f"FINAL SUMMARY:")
    logger.success(f"  📊 Total Records Processed: {total_records}")
    logger.success(f"  ✅ Successful Upserts: {total_success}")
    logger.success(f"  ❌ Failed Upserts: {total_failed}")
    logger.success(f"  ⚠️  Skipped Contacts: {contact_skip_count}")
    logger.success(f"  📈 Success Rate: {(total_success / total_records) * 100:.1f}%")
    logger.success(
        f"  🏢 Franchises: {franchise_success_count}/{len(franchises_data)} ({(franchise_success_count / len(franchises_data)) * 100:.1f}%)"
    )
    logger.success(
        f"  👥 Contacts: {contact_success_count}/{len(contacts_data)} ({(contact_success_count / len(contacts_data)) * 100:.1f}%)"
    )

    if franchise_fail_count > 0:
        logger.warning(
            f"⚠️  {franchise_fail_count} franchises failed to upsert. Check logs above for details."
        )
    if contact_fail_count > 0:
        logger.warning(
            f"⚠️  {contact_fail_count} contacts failed to upsert. Check logs above for details."
        )


if __name__ == "__main__":
    app()
