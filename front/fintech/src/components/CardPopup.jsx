import { getCompanyLogo } from '../data/companies';
import './CardPopup.css';

function CardPopup({ card, onClose }) {
  if (!card) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const logoUrl = card.logo || (card.company ? getCompanyLogo(card.company.domain) : null);

  return (
    <div className="popup-overlay" onClick={handleOverlayClick}>
      <div className="popup-content">
        <button className="close-button" onClick={onClose}>
          ×
        </button>
        <div className="popup-header">
          {logoUrl && (
            <img 
              src={logoUrl} 
              alt={card.title} 
              className="popup-logo"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          )}
          <h2>{card.title}</h2>
        </div>
        <p className="popup-description">{card.details.description}</p>
        
        <div className="metrics-section">
          <h3>Key Metrics</h3>
          <div className="metrics-grid">
            {Object.entries(card.details.metrics).map(([key, value]) => (
              <div key={key} className="metric-item">
                <span className="metric-label">{key}</span>
                <span className="metric-value">{value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="promises-section">
          <h3>Promises</h3>
          <ul className="promises-list">
            {card.details.promises && card.details.promises.map((promise, index) => (
              <li key={index}>{promise}</li>
            ))}
          </ul>
        </div>

        <div className="truths-section">
          <h3>Truths</h3>
          <ul className="truths-list">
            {card.details.truths && card.details.truths.map((truth, index) => (
              <li key={index} className={truth.positive ? 'truth-positive' : 'truth-negative'}>
                {truth.text}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default CardPopup;

