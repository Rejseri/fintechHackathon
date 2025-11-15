import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import os
import traceback
import pypdfium2 as pdfium
import aiwrapper

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
    metric_sources: Optional[Dict[str, List[Source]]] = {}  # Sources per metric


# Define base directory paths (needed by helper functions)
BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "data.json"


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


def save_data(file_path: str, data: Dict[str, Any]) -> bool:
    """Save JSON data to file."""
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)
        return True
    except Exception as e:
        print(f"Error saving data to file: {e}")
        return False


def read_pdf_text(pdf_filename: str) -> str:
    """Extract text from a PDF file in the data directory."""
    # Use os.path.join like promise.py does for compatibility
    pdf_path = os.path.join(str(BASE_DIR), "data", pdf_filename)
    
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    text = ""
    doc = None
    try:
        # pypdfium2 doesn't support context manager in this version, so open directly
        doc = pdfium.PdfDocument(pdf_path)
        for page in doc:
            textpage = page.get_textpage()
            text += textpage.get_text_range()
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"Error reading PDF {pdf_filename}: {e}")
        print(f"Full traceback:\n{error_traceback}")
        raise Exception(f"Error reading PDF {pdf_filename}: {e}")
    finally:
        # Clean up: close the document if it was opened
        if doc is not None:
            try:
                doc.close()
            except:
                pass
    
    return text


def process_company_analysis(ticker: str, company_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process ESG report analysis for a company if not already scanned.
    Returns updated company data.
    """
    # Check if already scanned
    if company_data.get("scanned", False):
        print(f"Company {ticker} already scanned, skipping analysis.")
        return company_data
    
    print(f"Processing ESG analysis for {ticker} ({company_data.get('name', 'Unknown')})...")
    
    # Get PDF filename from company data
    pdf_filename = company_data.get("esg_report", "")
    if not pdf_filename:
        raise ValueError(f"No ESG report PDF specified for {ticker}")
    
    # Extract text from PDF
    print(f"  Extracting text from {pdf_filename}...")
    esg_text = read_pdf_text(pdf_filename)
    
    # Process the ESG report using aiwrapper
    print(f"  Running ESG analysis workflow...")
    try:
        result = aiwrapper.process_esg_report(esg_text, company_data)
        
        # Validate result structure
        if not isinstance(result, dict):
            raise ValueError(f"process_esg_report returned invalid result type: {type(result)}")
        if "promise" not in result or "truth" not in result:
            raise ValueError(f"process_esg_report result missing required fields. Got keys: {list(result.keys())}")
        
        # Update company data with results, preserving all original keys
        # Merge promise values (update existing keys, keep others)
        original_promise = company_data.get("promise", {})
        new_promise = result.get("promise", {})
        original_promise.update(new_promise)  # This updates existing keys and adds new ones
        company_data["promise"] = original_promise
        
        # Merge truth values (update existing keys, keep others)
        original_truth = company_data.get("truth", {})
        new_truth = result.get("truth", {})
        original_truth.update(new_truth)  # This updates existing keys and adds new ones
        company_data["truth"] = original_truth
        
        # Merge sources (combine and deduplicate by URL)
        original_sources = company_data.get("sources", [])
        new_sources = result.get("sources", [])
        # Create a set of existing URLs for deduplication
        existing_urls = {source.get("url", "") for source in original_sources if isinstance(source, dict)}
        # Add new sources that don't already exist
        for source in new_sources:
            if isinstance(source, dict):
                url = source.get("url", "")
                if url and url not in existing_urls:
                    original_sources.append(source)
                    existing_urls.add(url)
        company_data["sources"] = original_sources
        
        # Merge metric_sources (map of metric names to their sources)
        original_metric_sources = company_data.get("metric_sources", {})
        new_metric_sources = result.get("metric_sources", {})
        # Merge metric sources, preserving existing and adding new
        for metric_key, sources in new_metric_sources.items():
            if metric_key in original_metric_sources:
                # Merge sources for this metric, deduplicating by URL
                existing_metric_urls = {s.get("url", "") for s in original_metric_sources[metric_key] if isinstance(s, dict)}
                for source in sources:
                    if isinstance(source, dict):
                        url = source.get("url", "")
                        if url and url not in existing_metric_urls:
                            original_metric_sources[metric_key].append(source)
                            existing_metric_urls.add(url)
            else:
                # New metric, add all its sources
                original_metric_sources[metric_key] = sources
        company_data["metric_sources"] = original_metric_sources
        
        company_data["scanned"] = True
        
        print(f"  Analysis complete for {ticker}")
        
        # Save updated data to file
        if COMPANY_DB:
            COMPANY_DB[ticker] = company_data
            save_data(str(DATA_FILE), COMPANY_DB)
            print(f"  Saved updated data to {DATA_FILE}")
        
        return company_data
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"  Error processing ESG analysis for {ticker}: {e}")
        print(f"  Full traceback:\n{error_traceback}")
        raise Exception(f"Error processing ESG analysis: {str(e)}\n{error_traceback}")


# Load data from data/data.json
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
    
    If the company has not been scanned yet, this endpoint will:
    1. Extract text from the ESG report PDF
    2. Run the ESG analysis workflow (extract promises, calculate metrics, validate)
    3. Update data.json with the results
    4. Mark the company as scanned
    """
    ticker_upper = ticker.upper()
    if not COMPANY_DB or ticker_upper not in COMPANY_DB:
        raise HTTPException(
            status_code=404, 
            detail=f"Company ticker '{ticker_upper}' not found in database."
        )

    # Get data from our database
    company_data = COMPANY_DB[ticker_upper]
    
    # Check if company needs to be scanned and process if needed
    if not company_data.get("scanned", False):
        try:
            company_data = process_company_analysis(ticker_upper, company_data)
            # Reload COMPANY_DB to get the latest data
            COMPANY_DB[ticker_upper] = company_data
        except Exception as e:
            error_msg = str(e)
            print(f"Exception in get_company_data for {ticker_upper}: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing ESG analysis for {ticker_upper}: {error_msg}"
            )

    # Format sources
    sources = [Source(**source) for source in company_data.get("sources", [])]
    
    # Format metric_sources (convert each metric's sources to Source objects)
    metric_sources = {}
    raw_metric_sources = company_data.get("metric_sources", {})
    for metric_key, metric_source_list in raw_metric_sources.items():
        if isinstance(metric_source_list, list):
            metric_sources[metric_key] = [Source(**s) if isinstance(s, dict) else s for s in metric_source_list]

    # Return the company data
    return CompanyData(
        ticker=ticker_upper,
        name=company_data["name"],
        esg_report=company_data["esg_report"],
        promise=company_data["promise"],
        truth=company_data["truth"],
        sources=sources,
        metric_sources=metric_sources
    )


# --- 5. Run the App ---
if __name__ == "__main__":
    # This line allows you to run the file with "python main.py"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)