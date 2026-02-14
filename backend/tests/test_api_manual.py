import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_api():
    print("Fetching races...")
    try:
        resp = requests.get(f"{BASE_URL}/races")
        resp.raise_for_status()
        races = resp.json()
        
        if not races:
            print("No races found.")
            return

        race_id = races[0]['race_id']
        print(f"Testing prediction for race: {race_id} ({races[0]['name']})")
        
        url = f"{BASE_URL}/races/{race_id}/predict"
        print(f"POST {url}")
        
        pred_resp = requests.post(url)
        
        if pred_resp.status_code == 200:
            result = pred_resp.json()
            print("\nPrediction Success!")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\nPrediction Failed: {pred_resp.status_code}")
            print(pred_resp.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
