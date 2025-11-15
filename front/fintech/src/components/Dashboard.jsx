import { useState, useEffect } from 'react';
import CardPopup from './CardPopup';
import CompanySearchPopup from './CompanySearchPopup';
import { getCompanyLogo } from '../data/companies';
import './Dashboard.css';

// Helper function to generate card data from company
const generateCardFromCompany = (company, id) => {
  // Generate some sample metrics based on company
  const sampleMetrics = {
    'Market Cap': `$${(Math.random() * 100 + 10).toFixed(1)}B`,
    'Revenue': `$${(Math.random() * 50 + 5).toFixed(1)}B`,
    'Employees': `${Math.floor(Math.random() * 50000 + 1000).toLocaleString()}`,
    'Growth Rate': `+${(Math.random() * 30 + 5).toFixed(1)}%`
  };

  const samplePromises = [
    'Commitment to sustainable growth',
    'Innovation-driven product development',
    'Customer-first approach',
    'Transparent business practices',
    'Long-term value creation'
  ];

  // Generate truths with random positive/negative status
  const sampleTruths = [
    { text: 'ESG compliance score above industry average', positive: Math.random() > 0.3 },
    { text: 'Recent regulatory filings show strong financial health', positive: Math.random() > 0.4 },
    { text: 'Market share has been declining over the past quarter', positive: false },
    { text: 'Employee satisfaction ratings are at record highs', positive: Math.random() > 0.3 },
    { text: 'Supply chain disruptions affecting production capacity', positive: false }
  ];

  return {
    id,
    title: company.name,
    company: company,
    overview: `${company.name} is a leading company in their industry`,
    thumbnail: company.domain,
    logo: getCompanyLogo(company.domain),
    details: {
      description: `${company.name} (${company.domain}) is a prominent company with strong market presence and innovative solutions.`,
      metrics: sampleMetrics,
      promises: samplePromises,
      truths: sampleTruths
    }
  };
};

function Dashboard({ onSignOut }) {
  const [companies, setCompanies] = useState([]);
  const [selectedCard, setSelectedCard] = useState(null);
  const [showCompanySearch, setShowCompanySearch] = useState(false);

  // Load companies from localStorage on mount
  useEffect(() => {
    const savedCompanies = localStorage.getItem('portfolioCompanies');
    if (savedCompanies) {
      try {
        const parsed = JSON.parse(savedCompanies);
        setCompanies(parsed);
      } catch (e) {
        console.error('Error loading companies:', e);
      }
    }
  }, []);

  // Save companies to localStorage whenever companies change
  useEffect(() => {
    if (companies.length > 0) {
      localStorage.setItem('portfolioCompanies', JSON.stringify(companies));
    }
  }, [companies]);

  const handleCardClick = (card) => {
    setSelectedCard(card);
  };

  const handleClosePopup = () => {
    setSelectedCard(null);
  };

  const handleAddCompany = (company) => {
    // Check if company already exists
    const exists = companies.some(c => c.domain === company.domain);
    if (exists) {
      alert(`${company.name} is already in your portfolio!`);
      return;
    }

    const newId = companies.length > 0 
      ? Math.max(...companies.map(c => c.id)) + 1 
      : 1;
    
    const newCompany = {
      id: newId,
      name: company.name,
      domain: company.domain
    };

    setCompanies([...companies, newCompany]);
  };

  // Convert companies to card data
  const cardData = companies.map(company => generateCardFromCompany(company, company.id));

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
      
      {cardData.length === 0 ? (
        <div className="empty-portfolio">
          <div className="empty-portfolio-content">
            <h2>Your portfolio is empty</h2>
            <p>Start building your portfolio by adding companies</p>
            <button 
              onClick={() => setShowCompanySearch(true)} 
              className="add-company-button-large"
            >
              + Add Your First Company
            </button>
          </div>
        </div>
      ) : (
        <div className="cards-grid">
          {cardData.map((card) => (
            <div
              key={card.id}
              className="card"
              onClick={() => handleCardClick(card)}
            >
              {card.logo && (
                <img 
                  src={card.logo} 
                  alt={card.title} 
                  className="card-logo"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              )}
              <h2>{card.title}</h2>
              <p className="card-overview">{card.overview}</p>
              <div className="card-thumbnail">{card.thumbnail}</div>
            </div>
          ))}
        </div>
      )}

      {selectedCard && (
        <CardPopup card={selectedCard} onClose={handleClosePopup} />
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

