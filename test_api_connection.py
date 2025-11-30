import requests
import json
import urllib.parse

# API Endpoint and Keys
URL = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
# Encoded Key from user
SERVICE_KEY_ENCODED = "UpyO%2FrN1%2B4lHyJ6uqJOqWcpMTmnMh3ghQ5qqOHP%2FMftGPiCa9Y9mI4MQNXN9Jl1eX%2BsZTBPPtSD%2F%2F%2B8a7CtZzg%3D%3D"

def test_api():
    print(f"Testing API: {URL}")
    
    # Construct URL manually to ensure key is not double-encoded
    query_params = [
        f"serviceKey={SERVICE_KEY_ENCODED}",
        "pageNo=1",
        "numOfRows=3",
        "type=json"
    ]
    full_url = f"{URL}?{'&'.join(query_params)}"
    
    try:
        print(f"Requesting: {full_url}")
        response = requests.get(full_url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response URL: {response.url}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("\n✅ JSON Parsing Successful:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Check result code
                header = data.get('header', {})
                body = data.get('body', {})
                
                if header.get('resultCode') == '00':
                    print("\n🎉 API Call Successful!")
                    print(f"Total Count: {body.get('totalCount')}")
                    items = body.get('items')
                    if items:
                        print(f"First Item: {items[0].get('itemName')}")
                else:
                    print(f"\n⚠️ API Error: {header.get('resultMsg')} (Code: {header.get('resultCode')})")
                    
            except json.JSONDecodeError:
                print("\n⚠️ Response is not JSON. It might be XML or Error HTML.")
                print("Raw Response:")
                print(response.text[:500]) # Print first 500 chars
        else:
            print("\n❌ HTTP Error")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Exception occurred: {str(e)}")

if __name__ == "__main__":
    test_api()
