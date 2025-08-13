# -*- coding: utf-8 -*-
"""
This module contains the functions to create a dataset from the raw data.
"""

import json
from pathlib import Path

from loguru import logger
import pandas as pd
import typer

from src.api.config.supabase_config import (
    CONTACTS_TABLE,
    FRANCHISE_TABLE,
    supabase_client,
)
from src.config import INTERIM_DATA_DIR, RAW_DATA_DIR
from src.data.utils import clean_contact_data, clean_franchise_data

app = typer.Typer(pretty_exceptions_enable=False)


def clean_franchise_data(franchise_dict):
    """
    Clean and convert franchise data types for database insertion.

    Handles:
    - Converting float strings to integers for year fields
    - Replacing NaN values with None
    - Ensuring proper data types for database fields
    """
    cleaned = franchise_dict.copy()

    # Fields that should be integers (smallint in database)
    # Expanded list to include ALL possible financial and numeric fields
    integer_fields = [
        "founded_year",
        "franchised_year",
        "franchise_fee_usd",
        "required_cash_investment_usd",
        "total_investment_min_usd",
        "total_investment_max_usd",
        "required_net_worth_usd",
        "current_franchises_count",
        "current_company_units_count",
        "franchising_years_count",
        "total_investment_range_min",
        "total_investment_range_max",
        "liquid_capital_required",
        "franchise_fee",
        "total_investment",
        "initial_investment",
        "startup_cost",
        "royalty_fee",
        "marketing_fee",
        "territory_fee",
        "units_in_development",
        "total_units",
        "company_owned_units",
        "franchised_units",
        "multi_unit_development_since",
        "franchise_since",
        "business_established",
        "first_franchise_opened",
    ]

    # Fields that should be floats
    float_fields = ["royalty_percentage", "marketing_fee_percentage"]

    # Debug: Log which field causes issues
    def debug_field_conversion(field_name, original_value, converted_value, error=None):
        if error:
            logger.error(
                f"    🔍 CONVERSION ERROR: {field_name}='{original_value}' -> ERROR: {error}"
            )
        else:
            logger.debug(
                f"    ✅ CONVERTED: {field_name}='{original_value}' -> {converted_value}"
            )

    # Clean integer fields
    for field in integer_fields:
        if field in cleaned:
            original_value = cleaned[field]
            try:
                if (
                    pd.isna(original_value)
                    or original_value == ""
                    or original_value is None
                ):
                    cleaned[field] = None
                    debug_field_conversion(field, original_value, None)
                elif isinstance(original_value, str):
                    # Handle string representations of floats and ints
                    if original_value.strip() == "" or original_value.lower() in [
                        "nan",
                        "null",
                        "none",
                    ]:
                        cleaned[field] = None
                        debug_field_conversion(field, original_value, None)
                    else:
                        # Convert string to float first, then to int to handle "200000.0" strings
                        float_value = float(original_value)
                        if math.isnan(float_value):
                            cleaned[field] = None
                            debug_field_conversion(field, original_value, None)
                        else:
                            converted_value = int(float_value)
                            cleaned[field] = converted_value
                            debug_field_conversion(
                                field, original_value, converted_value
                            )
                elif isinstance(original_value, (int, float)):
                    if isinstance(original_value, float) and math.isnan(original_value):
                        cleaned[field] = None
                        debug_field_conversion(field, original_value, None)
                    else:
                        converted_value = int(original_value)
                        cleaned[field] = converted_value
                        debug_field_conversion(field, original_value, converted_value)
                else:
                    # Handle any other type by trying to convert to int
                    converted_value = int(float(str(original_value)))
                    cleaned[field] = converted_value
                    debug_field_conversion(field, original_value, converted_value)
            except (ValueError, TypeError) as e:
                debug_field_conversion(field, original_value, None, str(e))
                logger.warning(
                    f"Could not convert {field} value '{original_value}' "
                    "(type: {type(original_value)}) to integer, setting to None"
                )
                cleaned[field] = None

    # Clean float fields
    for field in float_fields:
        if field in cleaned:
            original_value = cleaned[field]
            try:
                if (
                    pd.isna(original_value)
                    or original_value == ""
                    or original_value is None
                ):
                    cleaned[field] = None
                elif isinstance(original_value, str):
                    if original_value.strip() == "" or original_value.lower() in [
                        "nan",
                        "null",
                        "none",
                    ]:
                        cleaned[field] = None
                    else:
                        float_value = float(original_value)
                        if math.isnan(float_value):
                            cleaned[field] = None
                        else:
                            cleaned[field] = float_value
                elif isinstance(original_value, (int, float)):
                    if isinstance(original_value, float) and math.isnan(original_value):
                        cleaned[field] = None
                    else:
                        cleaned[field] = float(original_value)
                else:
                    cleaned[field] = float(str(original_value))
            except (ValueError, TypeError):
                logger.warning(
                    f"Could not convert {field} value '{original_value}' "
                    "(type: {type(original_value)}) to float, setting to None"
                )
                cleaned[field] = None

    # Clean string fields - replace NaN with None
    for key, value in cleaned.items():
        if key not in integer_fields and key not in float_fields:
            if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
                cleaned[key] = None
            elif isinstance(value, str) and value.lower() in ["nan", "null", ""]:
                cleaned[key] = None

    return cleaned


def clean_contact_data(contact_dict):
    """
    Clean contact data for database insertion.
    """
    cleaned = contact_dict.copy()

    # Clean string fields - replace NaN with None
    for key, value in cleaned.items():
        if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
            cleaned[key] = None
        elif isinstance(value, str) and value.lower() in ["nan", "null", ""]:
            cleaned[key] = None

    return cleaned


@app.command()
def format_jsonl_to_csv(
    input_path: Path = RAW_DATA_DIR
    / "batch_results"
    / "keywords"
    / "keywords_extraction_batch1_769_files_results.jsonl",
    output_path: Path = RAW_DATA_DIR / "keywords.csv",
):
    """
    Format the jsonl files to csv.
    """

    logger.info("Formatting jsonl to csv...")

    keywords_list = []
    with open(input_path, "r", encoding="utf-8") as file:
        for line in file:
            data = json.loads(line)
            source_id = data["key"].split("_")[-1]
            try:
                keywords = data["response"]["candidates"][0]["content"]["parts"][-1][
                    "text"
                ]
                keywords = keywords.replace("```", "")
                keywords = keywords.replace("`", "'")
                keywords = keywords.strip()

                keywords = keywords.split("[")[-1]
                keywords = keywords.split("]")[0]
                keywords = keywords.split(r"\n")[-1]

                if not keywords.startswith("["):
                    keywords = f"[{keywords}"
                if not keywords.endswith("]"):
                    keywords = f"{keywords}]"
            except KeyError:
                logger.error(f"Error parsing keywords: {data}")
                continue

            try:
                keywords = ast.literal_eval(keywords)
                keywords = [keyword.strip() for keyword in keywords]
                keywords = ", ".join(keywords)

                assert isinstance(
                    keywords, str
                ), f"Keywords is not a string: {keywords}"
                keyword_data = {
                    "source_id": source_id,
                    "keywords": keywords,
                }
                keywords_list.append(keyword_data)
            except (ValueError, SyntaxError):
                logger.error(f"Error parsing keywords: {keywords}")
                continue

    df = pd.DataFrame(keywords_list)
    df.to_csv(output_path, index=False)

    logger.success("Jsonl formatted to csv.")


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
                        contacts_data.append(
                            contact
                        )  # Append individual contact, not list
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
        franchises_path,
        keep_default_na=False,
        na_values=["", "nan", "NaN", "null", "NULL"],
    )
    df_contacts = pd.read_csv(
        contacts_path,
        keep_default_na=False,
        na_values=["", "nan", "NaN", "null", "NULL"],
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
        contacts_data = contacts_data[
            :10
        ]  # More contacts to test relationship matching

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
                franchise_id_mapping[str(cleaned_franchise["source_id"])] = db_record[
                    "id"
                ]
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
            logger.error(
                f"  ❌ ERROR: Failed to upsert franchise {source_id}: {str(e)}"
            )
            logger.error(f"  Exception type: {type(e).__name__}")
            continue

    logger.info("=" * 60)
    logger.info(
        f"FRANCHISE PROCESSING COMPLETE: {franchise_success_count} "
        f"success, {franchise_fail_count} failed"
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
            f"[{i}/{len(contacts_data)}] Processing contact: "
            f"{contact_name} (Franchise ID: {contact_source_id})"
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
            contact_response = (
                supabase.table(CONTACTS_TABLE).upsert(cleaned_contact).execute()
            )

            if contact_response.data and len(contact_response.data) > 0:
                contact_success_count += 1
                logger.info(f"  ✅ SUCCESS: Upserted contact {contact_name}")
            else:
                contact_fail_count += 1
                logger.error(
                    f"  ❌ FAILED: No data returned for contact {contact_name}"
                )
                logger.error(f"  Response: {contact_response}")

        except Exception as e:
            contact_fail_count += 1
            logger.error(
                f"  ❌ ERROR: Failed to upsert contact {contact_name}: {str(e)}"
            )
            logger.error(f"  Exception type: {type(e).__name__}")
            continue

    logger.info("=" * 60)
    logger.info(
        f"CONTACT PROCESSING COMPLETE: {contact_success_count} success, "
        f"{contact_fail_count} failed, {contact_skip_count} skipped"
    )
    logger.info("=" * 60)

    # Final summary
    total_records = len(franchises_data) + len(contacts_data)
    total_success = franchise_success_count + contact_success_count
    total_failed = franchise_fail_count + contact_fail_count

    logger.success("FINAL SUMMARY:")
    logger.success(f"  📊 Total Records Processed: {total_records}")
    logger.success(f"  ✅ Successful Upserts: {total_success}")
    logger.success(f"  ❌ Failed Upserts: {total_failed}")
    logger.success(f"  ⚠️  Skipped Contacts: {contact_skip_count}")
    logger.success(f"  📈 Success Rate: {(total_success / total_records) * 100:.1f}%")
    logger.success(
        f"  🏢 Franchises: {franchise_success_count}/{len(franchises_data)} "
        f"({(franchise_success_count / len(franchises_data)) * 100:.1f}%)"
    )
    logger.success(
        f"  👥 Contacts: {contact_success_count}/{len(contacts_data)} "
        f"({(contact_success_count / len(contacts_data)) * 100:.1f}%)"
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
