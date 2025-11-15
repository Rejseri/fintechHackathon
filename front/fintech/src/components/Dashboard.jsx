import { useState, useEffect } from 'react';
import CardPopup from './CardPopup';
import CompanySearchPopup from './CompanySearchPopup';
import { fetchPortfolio } from '../api/api';
import './Dashboard.css';

function Dashboard({ onSignOut }) {
  const [companies, setCompanies] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [showCompanySearch, setShowCompanySearch] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load companies from backend on mount
  useEffect(() => {
    const loadPortfolio = async () => {
      try {
        setLoading(true);
        setError(null);
        const portfolio = await fetchPortfolio();
        setCompanies(portfolio);
      } catch (err) {
        console.error('Error loading portfolio:', err);
        setError('Failed to load portfolio. Please make sure the backend is running.');
      } finally {
        setLoading(false);
      }
    };

    loadPortfolio();
  }, []);

  const handleCardClick = (ticker) => {
    setSelectedTicker(ticker);
  };

  const handleClosePopup = () => {
    setSelectedTicker(null);
  };

  const handleAddCompany = async (company) => {
    // Company has been added by the backend
    // Refresh the portfolio to show the new company
    try {
      const portfolio = await fetchPortfolio();
      setCompanies(portfolio);
      // Optionally show a success message
      console.log(`Successfully added ${company.name} (${company.ticker})`);
    } catch (err) {
      console.error('Error refreshing portfolio:', err);
      // Still show success since the company was added
      alert(`Company ${company.name} has been added! Please refresh the page to see it.`);
    }
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-left">
          <div className="header-title-section">
            <h1>Portfolio</h1>
            <span className="header-subtitle">Manage your investments</span>
          </div>
        </div>
        <div className="header-actions">
          <button 
            onClick={() => setShowCompanySearch(true)} 
            className="add-company-button"
          >
            <span className="button-icon">+</span>
            Add Company
          </button>
          <button 
            className="contagion-button"
            onClick={() => {
              // Placeholder for future functionality
            }}
          >
            Contagion
          </button>
          <button onClick={onSignOut} className="signout-button">
            Sign Out
          </button>
        </div>
      </header>
      
      {loading ? (
        <div className="empty-portfolio">
          <div className="empty-portfolio-content">
            <h2>Loading portfolio...</h2>
          </div>
        </div>
      ) : error ? (
        <div className="empty-portfolio">
          <div className="empty-portfolio-content">
            <h2>Error</h2>
            <p>{error}</p>
          </div>
        </div>
      ) : companies.length === 0 ? (
        <div className="empty-portfolio">
          <div className="empty-portfolio-content">
            <h2>Your portfolio is empty</h2>
            <p>No companies found in the portfolio</p>
          </div>
        </div>
      ) : (
        <div className="cards-grid">
          {companies.map((company) => (
            <div
              key={company.ticker}
              className="card"
              onClick={() => handleCardClick(company.ticker)}
            >
              <h2>{company.name}</h2>
              <p className="card-overview">{company.name} - {company.ticker}</p>
              <div className="card-thumbnail">{company.ticker}</div>
            </div>
          ))}
        </div>
      )}

      {selectedTicker && (
        <CardPopup ticker={selectedTicker} onClose={handleClosePopup} />
      )}

      {showCompanySearch && (
        <CompanySearchPopup
          onClose={() => setShowCompanySearch(false)}
          onAddCompany={handleAddCompany}
        />
      )}
    </div>
  );
}

export default Dashboard;

