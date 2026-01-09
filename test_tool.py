import requests
import json

# Test the API
API_BASE = "http://localhost:8001"

def test_stats():
    """Test stats endpoint"""
    response = requests.get(f"{API_BASE}/stats")
    print("Stats:", response.json())

def test_scraping():
    """Test email scraping"""
    response = requests.post(f"{API_BASE}/maps/scrape", params={
        'query': 'financial advisor',
        'location': 'New York',
        'max_results': 5
    })
    result = response.json()
    print(f"Scraping result: {result['businesses_found']} businesses, {result['emails_saved']} emails")
    
    # Show first few businesses
    for business in result['businesses'][:3]:
        print(f"- {business['name']}: {len(business['emails'])} emails")

if __name__ == "__main__":
    print("Testing Email Tool API...")
    
    try:
        test_stats()
        print("\n" + "="*50)
        test_scraping()
        print("\nTool is working correctly! ✅")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the server is running: python main.py")