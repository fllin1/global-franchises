# Global Franchises

[![Licence](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](./LICENSE)

Global Franchises is a comprehensive platform that scrapes franchise information from FranServe, extracts meaningful insights, and provides a dashboard for brokers to match lead profiles with compatible franchises.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![Next.js](https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white) ![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)

Note: _Franserve is a private platform in the US for brokers_

*Project Prompt Count: 145*

## Setup Instructions

This project uses a Conda environment with Python 3.12 for the backend and Node.js for the frontend.

1. **Virtual Environment**: **[Conda](https://www.anaconda.com/docs/getting-started/miniconda/install#quickstart-install-instructions)** environment:

   ```bash
   conda create -n global_franchises python=3.12
   conda activate global_franchises
   ```

2. **Install Backend Dependencies**: Use **[Poetry](https://python-poetry.org/docs/)** to install required packages:

   ```bash
   pip install -e .
   poetry install
   ```

3. **Install Frontend Dependencies**: Navigate to the frontend directory:

   ```bash
   cd frontend
   npm install
   ```

4. **Environment Variables**: Create a `.env` file in the project root with:

   ```text
   FRANSERVE_EMAIL=your_email
   FRANSERVE_PASSWORD=your_password

   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key

   GEMINI_API_KEY=your_gemini_key
   OPENAI_API_KEY=your_openai_key
   ```

## Web Application

The project now includes a full-stack web application for interacting with the data.

### Backend API

Start the FastAPI backend server:

```bash
uvicorn src.backend.main:app --reload
```

The API will be available at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

### Frontend Dashboard

Start the Next.js development server:

```bash
cd frontend
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

### Features

- **Dashboard**:
  - **Lead Management**: Create, read, update, and delete lead profiles.
  - **Match Analysis**: View AI-generated compatibility narratives for each franchise match.
- **Territory Map**: Interactive map to search and filter franchises by state/territory availability.
- **Franchise Deep Dive**: Detailed views of franchise disclosure documents (FDD) and key metrics.

## Data Pipeline Execution

Run scripts in this order to process data (ETL):

0. **Scrape Data**: `python src/data/functions/extract.py` (via Extractor class) - Fetches and uploads raw HTML to Supabase Storage.
1. **Parse Data**: There are two ways to parse the data (Converts HTML from Storage to JSON):
   - The conventional method with rule-based parsing: `python src/data/functions/extract.py` (via rule_based_parsing method)
   - A more organic method that uses API calls with Google Genai library for AI-assisted parsing: [`python src/data/nlp/genai_data.py`](./src/data/nlp/genai_data.py) (reads from Storage)
2. **Extract Info**: To facilitate the matching of the franchises with profiles of future leads, we prepare the data in two ways:
   - Extraction of **keywords**: [`python src/data/nlp/genai_keywords.py`](./src/data/nlp/genai_keywords.py)
   - Generation of **embeddings**: [`python src/data/embeddings/openai_embeddings.py`](./src/data/embeddings/openai_embeddings.py)
3. **Load to Supabase**: [`python src/data/upsert_supabase.py`](./src/data/upsert_supabase.py) - Upserts data to database.

### Territory Availability Processing (GHL Replies)

To extract territory availability from franchise email replies in GoHighLevel (GHL):

```bash
python src/ghl/process_territory_replies.py
```

**Features:**
- **Message Filtering**: Automatically detects and skips outbound template messages.
- **Classification**: Identifies out-of-office auto-replies and messages with attachment mentions using Gemini LLM.
- **Extraction**: Parses message bodies to find structured territory availability data (Location, State, Status).
- **Integration**: Updates the `territory_checks` table directly for use in the dashboard.

Options:
- `--limit 100`: Process N messages (default 100).
- `--loop`: Run continuously, polling every minute.

Note: _New architecture in development, all the data treatment functions will be in the `./src/data/functions/` folder, and they will manage the progressive update of the data._

## Summary of Database Features

Key points from `./docs/database/README.md`:

- Scrape: Authentication, URL retrieval, HTML saving.
- Extract: Formating structured data from HTML to JSON.
- Transform: Text analysis through keywords extraction and generation of embeddings.
- Load: Supabase integration with upsert for franchises/contacts information.

---

## Project Organization

This project uses the **[cookiecutter-data-science](https://cookiecutter-data-science.drivendata.org/)** template, extended with a modern web stack:

- `src/backend/`: FastAPI backend application and API routers.
- `frontend/`: Next.js React frontend application.
- `src/data/`: Data processing pipelines (ETL).
- `notebooks/`: Jupyter notebooks for analysis and prototyping.
