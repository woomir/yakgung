import json
import glob
import pandas as pd
import os

RAW_DATA_DIR = "data/raw"
OUTPUT_CSV = "data/drugs.csv"

def process_drug_overview():
    print("🚀 Starting Drug Overview Processing...")
    
    json_files = glob.glob(os.path.join(RAW_DATA_DIR, "drugs_page_*.json"))
    print(f"📂 Found {len(json_files)} raw data files.")
    
    all_drugs = []
    
    for file_path in sorted(json_files):
        with open(file_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
            
        for item in items:
            # Extract key fields
            drug_info = {
                "drug_name": item.get("itemName"),
                "manufacturer": item.get("entpName"),
                "efficacy": item.get("efcyQesitm"),
                "usage": item.get("useMethodQesitm"),
                "precautions": item.get("atpnQesitm"),
                "warnings": item.get("atpnWarnQesitm"),
                "interactions": item.get("intrcQesitm"),
                "side_effects": item.get("seQesitm"),
                "storage": item.get("depositMethodQesitm"),
                "image_url": item.get("itemImage"),
                "update_date": item.get("updateDe")
            }
            all_drugs.append(drug_info)
            
    # Convert to DataFrame
    df = pd.DataFrame(all_drugs)
    
    # Remove duplicates
    initial_count = len(df)
    df.drop_duplicates(subset=["drug_name"], inplace=True)
    final_count = len(df)
    
    print(f"📊 Processed {initial_count} items. Unique drugs: {final_count}")
    
    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"✅ Saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    process_drug_overview()
