# Global Franchises

[![Licence](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](./LICENSE)

Global Franchises is a data pipeline project that scrapes franchise information from FranServe, and extract meaningful information about the franchises, helping brokers matching leads profiles to potential compatible franchises.

This project focuses on the ETL for the moment.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white) ![Google Gemini](https://img.shields.io/badge/google%20gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white) ![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)

Note: _Franserve is a private plateform in the US for brokers_

## Setup Instructions

This project used a Conda environment with Python 3.12 version.

1. **Virtual Environment**: **[Conda](https://www.anaconda.com/docs/getting-started/miniconda/install#quickstart-install-instructions)** environment:

   ```bash
   conda create -n global_franchises python=3.12
   conda activate global_franchises
   ```

2. **Install Dependencies**: Use **[Poetry](https://python-poetry.org/docs/)** to install required packages:

   ```bash
   pip install -e .
   poetry install
   ```

3. **Environment Variables**: Create a `.env` file in the project root with:

   ```text
   FRANSERVE_EMAIL=your_email
   FRANSERVE_PASSWORD=your_password

   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key

   GEMINI_API_KEY=your_gemini_key
   OPENAI_API_KEY=your_openai_key
   ```

## Execution Order

Run scripts in this order to process data:

0. **Scrape Data**: [`python src/data/franserve/scrapper.py`](./src/data/franserve/scrapper.py) - Fetches and saves raw HTML.
1. **Parse Data**: There are two ways to parse the data (Converts HTML to JSON):
   - The conventional method with rule-based parsing: [`python src/data/franserve/html_formatter.py`](./src/data/franserve/html_formatter.py)
   - A more organic method that uses API calls with Google Genai library for AI-assisted parsing: [`python src/data/nlp/genai_data.py`](./src/data/nlp/genai_data.py) (there is also a batch method in the same folder, which is still unstable, using the newly added batch feature from Google Genai in July 2025)
2. **Extract Info**: To facilitate the matching of the franchises with profiles of future leads, we prepare the data in two ways:
   - Extraction of **keywords**: [`python src/data/nlp/genai_keywords.py`](./src/data/nlp/genai_data.py)
   - Generation of **embeddings**: [`python src/data/embeddings/openai_embeddings.py`](./src/data/embeddings/openai_embeddings.py)
3. **Load to Supabase**: [`python src/data/upsert_supabase.py`](./src/data/upsert_supabase.py) - Upserts data to database.

Note: _New architecture in development, all the data treatment funcitons will be in the `./src/data/functions/` folder, and they will manage the progressive update of the data._

## Summary of Database Features

Key points from `./docs/database/README.md`:

- Scrape: Authentication, URL retrieval, HTML saving.
- Extract: Formating structured data from HTML to JSON.
- Transfrom: Text analysis through keywords extraction and generation of embeddings.
- Load: Supabase integration with upsert for franchises/contacts information.

---

## Project Organization

This project uses the **[cookiecutter-data-science](https://cookiecutter-data-science.drivendata.org/)** template.
