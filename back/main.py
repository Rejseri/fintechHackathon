import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

# --- 1. Pydantic Models (Your API's "Schema") ---
# These define the shape of your data.
# FastAPI uses them to validate requests and document your API.

class CompanyPortfolioItem(BaseModel):
    """A single company in the user's portfolio list."""
    name: str
    ticker: str


class Source(BaseModel):
    """A single source reference."""
    url: str
    description: str


class CompanyData(BaseModel):
    """The full company data response."""
    ticker: str
    name: str
    esg_report: str
    promise: Dict[str, Any]  # ESG metrics with numeric values
    truth: Dict[str, bool]  # Boolean values for each metric
    sources: List[Source]


def load_data(file_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON data from file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print("Error: The file content is not valid JSON.")
        return None


def extract_name_n_ticker(data: Dict[str, Any]) -> List[CompanyPortfolioItem]:
    """Extract company name and ticker from data."""
    if not data:
        return []
    return [CompanyPortfolioItem(name=company["name"], ticker=ticker) 
            for ticker, company in data.items()]


# Load data from data/data.json (relative to back directory)
BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "data.json"
COMPANY_DB = load_data(str(DATA_FILE))
PORTFOLIO = extract_name_n_ticker(COMPANY_DB) if COMPANY_DB else []


# --- 3. FastAPI App & CORS ---
# Initialize the app
app = FastAPI(
    title="Corporate Lie Detector API",
    description="API for the ESG Hackathon Project",
    version="1.0.0"
)

# **CRITICAL FOR VITE:** Add CORS middleware
# This allows your Vite frontend (e.g., http://localhost:5173)
# to make requests to your FastAPI backend (http://localhost:8000).
origins = [
    "http://localhost",
    "http://localhost:5173",  # Default Vite dev server port
    "http://127.0.0.1:5173",
    # Add your production frontend URL here if you deploy
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],
)


# --- 4. API Endpoints ---

@app.get("/")
async def read_root():
    return {"message": "Welcome to the ESG Lie Detector API. Go to /docs to see endpoints."}


@app.get("/api/portfolio",
         response_model=List[CompanyPortfolioItem],
         summary="Get the user's company portfolio")
async def get_portfolio():
    """
    Retrieves a list of companies in the user's portfolio.
    Returns all companies from the data.json file.
    """
    return PORTFOLIO


@app.get("/api/company/{ticker}",
         response_model=CompanyData,
         summary="Get detailed data for a single company")
async def get_company_data(ticker: str):
    """
    Takes a company ticker (e.g., 'AKZA') and returns the full company data
    including promise metrics, truth values, and sources.
    """
    ticker_upper = ticker.upper()
    if not COMPANY_DB or ticker_upper not in COMPANY_DB:
        raise HTTPException(
            status_code=404, 
            detail=f"Company ticker '{ticker_upper}' not found in database."
        )

    # Get data from our database
    company_data = COMPANY_DB[ticker_upper]

    # Format sources
    sources = [Source(**source) for source in company_data.get("sources", [])]

    # Return the company data
    return CompanyData(
        ticker=ticker_upper,
        name=company_data["name"],
        esg_report=company_data["esg_report"],
        promise=company_data["promise"],
        truth=company_data["truth"],
        sources=sources
    )


# --- 5. Run the App ---
if __name__ == "__main__":
    # This line allows you to run the file with "python main.py"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)