import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import config as key

# --- 1. Pydantic Models (Your API's "Schema") ---
# These define the shape of your data.
# FastAPI uses them to validate requests and document your API.

class CompanyPortfolioItem(BaseModel):
    """A single company in the user's portfolio list."""
    name: str
    ticker: str


class DiscrepancySource(BaseModel):
    """A single news article or legal filing."""
    title: str
    url: str
    snippet: str


class DiscrepancyRisk(BaseModel):
    """The output of your LLM analysis."""
    score: float  # The 0-10 "hypocrisy score"
    explanation: str
    contradiction_found: bool


class CompanyAnalysis(BaseModel):
    """The full analysis response for a single company."""
    ticker: str
    company_name: str
    financial_data: Dict[str, Any]  # Flexible for any financial data
    discrepancy_risk: DiscrepancyRisk
    sources: List[DiscrepancySource]

def load_data(file_path):
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
    if not data:
        return []
    return [{"name": company["name"], "ticker": ticker} for ticker, company in data.items()]


MOCK_COMPANY_DB = load_data('../data/data.json')
MOCK_PORTFOLIO = extract_name_n_ticker(MOCK_COMPANY_DB)


def get_mock_llm_analysis(claim: str, evidence_list: List[Dict]) -> DiscrepancyRisk:
    """
    This MOCKS your LLM call from the previous step.
    It simulates the OpenAI API call based on the mock evidence.
    """
    if not evidence_list:
        return DiscrepancyRisk(
            score=0.5,  # Very low risk
            explanation="No significant contradictions found in public filings.",
            contradiction_found=False
        )

    # Mock a high-risk scenario
    mock_explanation = f"Direct contradiction found. Claim was '{claim[:50]}...' but evidence shows '{evidence_list[0]['title']}'."
    return DiscrepancyRisk(
        score=8.5,
        explanation=mock_explanation,
        contradiction_found=True
    )


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
    """
    return MOCK_PORTFOLIO


@app.get("/api/company/{ticker}",
         response_model=CompanyAnalysis,
         summary="Get detailed analysis for a single company")
async def get_company_analysis(ticker: str):
    """
    Takes a company ticker (e.g., 'TCO') and returns financial data,
    discrepancy risk, and supporting sources.
    """
    ticker_upper = ticker.upper()
    if not MOCK_COMPANY_DB or ticker_upper not in MOCK_COMPANY_DB:
        raise HTTPException(status_code=404, detail="Company ticker not found in mock database.")

    # Get data from our "database"
    company_data = MOCK_COMPANY_DB[ticker_upper]

    # 1. Simulate the LLM call
    claim = company_data["esg_claim"]
    evidence = company_data["evidence"]
    risk_analysis = get_mock_llm_analysis(claim, evidence)

    # 2. Format the sources into the Pydantic model
    sources = [DiscrepancySource(**source_data) for source_data in evidence]

    # 3. Assemble and return the final response
    return CompanyAnalysis(
        ticker=ticker_upper,
        company_name=company_data["name"],
        financial_data=company_data["financials"],
        discrepancy_risk=risk_analysis,
        sources=sources
    )


# --- 5. Run the App ---
if __name__ == "__main__":
    # This line allows you to run the file with "python main.py"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)