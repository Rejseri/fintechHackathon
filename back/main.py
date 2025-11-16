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
import requests
from openai import OpenAI
import config as key
import re
import cloudscraper

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
    metric_units: Optional[Dict[str, str]] = {}  # Units for scalar metrics


class AddCompanyRequest(BaseModel):
    """Request model for adding a new company."""
    company_name: str
    ticker: Optional[str] = None  # Optional, will be generated if not provided


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


# Initialize OpenAI client
openai_client = OpenAI(api_key=key.OPENAI_KEY)


def generate_ticker_from_name(company_name: str) -> str:
    """Generate a ticker symbol from company name (first 4 uppercase letters)."""
    # Remove common words and get first letters
    words = re.findall(r'\b[A-Za-z]+\b', company_name)
    if not words:
        # Fallback: use first 4 characters
        ticker = ''.join(c.upper() for c in company_name if c.isalnum())[:4]
    else:
        # Use first letters of words, up to 4 characters
        ticker = ''.join(w[0].upper() for w in words[:4])
        if len(ticker) < 2:
            # Fallback if too short
            ticker = ''.join(c.upper() for c in company_name if c.isalnum())[:4]
    return ticker[:4]  # Ensure max 4 characters


def create_company_template(ticker: str, name: str, esg_report_filename: str) -> Dict[str, Any]:
    """Create a template company entry with all required fields."""
    # Get template from existing company to ensure all fields are present
    if COMPANY_DB and len(COMPANY_DB) > 0:
        template_company = list(COMPANY_DB.values())[0]
        promise_template = template_company.get("promise", {})
        truth_template = template_company.get("truth", {})
    else:
        # Fallback: create minimal template (shouldn't happen if data.json exists)
        promise_template = {}
        truth_template = {}
    
    # Create new company entry with null/false values
    new_company = {
        "name": name,
        "esg_report": esg_report_filename,
        "promise": {k: None for k in promise_template.keys()},
        "truth": {k: False for k in truth_template.keys()},
        "sources": [],
        "scanned": False
    }
    
    return new_company


def find_esg_report_url(company_name: str, ticker: str) -> str:
    """Use OpenAI to find the latest ESG/sustainability report URL for a company."""
    prompt = f"""Find the direct download URL for the most recent ESG (Environmental, Social, Governance) or Sustainability report PDF for the company "{company_name}" (stock ticker: {ticker}).

Search the internet for:
- The company's official ESG report PDF
- Sustainability report PDF
- Corporate responsibility report PDF
- Annual sustainability report PDF
- CSR report PDF
- Environmental, Social, and Governance report PDF

IMPORTANT REQUIREMENTS:
1. The URL must be a DIRECT download link to a PDF file (ending in .pdf)
2. Prefer URLs from the company's official website (usually investor relations or sustainability section)
3. Look for the most recent report (2023, 2024, or latest available)
4. Common URL patterns: 
   - investor.[company].com/sustainability
   - [company].com/esg
   - [company].com/sustainability-report
   - [company].com/csr

If you find a page URL instead of a direct PDF link, try to construct the PDF URL based on common patterns, or return the page URL and we'll try to extract it.

Return ONLY the URL, nothing else. No explanations, no additional text."""

    try:
        response = openai_client.responses.create(
            model="gpt-5-nano",
            input=prompt,
            instructions="You are an expert at finding ESG report URLs. You have access to current web information. Return only valid URLs, no explanations.",
            tools=[{"type": "web_search"}]
        )
        
        url = response.output_text.strip()
        # Clean up the URL (remove quotes, markdown links, whitespace, etc.)
        url = url.strip('"\' \n\t')
        # Remove markdown link format [text](url) -> url
        if '](' in url:
            url = url.split('](')[-1].rstrip(')')
        url = url.strip('"\' \n\t')
        
        # Validate it looks like a URL
        if not url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL format returned: {url}")
        
        return url
    except Exception as e:
        raise Exception(f"Error finding ESG report URL: {str(e)}")


def download_pdf(url: str, filepath: str) -> bool:
    """Download a PDF from URL and save to filepath."""

    # Create a scraper instance
    scraper = cloudscraper.create_scraper()  # <-- Add this

    try:
        # These headers are now less critical,
        # as cloudscraper will add its own better ones, but
        # it's fine to keep them as a base.
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/pdf,application/octet-stream,*/*'
        }

        # Use the scraper instance instead of 'requests'
        # response = requests.get(...)  <-- Your old code
        response = scraper.get(url, headers=headers, stream=True, timeout=60,
                               allow_redirects=True)  # <-- Use scraper.get

        response.raise_for_status()

        # ... (The rest of your code is perfect and doesn't need to change)

        content_type = response.headers.get('Content-Type', '').lower()
        final_url = response.url
        is_pdf = 'pdf' in content_type or final_url.lower().endswith('.pdf')

        if not is_pdf:
            print(f"  Warning: URL doesn't appear to be a direct PDF link. Content-Type: {content_type}")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        try:
            test_doc = pdfium.PdfDocument(filepath)
            page_count = len(test_doc)
            test_doc.close()
            if page_count == 0:
                raise ValueError("PDF appears to be empty")
            print(f"  Successfully downloaded PDF with {page_count} pages")
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise ValueError(f"Downloaded file is not a valid PDF: {str(e)}")

        return True
    except Exception as e:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        raise Exception(f"Error downloading PDF: {str(e)}")


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
    global COMPANY_DB
    
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

    # Get metric units from aiwrapper
    metric_units = aiwrapper.METRIC_UNITS.copy()

    # Return the company data
    return CompanyData(
        ticker=ticker_upper,
        name=company_data["name"],
        esg_report=company_data["esg_report"],
        promise=company_data["promise"],
        truth=company_data["truth"],
        sources=sources,
        metric_sources=metric_sources,
        metric_units=metric_units
    )


@app.post("/api/company",
          response_model=CompanyPortfolioItem,
          summary="Add a new company to the portfolio")
def add_company(request: AddCompanyRequest):
    """
    Add a new company to the portfolio by:
    1. Finding the latest ESG report using OpenAI
    2. Downloading the PDF to data folder
    3. Creating company entry in data.json
    
    Note: ESG analysis will be performed automatically when the company data is first accessed.
    
    Returns the added company information.
    """
    global COMPANY_DB, PORTFOLIO
    
    try:
        # Generate or use provided ticker
        ticker = request.ticker.upper() if request.ticker else generate_ticker_from_name(request.company_name)
        ticker = ticker.upper()
        
        # Check if company already exists
        if COMPANY_DB and ticker in COMPANY_DB:
            raise HTTPException(
                status_code=400,
                detail=f"Company with ticker '{ticker}' already exists in the database."
            )
        
        print(f"\n{'='*60}")
        print(f"Adding new company: {request.company_name} ({ticker})")
        print(f"{'='*60}")
        
        # Step 1: Find ESG report URL using OpenAI
        print("Step 1: Finding ESG report URL...")
        try:
            esg_url = find_esg_report_url(request.company_name, ticker)
            print(f"  Found ESG report URL: {esg_url}")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to find ESG report URL: {str(e)}"
            )
        
        # Step 2: Download PDF
        print("Step 2: Downloading ESG report PDF...")
        esg_filename = f"{ticker}_ESG.pdf"
        pdf_path = BASE_DIR / "data" / esg_filename
        
        try:
            download_pdf(esg_url, str(pdf_path))
            print(f"  Downloaded PDF to: {pdf_path}")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to download PDF: {str(e)}"
            )
        
        # Step 3: Create company template entry
        print("Step 3: Creating company entry...")
        new_company = create_company_template(ticker, request.company_name, esg_filename)
        
        # Ensure scanned is False so analysis runs when company is accessed
        new_company["scanned"] = False
        
        # Step 4: Add to database
        if not COMPANY_DB:
            COMPANY_DB = {}
        COMPANY_DB[ticker] = new_company
        
        # Step 5: Save to file
        if not save_data(str(DATA_FILE), COMPANY_DB):
            raise HTTPException(
                status_code=500,
                detail="Failed to save company to database"
            )
        print(f"  Saved company entry to {DATA_FILE}")
        
        # Update portfolio list
        PORTFOLIO = extract_name_n_ticker(COMPANY_DB)
        
        print(f"{'='*60}")
        print(f"Successfully added company: {request.company_name} ({ticker})")
        print(f"  ESG report downloaded. Analysis will run when company data is accessed.")
        print(f"{'='*60}\n")
        
        return CompanyPortfolioItem(name=request.company_name, ticker=ticker)
        
    except HTTPException:
        raise
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"Error adding company: {str(e)}")
        print(f"Full traceback:\n{error_traceback}")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding company: {str(e)}"
        )


# --- 5. Run the App ---
if __name__ == "__main__":
    # This line allows you to run the file with "python main.py"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)