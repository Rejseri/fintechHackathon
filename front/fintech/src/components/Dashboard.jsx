import { useState } from 'react';
import CardPopup from './CardPopup';
import './Dashboard.css';

// Sample card data
const cardData = [
  {
    id: 1,
    title: 'Financial Overview',
    overview: 'Total revenue increased by 15% this quarter',
    thumbnail: 'Revenue: $2.5M',
    details: {
      description: 'Comprehensive financial analysis showing strong growth across all sectors.',
      metrics: {
        'Total Revenue': '$2,500,000',
        'Growth Rate': '+15%',
        'Active Accounts': '12,450',
        'Profit Margin': '23%'
      },
      highlights: [
        'Record-breaking quarter performance',
        'Expansion into 3 new markets',
        'Customer retention rate at 94%'
      ]
    }
  },
  {
    id: 2,
    title: 'User Analytics',
    overview: 'Active users reached 50K milestone',
    thumbnail: 'Users: 50,000',
    details: {
      description: 'User engagement metrics showing significant growth in platform adoption.',
      metrics: {
        'Active Users': '50,000',
        'New Signups': '5,200',
        'Daily Active': '35,000',
        'Retention Rate': '87%'
      },
      highlights: [
        '50K milestone achieved',
        'Mobile app usage up 40%',
        'User satisfaction score: 4.8/5'
      ]
    }
  },
  {
    id: 3,
    title: 'Transaction Volume',
    overview: 'Processing 1M+ transactions monthly',
    thumbnail: 'Transactions: 1.2M',
    details: {
      description: 'Transaction processing statistics and performance metrics.',
      metrics: {
        'Monthly Volume': '1,200,000',
        'Success Rate': '99.8%',
        'Avg Processing Time': '0.3s',
        'Peak Hour Volume': '15,000/hr'
      },
      highlights: [
        'Zero downtime this quarter',
        'Processing speed improved by 25%',
        'Fraud detection rate: 99.9%'
      ]
    }
  },
  {
    id: 4,
    title: 'Market Trends',
    overview: 'Market capitalization up 30%',
    thumbnail: 'Market Cap: $45M',
    details: {
      description: 'Market analysis and trend indicators showing positive momentum.',
      metrics: {
        'Market Cap': '$45,000,000',
        'Growth': '+30%',
        'Market Share': '12%',
        'Valuation': '$180M'
      },
      highlights: [
        'Strong investor confidence',
        'Partnership with 5 major institutions',
        'Industry recognition award received'
      ]
    }
  },
  {
    id: 5,
    title: 'Security Metrics',
    overview: 'Zero security breaches this year',
    thumbnail: 'Security: 100%',
    details: {
      description: 'Comprehensive security monitoring and threat detection statistics.',
      metrics: {
        'Security Score': '100%',
        'Threats Blocked': '12,450',
        'Incidents': '0',
        'Compliance': '100%'
      },
      highlights: [
        'ISO 27001 certified',
        'SOC 2 Type II compliant',
        'Penetration testing passed'
      ]
    }
  },
  {
    id: 6,
    title: 'Customer Support',
    overview: 'Average response time under 2 minutes',
    thumbnail: 'Response: 1.8min',
    details: {
      description: 'Customer support performance and satisfaction metrics.',
      metrics: {
        'Avg Response Time': '1.8 minutes',
        'Resolution Rate': '95%',
        'Satisfaction Score': '4.9/5',
        'Tickets Resolved': '8,500'
      },
      highlights: [
        '24/7 support availability',
        'AI chatbot handles 60% of queries',
        'Customer satisfaction at all-time high'
      ]
    }
  }
];

function Dashboard({ onSignOut }) {
  const [selectedCard, setSelectedCard] = useState(null);

  const handleCardClick = (card) => {
    setSelectedCard(card);
  };

  const handleClosePopup = () => {
    setSelectedCard(null);
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Dashboard</h1>
        <button onClick={onSignOut} className="signout-button">
          Sign Out
        </button>
      </header>
      <div className="cards-grid">
        {cardData.map((card) => (
          <div
            key={card.id}
            className="card"
            onClick={() => handleCardClick(card)}
          >
            <h2>{card.title}</h2>
            <p className="card-overview">{card.overview}</p>
            <div className="card-thumbnail">{card.thumbnail}</div>
          </div>
        ))}
      </div>
      {selectedCard && (
        <CardPopup card={selectedCard} onClose={handleClosePopup} />
      )}
    </div>
  );
}

export default Dashboard;

