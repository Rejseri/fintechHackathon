"""
Script to update data.json:
1. Add "scanned": false field to each company
2. Clear all dummy values in promise and truth fields (keep keys, set to null)
"""

import json
from pathlib import Path

# Path to data.json
BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "data.json"

def clear_dummy_data():
    """Clear dummy data from data.json and add scanned field."""
    print(f"Loading data from {DATA_FILE}...")
    
    # Load the data
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    
    print(f"Found {len(data)} companies")
    
    # Process each company
    for ticker, company_data in data.items():
        print(f"\nProcessing {ticker} ({company_data.get('name', 'Unknown')})...")
        
        # Add scanned field
        company_data["scanned"] = False
        print(f"  Added 'scanned': false")
        
        # Clear promise values (keep keys, set to null)
        if "promise" in company_data:
            promise_keys = list(company_data["promise"].keys())
            company_data["promise"] = {key: None for key in promise_keys}
            print(f"  Cleared {len(promise_keys)} promise values")
        
        # Clear truth values (keep keys, set to false)
        if "truth" in company_data:
            truth_keys = list(company_data["truth"].keys())
            company_data["truth"] = {key: False for key in truth_keys}
            print(f"  Cleared {len(truth_keys)} truth values")
        
        # Clear sources field (set to empty array)
        company_data["sources"] = []
        print(f"  Cleared sources field (set to empty array)")
    
    # Save the updated data
    print(f"\nSaving updated data to {DATA_FILE}...")
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Done! All companies updated with:")
    print("  - 'scanned': false field added")
    print("  - Promise values cleared (set to null)")
    print("  - Truth values cleared (set to false)")
    print("  - Sources field ensured (empty array)")

if __name__ == "__main__":
    clear_dummy_data()

