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

- Scraping: Authentication, URL retrieval, HTML saving.
- Parsing: Extract structured data to JSON.
- Uploading: Supabase integration with upsert for franchises/contacts.
- Scripts: scrapper.py, html_formatter.py, upsert_supabase.py.

## Go High Level Conversations

### Run GHL

Complete `./.env` file:

```txt
GHL_TOKEN="your_go_high_level_token"
GHL_LOCATION_ID="your_location_id"
```

Run scripts in this order to GET Go High Level's conversations and upsert to Supabase:

1. **Fetch Conversations**: `python src/ghl/get_messages.py` - Get messages from conversations.
2. **Upload to Supabase**: `python src/ghl/load_ghl_to_supabase.py` - Upserts data to database.

---

## Project Organization

```text
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for
│                         src and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── src   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes src a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling
    │   ├── __init__.py
    │   ├── predict.py          <- Code to run model inference with trained models
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```
