import os
import requests
from datetime import datetime
import json

def test_resight_api(api_key: str, base_url: str = "https://api.resights.dk/api/v2"):
    """
    Simple function to test Resights API token validity and fetch valuation history.
    
    Args:
        api_key: Your Resights API token
        base_url: The API base URL (defaults to production URL)
        
    Returns:
        A dictionary with test results
    """
    # First, get the property ID using BFE number
    bfe_number = "100407981"
    
    property_url = f"{base_url.rstrip('/')}/properties?bfe_number={bfe_number}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    try:
        # Get property ID
        response = requests.get(property_url, headers=headers, timeout=30.0)
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Failed to get property ID: {response.status_code}",
                "details": response.json() if response.text else {"error": "No error details available"},
                "timestamp": datetime.now().isoformat()
            }
        
        property_data = response.json()
        property_id = property_data.get('data', [{}])[0].get('id')
        
        if not property_id:
            return {
                "status": "error",
                "message": "Could not find property ID in response",
                "details": property_data,
                "timestamp": datetime.now().isoformat()
            }
        
        # Now get valuation history using the property ID
        valuation_url = f"{base_url.rstrip('/')}/properties/{property_id}/valuations"
        valuation_response = requests.get(valuation_url, headers=headers, timeout=30.0)
        
        if valuation_response.status_code == 200:
            valuation_data = valuation_response.json()
            return {
                "status": "success",
                "message": "Successfully fetched valuation history",
                "property_data": property_data,
                "valuation_data": valuation_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            error_data = valuation_response.json() if valuation_response.text else {"error": "No error details available"}
            return {
                "status": "error",
                "message": f"Failed to get valuation history: {valuation_response.status_code}",
                "details": error_data,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"API test failed with exception",
            "details": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Example usage
if __name__ == "__main__":
    # Replace with your actual API key
    API_KEY = os.getenv("RESIGHT_API_KEY", "")
    
    if not API_KEY:
        print("Please set your API key in the RESIGHT_API_KEY environment variable")
        exit(1)
    
    result = test_resight_api(API_KEY)
    print(json.dumps(result, indent=2))
