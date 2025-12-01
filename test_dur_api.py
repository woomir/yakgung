import requests
import json

# Try Service02 (older version often works better)
BASE_URL = "http://apis.data.go.kr/1471000/DURCmptInfoService02/getUsjntTabooList"
# Encoded Key provided by user
ENCODED_KEY = "UpyO%2FrN1%2B4lHyJ6uqJOqWcpMTmnMh3ghQ5qqOHP%2FMftGPiCa9Y9mI4MQNXN9Jl1eX%2BsZTBPPtSD%2F%2F%2B8a7CtZzg%3D%3D"

def test_dur_api():
    print(f"🔬 Testing DUR API: {BASE_URL}")
    
    # Construct URL manually. Remove type=json to default to XML (often more stable)
    query_params = f"?serviceKey={ENCODED_KEY}&pageNo=1&numOfRows=3"
    full_url = BASE_URL + query_params
    
    print(f"Requesting: {full_url}")
    
    try:
        response = requests.get(full_url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("\n✅ JSON Parsing Successful:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print("\n⚠️ Response is not JSON. Raw Text:")
                print(response.text[:500])
        else:
            print(f"\n❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")

if __name__ == "__main__":
    test_dur_api()
