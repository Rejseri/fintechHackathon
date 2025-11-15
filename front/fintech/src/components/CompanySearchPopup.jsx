import { useState, useEffect, useRef } from 'react';
import { searchCompanies, getCompanyLogo } from '../data/companies';
import { addCompany } from '../api/api';
import './CompanySearchPopup.css';

function CompanySearchPopup({ onClose, onAddCompany }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [addingCompany, setAddingCompany] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // Focus input when popup opens
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    // Debounce search
    const timer = setTimeout(() => {
      if (searchTerm.trim().length > 0) {
        setIsLoading(true);
        const searchResults = searchCompanies(searchTerm);
        setResults(searchResults);
        setIsLoading(false);
      } else {
        setResults([]);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  const handleAddCompany = async (company) => {
    setIsAdding(true);
    setAddingCompany(company.name);
    setError(null);
    
    try {
      // Call the backend API to add the company
      // Ticker is optional - backend will generate if not provided
      const result = await addCompany(company.name, company.ticker || null);
      
      // Success - notify parent and close
      onAddCompany(result);
      onClose();
    } catch (err) {
      console.error('Error adding company:', err);
      setError(err.message || 'Failed to add company. Please try again.');
      setIsAdding(false);
      setAddingCompany(null);
    }
  };

  const handleAddCustomCompany = async () => {
    if (!searchTerm.trim()) {
      setError('Please enter a company name');
      return;
    }

    setIsAdding(true);
    setAddingCompany(searchTerm.trim());
    setError(null);
    
    try {
      // Call the backend API to add the company
      const result = await addCompany(searchTerm.trim());
      
      // Success - notify parent and close
      onAddCompany(result);
      onClose();
    } catch (err) {
      console.error('Error adding company:', err);
      setError(err.message || 'Failed to add company. Please try again.');
      setIsAdding(false);
      setAddingCompany(null);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget && !isAdding) {
      onClose();
    }
  };

  return (
    <div className="company-search-overlay" onClick={handleOverlayClick}>
      <div className="company-search-popup">
        <button className="close-button" onClick={onClose} disabled={isAdding}>
          ×
        </button>
        <h2>Add Company to Portfolio</h2>
        <p className="search-subtitle">
          Enter any company name. We'll find their ESG report and analyze it.
        </p>
        <div className="search-container">
          <input
            ref={inputRef}
            type="text"
            className="search-input"
            placeholder="Enter company name (e.g., Microsoft, Apple, Tesla)..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setError(null);
            }}
            disabled={isAdding}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !isAdding && searchTerm.trim()) {
                handleAddCustomCompany();
              }
            }}
          />
          {isLoading && <div className="loading-spinner">Searching...</div>}
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {isAdding && (
          <div className="adding-status">
            <div className="loading-spinner-large">⏳</div>
            <p>Adding {addingCompany}...</p>
            <p className="status-detail">
              Finding ESG report and downloading PDF.
              Analysis will run automatically when you view the company.
            </p>
          </div>
        )}
        
        {!isAdding && results.length > 0 && (
          <div className="search-results">
            <p className="results-header">Suggested companies:</p>
            {results.map((company) => (
              <div key={company.domain} className="company-result-item">
                <div className="company-info">
                  <img
                    src={getCompanyLogo(company.domain)}
                    alt={company.name}
                    className="company-logo"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                  <div className="company-details">
                    <div className="company-name">{company.name}</div>
                    <div className="company-domain">{company.domain}</div>
                  </div>
                </div>
                <button
                  className="add-button"
                  onClick={() => handleAddCompany(company)}
                >
                  Add
                </button>
              </div>
            ))}
          </div>
        )}

        {!isAdding && searchTerm.trim().length > 0 && results.length === 0 && !isLoading && (
          <div className="add-custom-container">
            <div className="no-results">
              No suggestions found for "{searchTerm}"
            </div>
            <button
              className="add-custom-button"
              onClick={handleAddCustomCompany}
            >
              Add "{searchTerm}" Anyway
            </button>
            <p className="custom-hint">
              We'll search for their ESG report and add them to your portfolio.
            </p>
          </div>
        )}

        {!isAdding && searchTerm.trim().length === 0 && (
          <div className="search-hint">
            Enter a company name above, or choose from suggestions when available.
          </div>
        )}
      </div>
    </div>
  );
}

export default CompanySearchPopup;

