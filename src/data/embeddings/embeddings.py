# -*- coding: utf-8 -*-
"""
Functions to generate embeddings for the franchises table in Supabase.
"""

import json
from pathlib import Path

from loguru import logger
import pandas as pd

from src.config import RAW_DATA_DIR


class PrepareDataEmbeddings:
    """
    Class to prepare data for embedding.
    """

    def __init__(self):
        self.offset = 0
        self.batch_size = 100
        self.columns_franchise_data = [
            "source_id",
            "franchise_name",
            "primary_category",
            "sub_categories",
            "why_franchise_summary",
            "ideal_candidate_profile_text",
            "description_text",
        ]

        self.columns_embeddings = ["source_id", "franchise_embedding"]
        self.embeddings_path = RAW_DATA_DIR / "embeddings.csv"

        self.franchises_data_dir = RAW_DATA_DIR / "franserve"
        self.franchises_data_files = list(self.franchises_data_dir.glob("*.json"))

    def get_franchises_data_files(self) -> list[Path]:
        """
        Get the franchises data files.
        """
        return list(self.franchises_data_dir.glob("*.json"))

    def get_df_embeddings(self) -> pd.DataFrame:
        """
        Get the embeddings dataframe.
        """
        if self.embeddings_path.exists():
            df_embeddings = pd.read_csv(self.embeddings_path)
        else:
            df_embeddings = pd.DataFrame(columns=self.columns_embeddings)
        return df_embeddings


def create_persona_document(franchise: dict) -> str:
    """
    Concatenates key text fields from a franchise record into a single
    document for embedding. Handles missing fields gracefully.
    """
    # Prioritize the most descriptive fields first
    parts = [
        franchise.get("franchise_name", ""),
        franchise.get("primary_category", ""),
        " ".join(franchise.get("sub_categories", [])),  # Assuming sub_categories is a list
        franchise.get("why_franchise_summary", ""),
        franchise.get("ideal_candidate_profile_text", ""),
        franchise.get("description_text", ""),
    ]

    for i, part in enumerate(parts):
        if isinstance(part, list):
            parts[i] = " ".join(part)

    # Filter out empty or None parts and join them
    document = " ".join(filter(None, parts)).strip().replace("\n", " ")
    return document


def prepare_data_for_embeddings(
    franchises_batch: list,
    franchises_data_files: list,
    offset: int,
    batch_size: int,
) -> list:
    """
    Generates embeddings for a list of franchises.
    """

    logger.info(
        f"Processing batch {offset // batch_size + 1} "
        f"of {len(franchises_data_files) // batch_size + 1}"
    )
    franchises_batch = []

    for file in franchises_data_files[offset : offset + batch_size]:
        with open(file, "r", encoding="utf-8") as f:
            franchise_data = json.load(f)["franchise_data"]
            franchise_data = {
                k: v
                for k, v in franchise_data.items()
                if k in PrepareDataEmbeddings.columns_franchise_data
            }
        franchises_batch.append(franchise_data)

    # Prepare documents for the API call
    documents_to_embed = [create_persona_document(f) for f in franchises_batch]
    return documents_to_embed


def format_data_for_embeddings(
    franchises_batch: list,
    df_embeddings: pd.DataFrame,
    embedding_response: list,
    final_embeddings: list,
) -> list:
    """
    Format data for embeddings.
    """
    embeddings = [item.embedding for item in embedding_response.data]

    # Prepare data for batch update
    updates = []
    for i, franchise in enumerate(franchises_batch):
        updates.append({"source_id": franchise["source_id"], "franchise_embedding": embeddings[i]})
    final_embeddings.extend(updates)

    df_updates = pd.DataFrame(updates)
    df_embeddings = df_embeddings[~df_embeddings["source_id"].isin(df_updates["source_id"])]
    df_embeddings = pd.concat([df_embeddings, df_updates], ignore_index=True)

    return df_embeddings, final_embeddings
