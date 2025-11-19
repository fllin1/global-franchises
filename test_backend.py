import requests
import json
import time

def test_analyze_lead():
    url = "http://localhost:8001/analyze-lead"
    
    # Wait for server to be ready
    print("Waiting for server...")
    for _ in range(10):
        try:
            requests.get("http://localhost:8001/docs")
            break
        except:
            time.sleep(1)
    
    # Test Case 1: Tier 1 Lead (Complete)
    print("\nTesting Tier 1 Lead...")
    notes_tier1 = "Client is looking for a fitness franchise. Has $150,000 in liquid capital. Wants to open in Austin, TX. Interested in semi-absentee ownership."
    response = requests.post(url, json={"notes": notes_tier1})
    if response.status_code == 200:
        print("Success!")
        data = response.json()
        print(json.dumps(data, indent=2))
        
        # Assertion for Match Narrative
        if data['status'] == 'complete':
            matches = data.get('matches', [])
            if matches:
                print(f"\nFound {len(matches)} matches.")
                first_match = matches[0]
                if 'why_narrative' in first_match and first_match['why_narrative']:
                    print(f"✅ Match Narrative verified: {first_match['why_narrative'][:100]}...")
                else:
                    print("❌ Match Narrative MISSING or empty!")
            else:
                print("⚠️ No matches found to verify narrative.")
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
