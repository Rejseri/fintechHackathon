// API configuration and utility functions

const API_BASE_URL = 'http://localhost:8000';

/**
 * Fetch portfolio companies from backend
 */
export const fetchPortfolio = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/portfolio`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching portfolio:', error);
    throw error;
  }
};

/**
 * Fetch detailed company data by ticker
 */
export const fetchCompanyData = async (ticker) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/company/${ticker}`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Company with ticker ${ticker} not found`);
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error fetching company data for ${ticker}:`, error);
    throw error;
  }
};

/**
 * Add a new company to the portfolio
 * This will find the ESG report, download it, and run analysis
 */
export const addCompany = async (companyName, ticker = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/company`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        company_name: companyName,
        ticker: ticker
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error adding company:', error);
    throw error;
  }
};

