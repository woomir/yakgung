import pandas as pd
import os

CSV_FILE = "data/drug_food_interactions.csv"

def verify_data():
    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: {CSV_FILE} not found.")
        return

    df = pd.read_csv(CSV_FILE)
    print(f"📊 Total interactions: {len(df)}")
    
    # Check for new entries (source = "K-Pharm API (AI Processed)")
    new_entries = df[df['source'] == "K-Pharm API (AI Processed)"]
    print(f"✨ New AI-processed entries: {len(new_entries)}")
    
    if not new_entries.empty:
        print("\n🔍 Sample new entries:")
        print(new_entries[['drug_name', 'food_name', 'risk_level']].head(10).to_string(index=False))
        
        # Check for specific keywords
        keywords = ["자몽", "우유", "술", "알코올"]
        print("\n📈 Keyword stats in new data:")
        for k in keywords:
            count = new_entries['food_name'].str.contains(k, na=False).sum()
            print(f"   - {k}: {count}")
    else:
        print("⚠️ No new entries found yet.")

if __name__ == "__main__":
    verify_data()
