import requests
import json
import os
import time
from datetime import datetime

# API Configuration
URL = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
SERVICE_KEY_ENCODED = "UpyO%2FrN1%2B4lHyJ6uqJOqWcpMTmnMh3ghQ5qqOHP%2FMftGPiCa9Y9mI4MQNXN9Jl1eX%2BsZTBPPtSD%2F%2F%2B8a7CtZzg%3D%3D"
OUTPUT_DIR = "data/raw"

def fetch_drug_data():
    print(f"🚀 Starting data collection at {datetime.now()}")
    
    page_no = 1
    num_of_rows = 100 # Fetch 100 items per page
    total_count = 0
    collected_count = 0
    
    while True:
        print(f"📄 Fetching page {page_no}...")
        
        query_params = [
            f"serviceKey={SERVICE_KEY_ENCODED}",
            f"pageNo={page_no}",
            f"numOfRows={num_of_rows}",
            "type=json"
        ]
        full_url = f"{URL}?{'&'.join(query_params)}"
        
        try:
            response = requests.get(full_url, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Error: Status code {response.status_code}")
                break
                
            data = response.json()
            body = data.get('body', {})
            items = body.get('items', [])
            
            if not items:
                print("⚠️ No more items found.")
                break
                
            if page_no == 1:
                total_count = body.get('totalCount', 0)
                print(f"📊 Total items available: {total_count}")
            
            # Save this batch
            filename = os.path.join(OUTPUT_DIR, f"drugs_page_{page_no}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
                
            collected_count += len(items)
            print(f"✅ Saved {len(items)} items to {filename} (Total: {collected_count}/{total_count})")
            
            if collected_count >= total_count:
                print("🎉 All items collected!")
                break
                
            page_no += 1
            time.sleep(0.5) # Be polite to the API
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            break

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    fetch_drug_data()
