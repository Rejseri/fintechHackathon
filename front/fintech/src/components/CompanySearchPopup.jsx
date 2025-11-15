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
  const [currentStep, setCurrentStep] = useState(0);
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
    setCurrentStep(0);
    
    // Start step progression simulation
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < 1) return prev + 1; // Steps 0 and 1
        return prev;
      });
    }, 10000); // Change step every 10 seconds as approximation
    
    try {
      // Call the backend API to add the company
      // Ticker is optional - backend will generate if not provided
      const result = await addCompany(company.name, company.ticker || null);
      
      // Clear interval and mark all steps complete
      clearInterval(stepInterval);
      setCurrentStep(2); // All steps complete
      
      // Small delay to show completion, then close
      setTimeout(() => {
        onAddCompany(result);
        onClose();
      }, 500);
    } catch (err) {
      console.error('Error adding company:', err);
      clearInterval(stepInterval);
      setError(err.message || 'Failed to add company. Please try again.');
      setIsAdding(false);
      setAddingCompany(null);
      setCurrentStep(0);
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
    setCurrentStep(0);
    
    // Start step progression simulation
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < 1) return prev + 1; // Steps 0 and 1
        return prev;
      });
    }, 10000); // Change step every 10 seconds as approximation
    
    try {
      // Call the backend API to add the company
      const result = await addCompany(searchTerm.trim());
      
      // Clear interval and mark all steps complete
      clearInterval(stepInterval);
      setCurrentStep(2); // All steps complete
      
      // Small delay to show completion, then close
      setTimeout(() => {
        onAddCompany(result);
        onClose();
      }, 500);
    } catch (err) {
      console.error('Error adding company:', err);
      clearInterval(stepInterval);
      setError(err.message || 'Failed to add company. Please try again.');
      setIsAdding(false);
      setAddingCompany(null);
      setCurrentStep(0);
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
            <div className="emoji-loader-container">
              <div className="emoji-loader">⏳</div>
            </div>
            <h2>Adding {addingCompany}</h2>
            <p className="loading-subtitle">This may take a minute...</p>
            <div className="loading-steps">
              <div className={`loading-step ${currentStep >= 0 ? 'active' : ''} ${currentStep > 0 ? 'completed' : ''}`}>
                <div className="step-icon">🔍</div>
                <div className="step-content">
                  <div className="step-title">Finding ESG Report</div>
                  <div className="step-description">Searching for the latest sustainability report</div>
                </div>
                {currentStep > 0 && <div className="step-check">✓</div>}
              </div>
              <div className={`loading-step ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
                <div className="step-icon">📥</div>
                <div className="step-content">
                  <div className="step-title">Downloading PDF</div>
                  <div className="step-description">Saving ESG report to data folder</div>
                </div>
                {currentStep > 1 && <div className="step-check">✓</div>}
              </div>
              <div className={`loading-step ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
                <div className="step-icon">✅</div>
                <div className="step-content">
                  <div className="step-title">Company Added</div>
                  <div className="step-description">Ready for ESG analysis</div>
                </div>
                {currentStep > 2 && <div className="step-check">✓</div>}
              </div>
            </div>
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
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

