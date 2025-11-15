import { useState, useEffect, useRef } from 'react';
import { searchCompanies, getCompanyLogo } from '../data/companies';
import './CompanySearchPopup.css';

function CompanySearchPopup({ onClose, onAddCompany }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
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

  const handleAddCompany = (company) => {
    onAddCompany(company);
    onClose();
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="company-search-overlay" onClick={handleOverlayClick}>
      <div className="company-search-popup">
        <button className="close-button" onClick={onClose}>
          ×
        </button>
        <h2>Add Company to Portfolio</h2>
        <div className="search-container">
          <input
            ref={inputRef}
            type="text"
            className="search-input"
            placeholder="Search for a company (e.g., OpenAI, Google, Apple)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {isLoading && <div className="loading-spinner">Searching...</div>}
        </div>
        
        {results.length > 0 && (
          <div className="search-results">
            {results.map((company) => (
              <div key={company.domain} className="company-result-item">
                <div className="company-info">
                  <img
                    src={getCompanyLogo(company.domain)}
                    alt={company.name}
                    className="company-logo"
                    onError={(e) => {
                      // Fallback to a placeholder if logo fails to load
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

        {searchTerm.trim().length > 0 && results.length === 0 && !isLoading && (
          <div className="no-results">
            No companies found matching "{searchTerm}"
          </div>
        )}

        {searchTerm.trim().length === 0 && (
          <div className="search-hint">
            Start typing to search for companies...
          </div>
        )}
      </div>
    </div>
  );
}

export default CompanySearchPopup;

