# -*- coding: utf-8 -*-
"""
Utility functions for cleaning and converting data types for database insertion.
"""

import ast
import json
import math
from pathlib import Path

from loguru import logger
import pandas as pd

from src.config import RAW_DATA_DIR


# Debug: Log which field causes issues
def _debug_field_conversion(field_name, original_value, converted_value, error=None):
    if error:
        logger.error(f"    🔍 CONVERSION ERROR: {field_name}='{original_value}' -> ERROR: {error}")
    else:
        logger.debug(f"    ✅ CONVERTED: {field_name}='{original_value}' -> {converted_value}")


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

    # Clean integer fields
    for field in integer_fields:
        if field in cleaned:
            original_value = cleaned[field]
            try:
                if pd.isna(original_value) or original_value == "" or original_value is None:
                    cleaned[field] = None
                    _debug_field_conversion(field, original_value, None)
                elif isinstance(original_value, str):
                    # Handle string representations of floats and ints
                    if original_value.strip() == "" or original_value.lower() in [
                        "nan",
                        "null",
                        "none",
                    ]:
                        cleaned[field] = None
                        _debug_field_conversion(field, original_value, None)
                    else:
                        # Convert string to float first, then to int to handle "200000.0" strings
                        float_value = float(original_value)
                        if math.isnan(float_value):
                            cleaned[field] = None
                            _debug_field_conversion(field, original_value, None)
                        else:
                            converted_value = int(float_value)
                            cleaned[field] = converted_value
                            _debug_field_conversion(field, original_value, converted_value)
                elif isinstance(original_value, (int, float)):
                    if isinstance(original_value, float) and math.isnan(original_value):
                        cleaned[field] = None
                        _debug_field_conversion(field, original_value, None)
                    else:
                        converted_value = int(original_value)
                        cleaned[field] = converted_value
                        _debug_field_conversion(field, original_value, converted_value)
                else:
                    # Handle any other type by trying to convert to int
                    converted_value = int(float(str(original_value)))
                    cleaned[field] = converted_value
                    _debug_field_conversion(field, original_value, converted_value)
            except (ValueError, TypeError) as e:
                _debug_field_conversion(field, original_value, None, str(e))
                logger.warning(
                    f"Could not convert {field} value '{original_value}' (type: {type(original_value)}) to integer, setting to None"
                )
                cleaned[field] = None

    # Clean float fields
    for field in float_fields:
        if field in cleaned:
            original_value = cleaned[field]
            try:
                if pd.isna(original_value) or original_value == "" or original_value is None:
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
                    f"Could not convert {field} value '{original_value}' (type: {type(original_value)}) to float, setting to None"
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


def format_jsonl_to_csv(
    input_path: Path = RAW_DATA_DIR
    / "batch_results"
    / "keywords"
    / "keywords_extraction_batch1_769_files_results.jsonl",
    output_path: Path = RAW_DATA_DIR / "keywords.csv",
):
    """
    Format the jsonl output from the batch processing files to csv.
    """

    logger.info("Formatting jsonl to csv...")

    keywords_list = []
    with open(input_path, "r", encoding="utf-8") as file:
        for line in file:
            data = json.loads(line)
            source_id = data["key"].split("_")[-1]
            try:
                keywords = data["response"]["candidates"][0]["content"]["parts"][-1]["text"]
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

                assert isinstance(keywords, str), f"Keywords is not a string: {keywords}"
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
