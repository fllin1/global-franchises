# -*- coding: utf-8 -*-
"""
Generate embeddings for the franchises table in Supabase with OpenAI API.
"""

from loguru import logger
import pandas as pd

from src.api.openai_text_embedding_3_small import generate_text_embedding_3_small
from src.config import RAW_DATA_DIR
from src.data.embeddings.embeddings import (
    PrepareDataEmbeddings,
    format_data_for_embeddings,
    prepare_data_for_embeddings,
)


def generate_embeddings() -> None:
    """
    Generate embeddings for the franchises table in Supabase with OpenAI API.
    """

    embedd = PrepareDataEmbeddings()
    df_embeddings = embedd.get_df_embeddings()
    franchises_data_files = embedd.get_franchises_data_files()
    offset = embedd.offset
    batch_size = embedd.batch_size

    final_embeddings = []

    while True:
        franchises_batch = franchises_data_files[offset : offset + batch_size]

        # Check if we've processed all available franchises in this run
        if len(franchises_batch) < batch_size:
            logger.success(f"Processed {offset + len(franchises_batch)} franchises")
            break

        offset += batch_size

        documents_to_embed = prepare_data_for_embeddings(
            franchises_batch, franchises_data_files, offset, batch_size
        )

        embedding_response = generate_text_embedding_3_small(documents_to_embed)
        df_embeddings, final_embeddings = format_data_for_embeddings(
            franchises_batch, df_embeddings, embedding_response, final_embeddings
        )

    df_embeddings = pd.DataFrame(final_embeddings)
    df_embeddings.to_csv(RAW_DATA_DIR / "embeddings.csv", index=False)
