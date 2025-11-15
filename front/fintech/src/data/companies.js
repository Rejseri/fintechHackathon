// Popular companies database for search
export const companiesDatabase = [
  // Tech & AI
  { name: 'OpenAI', domain: 'openai.com' },
  { name: 'Google', domain: 'google.com' },
  { name: 'Apple', domain: 'apple.com' },
  { name: 'Microsoft', domain: 'microsoft.com' },
  { name: 'Amazon', domain: 'amazon.com' },
  { name: 'Meta', domain: 'meta.com' },
  { name: 'Tesla', domain: 'tesla.com' },
  { name: 'Netflix', domain: 'netflix.com' },
  { name: 'NVIDIA', domain: 'nvidia.com' },
  { name: 'AMD', domain: 'amd.com' },
  { name: 'Intel', domain: 'intel.com' },
  { name: 'IBM', domain: 'ibm.com' },
  { name: 'Oracle', domain: 'oracle.com' },
  { name: 'Adobe', domain: 'adobe.com' },
  { name: 'Salesforce', domain: 'salesforce.com' },
  { name: 'Shopify', domain: 'shopify.com' },
  { name: 'Zoom', domain: 'zoom.us' },
  { name: 'Slack', domain: 'slack.com' },
  { name: 'Dropbox', domain: 'dropbox.com' },
  { name: 'Atlassian', domain: 'atlassian.com' },
  { name: 'GitHub', domain: 'github.com' },
  { name: 'GitLab', domain: 'gitlab.com' },
  { name: 'Docker', domain: 'docker.com' },
  { name: 'Red Hat', domain: 'redhat.com' },
  { name: 'VMware', domain: 'vmware.com' },
  { name: 'Cisco', domain: 'cisco.com' },
  { name: 'HP', domain: 'hp.com' },
  { name: 'Dell', domain: 'dell.com' },
  { name: 'Samsung', domain: 'samsung.com' },
  { name: 'Sony', domain: 'sony.com' },
  { name: 'Nintendo', domain: 'nintendo.com' },
  
  // Fintech & Financial Services
  { name: 'Stripe', domain: 'stripe.com' },
  { name: 'PayPal', domain: 'paypal.com' },
  { name: 'Square', domain: 'square.com' },
  { name: 'Coinbase', domain: 'coinbase.com' },
  { name: 'Robinhood', domain: 'robinhood.com' },
  { name: 'Revolut', domain: 'revolut.com' },
  { name: 'N26', domain: 'n26.com' },
  { name: 'Chime', domain: 'chime.com' },
  { name: 'Plaid', domain: 'plaid.com' },
  { name: 'Visa', domain: 'visa.com' },
  { name: 'Mastercard', domain: 'mastercard.com' },
  { name: 'JPMorgan Chase', domain: 'jpmorganchase.com' },
  { name: 'Goldman Sachs', domain: 'goldmansachs.com' },
  { name: 'Morgan Stanley', domain: 'morganstanley.com' },
  { name: 'Bank of America', domain: 'bankofamerica.com' },
  { name: 'Wells Fargo', domain: 'wellsfargo.com' },
  { name: 'Citigroup', domain: 'citi.com' },
  
  // Consumer & Retail
  { name: 'Uber', domain: 'uber.com' },
  { name: 'Airbnb', domain: 'airbnb.com' },
  { name: 'Spotify', domain: 'spotify.com' },
  { name: 'Twitter', domain: 'twitter.com' },
  { name: 'LinkedIn', domain: 'linkedin.com' },
  { name: 'Walmart', domain: 'walmart.com' },
  { name: 'Target', domain: 'target.com' },
  { name: 'Costco', domain: 'costco.com' },
  { name: 'Home Depot', domain: 'homedepot.com' },
  { name: 'McDonald\'s', domain: 'mcdonalds.com' },
  { name: 'Starbucks', domain: 'starbucks.com' },
  { name: 'Coca-Cola', domain: 'coca-cola.com' },
  { name: 'Pepsi', domain: 'pepsi.com' },
  { name: 'Nike', domain: 'nike.com' },
  { name: 'Adidas', domain: 'adidas.com' },
  { name: 'Lululemon', domain: 'lululemon.com' },
  { name: 'Patagonia', domain: 'patagonia.com' },
  { name: 'The North Face', domain: 'thenorthface.com' },
  { name: 'Under Armour', domain: 'underarmour.com' },
  
  // Media & Entertainment
  { name: 'Disney', domain: 'disney.com' },
  { name: 'Warner Bros', domain: 'warnerbros.com' },
  
  // Automotive & Transportation
  { name: 'BMW', domain: 'bmw.com' },
  { name: 'Mercedes-Benz', domain: 'mercedes-benz.com' },
  { name: 'Volkswagen', domain: 'volkswagen.com' },
  { name: 'Ford', domain: 'ford.com' },
  { name: 'General Motors', domain: 'gm.com' },
  { name: 'Boeing', domain: 'boeing.com' },
  { name: 'Airbus', domain: 'airbus.com' },
  { name: 'FedEx', domain: 'fedex.com' },
  { name: 'UPS', domain: 'ups.com' },
  { name: 'DHL', domain: 'dhl.com' },
];

// Helper function to get logo URL using Clearbit's free logo API
export const getCompanyLogo = (domain) => {
  return `https://logo.clearbit.com/${domain}`;
};

// Search companies by name (case-insensitive, partial match)
export const searchCompanies = (searchTerm) => {
  if (!searchTerm || searchTerm.length < 1) {
    return [];
  }
  
  const term = searchTerm.toLowerCase().trim();
  return companiesDatabase.filter(company =>
    company.name.toLowerCase().includes(term) ||
    company.domain.toLowerCase().includes(term)
  ).slice(0, 10); // Limit to 10 results
};

