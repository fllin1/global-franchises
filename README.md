# Global Franchises

A short description of the project.

## Setup Instructions

This project used a Conda environment with Python 3.12 version.

1. **Install Dependencies**: Use Poetry to install required packages:

   ```bash
   pip install -e .
   poetry install
   ```

2. **Environment Variables**: Create a `.env` file in the project root with:

   ```text
   FRANSERVE_EMAIL=your_email
   FRANSERVE_PASSWORD=your_password
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

3. **Virtual Environment**: Activate with `poetry shell`.

## Execution Order

Run scripts in this order to process data:

1. **Scrape Data**: `python src/data/franserve/scrapper.py` - Fetches and saves raw HTML.
2. **Parse Data**: `python src/data/franserve/html_formatter.py` - Converts HTML to JSON.
3. **Upload to Supabase**: `python src/data/upsert_supabase.py` - Upserts data to database.

## Summary of Database Features

Key points from `./docs/database/README.md`:

- Scraping: Authentication, URL retrieval, HTML saving.
- Parsing: Extract structured data to JSON.
- Uploading: Supabase integration with upsert for franchises/contacts.
- Scripts: scrapper.py, html_formatter.py, upsert_supabase.py.

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
