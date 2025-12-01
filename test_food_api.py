import requests
import json

# Food Nutrition DB API Base URL
# Based on search results: http://openapi.foodsafetykorea.go.kr/api/{key}/{serviceId}/{type}/{start}/{end}
# Service ID for Food Nutrition DB is likely I2790
BASE_URL = "http://openapi.foodsafetykorea.go.kr/api"
SERVICE_ID = "I2790"
TYPE = "json"
START_IDX = "1"
END_IDX = "5"

# User provided key (Decoding)
# Note: FoodSafetyKorea usually uses the key directly in the URL path, not as a query param.
# Let's try the decoding key first.
API_KEY = "UpyO/rN1+4lHyJ6uqJOqWcpMTmnMh3ghQ5qqOHP/MftGPiCa9Y9mI4MQNXN9Jl1eX+sZTBPPtSD//+8a7CtZzg=="

def test_food_api():
    # Construct URL: http://openapi.foodsafetykorea.go.kr/api/keyId/serviceId/dataType/startIdx/endIdx
    # Note: Keys often need to be URL encoded if they contain special chars, but let's try raw first as per some docs.
    # Actually, FoodSafetyKorea keys are usually simple strings, but this looks like a standard public data portal key.
    # If it's a standard portal key, it might use the standard portal endpoint structure instead.
    # Let's try the standard portal structure first since the key format matches.
    
    print("🔬 Testing Food Nutrition API...")
    
    # Attempt 1: Standard Public Data Portal Structure (if applicable)
    # http://apis.data.go.kr/1471000/FoodNtrIrdntDbInfo/getFoodNtrItdntList
    portal_url = "http://apis.data.go.kr/1471000/FoodNtrIrdntDbInfo/getFoodNtrItdntList"
    params = {
        "serviceKey": API_KEY,
        "pageNo": "1",
        "numOfRows": "3",
        "type": "json"
    }
    
    print(f"👉 Attempt 1: Public Data Portal Style ({portal_url})")
    try:
        response = requests.get(portal_url, params=params)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ JSON Parsing Successful:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return
            except:
                print(f"⚠️ Response text: {response.text[:200]}")
        else:
            print(f"❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

    print("\n👉 Attempt 2: FoodSafetyKorea Style (I2790)")
    # If the key is from data.go.kr, it might not work with openapi.foodsafetykorea.go.kr directly 
    # unless they share the backend. But let's try.
    food_safety_url = f"{BASE_URL}/{API_KEY}/{SERVICE_ID}/{TYPE}/{START_IDX}/{END_IDX}"
    try:
        response = requests.get(food_safety_url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print("✅ JSON Parsing Successful:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except:
                print(f"⚠️ Response text: {response.text[:200]}")
        else:
            print(f"❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_food_api()
