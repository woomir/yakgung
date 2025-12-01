import requests
import json
import urllib.parse
import time

# API Endpoint and Keys
URL = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
# Encoded Key from user
SERVICE_KEY_ENCODED = "UpyO%2FrN1%2B4lHyJ6uqJOqWcpMTmnMh3ghQ5qqOHP%2FMftGPiCa9Y9mI4MQNXN9Jl1eX%2BsZTBPPtSD%2F%2F%2B8a7CtZzg%3D%3D"

def search_interactions():
    print(f"Searching API for interaction keywords...")
    
    # Keywords to look for in the response
    keywords = ["자몽", "우유", "술", "알코올", "커피", "카페인", "음식", "식사"]
    
    # Fetch a batch of drugs (e.g., 20 items)
    query_params = [
        f"serviceKey={SERVICE_KEY_ENCODED}",
        "pageNo=1",
        "numOfRows=20",
        "type=json"
    ]
    full_url = f"{URL}?{'&'.join(query_params)}"
    
    try:
        response = requests.get(full_url)
        if response.status_code == 200:
            data = response.json()
            items = data.get('body', {}).get('items', [])
            
            found_count = 0
            for item in items:
                # Fields to check
                fields_to_check = [
                    item.get('efcyQesitm'), # 효능
                    item.get('useMethodQesitm'), # 용법
                    item.get('atpnWarnQesitm'), # 경고
                    item.get('atpnQesitm'), # 주의사항
                    item.get('intrcQesitm'), # 상호작용
                    item.get('depositMethodQesitm') # 보관법
                ]
                
                full_text = " ".join([str(f) for f in fields_to_check if f])
                
                matched_keywords = [k for k in keywords if k in full_text]
                
                if matched_keywords:
                    found_count += 1
                    print(f"\n💊 [{item.get('itemName')}]")
                    print(f"   Keywords found: {', '.join(matched_keywords)}")
                    # Print relevant snippets (simplified)
                    if item.get('intrcQesitm'):
                         print(f"   🔗 Interaction Field: {item.get('intrcQesitm')[:100]}...")
                    if item.get('atpnQesitm'):
                         # Find sentence with keyword
                         for k in matched_keywords:
                             if k in str(item.get('atpnQesitm')):
                                 start = str(item.get('atpnQesitm')).find(k)
                                 snippet = str(item.get('atpnQesitm'))[max(0, start-20):min(len(str(item.get('atpnQesitm'))), start+50)]
                                 print(f"   ⚠️ Caution Snippet ({k}): ...{snippet}...")

            print(f"\nFound {found_count} drugs with interaction keywords out of {len(items)} items checked.")
            
        else:
            print("Error: API request failed")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    search_interactions()
