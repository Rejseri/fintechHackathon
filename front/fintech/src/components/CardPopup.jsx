import { useState, useEffect } from 'react';
import { fetchCompanyData } from '../api/api';
import './CardPopup.css';

function CardPopup({ ticker, onClose }) {
  const [companyData, setCompanyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadCompanyData = async () => {
      if (!ticker) return;
      
      try {
        setLoading(true);
        setError(null);
        const data = await fetchCompanyData(ticker);
        setCompanyData(data);
      } catch (err) {
        console.error('Error loading company data:', err);
        setError(err.message || 'Failed to load company data');
      } finally {
        setLoading(false);
      }
    };

    loadCompanyData();
  }, [ticker]);

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!ticker) return null;

  // Format promise metrics for display (show first 10 as sample metrics)
  const getSampleMetrics = () => {
    if (!companyData?.promise) return {};
    const entries = Object.entries(companyData.promise).slice(0, 10);
    return Object.fromEntries(entries);
  };

  // Format promises for display (show metric names with values)
  const getFormattedPromises = () => {
    if (!companyData?.promise) return [];
    return Object.entries(companyData.promise).slice(0, 20).map(([key, value]) => ({
      metric: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      value: value
    }));
  };

  // Format truths for display (show metrics where truth is true/false)
  const getFormattedTruths = () => {
    if (!companyData?.truth) return [];
    return Object.entries(companyData.truth).slice(0, 20).map(([key, value]) => ({
      metric: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      verified: value
    }));
  };

  return (
    <div className="popup-overlay" onClick={handleOverlayClick}>
      <div className="popup-content">
        <button className="close-button" onClick={onClose}>
          ×
        </button>
        
        {loading ? (
          <div className="popup-loading">
            <h2>Loading company data...</h2>
          </div>
        ) : error ? (
          <div className="popup-error">
            <h2>Error</h2>
            <p>{error}</p>
          </div>
        ) : companyData ? (
          <>
            <div className="popup-header">
              <h2>{companyData.name}</h2>
              <p className="popup-ticker">Ticker: {companyData.ticker}</p>
            </div>
            
            <p className="popup-description">
              ESG Report: {companyData.esg_report}
            </p>
            
            <div className="metrics-section">
              <h3>Sample ESG Metrics</h3>
              <div className="metrics-grid">
                {Object.entries(getSampleMetrics()).map(([key, value]) => (
                  <div key={key} className="metric-item">
                    <span className="metric-label">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                    <span className="metric-value">{value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="promises-section">
              <h3>ESG Promises & Metrics</h3>
              <ul className="promises-list">
                {getFormattedPromises().map((promise, index) => (
                  <li key={index}>
                    <strong>{promise.metric}:</strong> {promise.value}
                  </li>
                ))}
              </ul>
            </div>

            <div className="truths-section">
              <h3>Truth Verification</h3>
              <ul className="truths-list">
                {getFormattedTruths().map((truth, index) => (
                  <li 
                    key={index} 
                    className={truth.verified ? 'truth-positive' : 'truth-negative'}
                  >
                    <strong>{truth.metric}:</strong> {truth.verified ? 'Verified ✓' : 'Not Verified ✗'}
                  </li>
                ))}
              </ul>
            </div>

            {companyData.sources && companyData.sources.length > 0 && (
              <div className="sources-section">
                <h3>Sources</h3>
                <ul className="sources-list">
                  {companyData.sources.map((source, index) => (
                    <li key={index}>
                      <a href={source.url} target="_blank" rel="noopener noreferrer">
                        {source.description || source.url}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}

export default CardPopup;

