import requests
import json

# e-Drug API Base URL
# This is the same endpoint we used before, but now we test the specific key provided by the user
BASE_URL = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"

# User provided key (Decoding)
SERVICE_KEY = "UpyO/rN1+4lHyJ6uqJOqWcpMTmnMh3ghQ5qqOHP/MftGPiCa9Y9mI4MQNXN9Jl1eX+sZTBPPtSD//+8a7CtZzg=="

def test_edrug_api():
    print(f"🔬 Testing e-Drug API: {BASE_URL}")
    
    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": "1",
        "numOfRows": "3",
        "type": "json"
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response URL: {response.url}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("\n✅ JSON Parsing Successful:")
                # Print first item to see available fields
                if "body" in data and "items" in data["body"]:
                    first_item = data["body"]["items"][0]
                    print(json.dumps(first_item, indent=2, ensure_ascii=False))
                    
                    # Check for key fields
                    print("\n📋 Checking Key Fields:")
                    fields = ["entpName", "itemName", "efcyQesitm", "useMethodQesitm", "atpnQesitm"]
                    for field in fields:
                        has_field = field in first_item
                        print(f"   - {field}: {'✅ Found' if has_field else '❌ Missing'}")
                else:
                    print(json.dumps(data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print("\n⚠️ Response is not JSON. Raw Text:")
                print(response.text[:500])
        else:
            print(f"\n❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")

if __name__ == "__main__":
    test_edrug_api()
