import requests
import json

def test_analyze_lead():
    url = "http://localhost:8000/analyze-lead"
    
    # Test Case 1: Tier 1 Lead (Complete)
    print("\nTesting Tier 1 Lead...")
    notes_tier1 = "Client is looking for a fitness franchise. Has $150,000 in liquid capital. Wants to open in Austin, TX. Interested in semi-absentee ownership."
    response = requests.post(url, json={"notes": notes_tier1})
    if response.status_code == 200:
        print("Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Failed: {response.text}")

    # Test Case 2: Tier 2 Lead (Incomplete - Missing Liquidity)
    print("\nTesting Tier 2 Lead...")
    notes_tier2 = "Client wants a coffee shop. Loves coffee. Located in Seattle."
    response = requests.post(url, json={"notes": notes_tier2})
    if response.status_code == 200:
        print("Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Failed: {response.text}")

if __name__ == "__main__":
    try:
        test_analyze_lead()
    except Exception as e:
        print(f"Test failed: {e}")

