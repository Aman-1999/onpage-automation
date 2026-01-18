from analyzer import SEOAnalyzer
from data_manager import DataManager
import os

def test_system():
    print("Testing Data Manager...")
    dm = DataManager()
    dm.add_client("Test Client")
    dm.add_url("Test Client", {
        "url": "https://example.com",
        "primary_keyword": "example",
        "secondary_keywords": ["domain", "iana"],
        "status": "Pending",
        "priority": "High",
        "last_audit": "Never",
        "notes": ""
    })
    
    data = dm.load_data()
    if "Test Client" in data and len(data["Test Client"]) == 1:
        print("✅ Data Manager working.")
    else:
        print("❌ Data Manager failed.")

    print("\nTesting SEO Analyzer (Network Request)...")
    analyzer = SEOAnalyzer()
    # Test with example.com
    res = analyzer.analyze_url("https://example.com", "example", ["domain"])
    
    if res['Status_Code'] == 200:
        print(f"✅ Fetch Success (Status: {res['Status_Code']})")
        print(f"   Title: {res['Title']}")
        print(f"   Primary Found in Title: {res['Primary_in_Title']}")
        print(f"   Secondary Found in Content: {res['Secondary_in_Content_List']}")
    else:
        print(f"❌ Fetch Failed: {res['Status_Code']}")

    # Clean up
    print("\nCleaning up test data...")
    # We keep the file but maybe remove the test client if we wanted to be clean, 
    # but for now seeing it in the file validates persistence.

if __name__ == "__main__":
    test_system()
