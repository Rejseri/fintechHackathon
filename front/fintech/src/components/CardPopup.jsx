import { useState, useEffect } from 'react';
import { fetchCompanyData } from '../api/api';
import './CardPopup.css';

function CardPopup({ ticker, onClose }) {
  const [companyData, setCompanyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedMetric, setSelectedMetric] = useState(null);

  useEffect(() => {
    let stepInterval = null;
    let isMounted = true;
    
    const loadCompanyData = async () => {
      if (!ticker) return;
      
      try {
        setLoading(true);
        setError(null);
        setCurrentStep(0);
        
        // Simulate step progression (this will be approximate since we can't track backend progress)
        stepInterval = setInterval(() => {
          if (isMounted) {
            setCurrentStep(prev => {
              if (prev < 2) return prev + 1;
              return prev;
            });
          }
        }, 15000); // Change step every 15 seconds as approximation
        
        const data = await fetchCompanyData(ticker);
        if (stepInterval) {
          clearInterval(stepInterval);
          stepInterval = null;
        }
        if (isMounted) {
          setCurrentStep(3); // All steps complete
          setCompanyData(data);
        }
      } catch (err) {
        console.error('Error loading company data:', err);
        if (isMounted) {
          setError(err.message || 'Failed to load company data');
        }
      } finally {
        if (stepInterval) {
          clearInterval(stepInterval);
          stepInterval = null;
        }
        if (isMounted) {
          setLoading(false);
          setCurrentStep(0);
        }
      }
    };

    loadCompanyData();
    
    // Cleanup function
    return () => {
      isMounted = false;
      if (stepInterval) {
        clearInterval(stepInterval);
      }
    };
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
      metricKey: key,
      metric: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      verified: value
    }));
  };

  // Get sources for a specific metric
  const getSourcesForMetric = (metricKey) => {
    if (!companyData?.metric_sources) return [];
    return companyData.metric_sources[metricKey] || [];
  };

  // Handle metric click to show sources
  const handleMetricClick = (metricKey) => {
    const sources = getSourcesForMetric(metricKey);
    if (sources.length > 0) {
      setSelectedMetric({ metricKey, sources });
    }
  };

  return (
    <div className="popup-overlay" onClick={handleOverlayClick}>
      <div className="popup-content">
        <button className="close-button" onClick={onClose}>
          ×
        </button>
        
        {loading ? (
          <div className="popup-loading">
            <div className="emoji-loader-container">
              <div className="emoji-loader">⏳</div>
            </div>
            <h2>Analyzing ESG Report</h2>
            <p className="loading-subtitle">This may take a minute...</p>
            <div className="loading-steps">
              <div className={`loading-step ${currentStep >= 0 ? 'active' : ''} ${currentStep > 0 ? 'completed' : ''}`}>
                <div className="step-icon">📄</div>
                <div className="step-content">
                  <div className="step-title">Extracting Promises</div>
                  <div className="step-description">Reading ESG report and identifying commitments</div>
                </div>
                {currentStep > 0 && <div className="step-check">✓</div>}
              </div>
              <div className={`loading-step ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
                <div className="step-icon">📊</div>
                <div className="step-content">
                  <div className="step-title">Calculating Metrics</div>
                  <div className="step-description">Computing derived ESG metrics</div>
                </div>
                {currentStep > 1 && <div className="step-check">✓</div>}
              </div>
              <div className={`loading-step ${currentStep >= 2 ? 'active' : ''} ${currentStep > 2 ? 'completed' : ''}`}>
                <div className="step-icon">🔍</div>
                <div className="step-content">
                  <div className="step-title">Validating Claims</div>
                  <div className="step-description">Verifying promises against public data</div>
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
                {getFormattedTruths().map((truth, index) => {
                  const sources = getSourcesForMetric(truth.metricKey);
                  const hasSources = sources.length > 0;
                  return (
                    <li 
                      key={index} 
                      className={`${truth.verified ? 'truth-positive' : 'truth-negative'} ${hasSources ? 'clickable-metric' : ''}`}
                      onClick={() => hasSources && handleMetricClick(truth.metricKey)}
                      style={hasSources ? { cursor: 'pointer' } : {}}
                    >
                      <strong>{truth.metric}:</strong> {truth.verified ? 'Verified ✓' : 'Not Verified ✗'}
                      {hasSources && <span className="sources-indicator"> ({sources.length} source{sources.length !== 1 ? 's' : ''})</span>}
                    </li>
                  );
                })}
              </ul>
            </div>

            {/* Sources Modal */}
            {selectedMetric && (
              <div className="sources-modal-overlay" onClick={() => setSelectedMetric(null)}>
                <div className="sources-modal" onClick={(e) => e.stopPropagation()}>
                  <div className="sources-modal-header">
                    <h3>Sources for Verification</h3>
                    <button className="sources-modal-close" onClick={() => setSelectedMetric(null)}>×</button>
                  </div>
                  <div className="sources-modal-content">
                    <p className="sources-metric-name">
                      {selectedMetric.metricKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </p>
                    <ul className="sources-modal-list">
                      {selectedMetric.sources.map((source, index) => (
                        <li key={index} className="source-item">
                          <a 
                            href={source.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="source-link"
                          >
                            <span className="source-title">{source.description || source.url}</span>
                            <span className="source-url">{source.url}</span>
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

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

