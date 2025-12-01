import os
import json
import pandas as pd
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
RAW_DATA_DIR = "data/raw"
OUTPUT_CSV = "data/drug_food_interactions.csv"
KEYWORDS = ["음식", "식사", "술", "알코올", "우유", "자몽", "카페인", "주스", "치즈", "커피"]
MAX_ITEMS_TO_PROCESS = None  # Process all items

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0)

# Prompt Template
PROMPT_TEMPLATE = """
You are a clinical pharmacist. Analyze the following drug information and extract drug-food interactions.
If there is NO specific food interaction mentioned, return "NO_INTERACTION".

Input Data:
Drug Name: {drug_name}
Usage: {usage}
Caution: {caution}
Interaction: {interaction}

Target Output Format (JSON):
{{
    "interactions": [
        {{
            "drug_name": "{drug_name}",
            "drug_ingredient": "Unknown", 
            "drug_category": "Unknown",
            "food_name": "Specific food name (e.g., Milk, Grapefruit, Alcohol)",
            "food_category": "Category (e.g., Dairy, Fruit, Alcohol)",
            "risk_level": "Danger/Warning/Caution",
            "interaction_mechanism": "Brief explanation of mechanism",
            "clinical_effect": "Brief explanation of effect",
            "recommendation": "Actionable advice (e.g., Avoid taking together)",
            "alternative_food": "Suggested alternative or '-'"
        }}
    ]
}}

Rules:
1. Only extract interactions related to FOOD, DRINKS, or ALCOHOL. Ignore drug-drug interactions.
2. Translate all output values to Korean.
3. Risk Level Guide:
   - Danger: Serious adverse effects or complete loss of efficacy (e.g., "Do not take", "Contraindicated").
   - Warning: Potential for significant interaction (e.g., "Avoid", "Consult doctor").
   - Caution: Minor interaction or absorption issues (e.g., "Take with interval").
4. If multiple foods are mentioned, create multiple objects in the "interactions" list.
5. Return ONLY the JSON object.
"""

prompt = PromptTemplate(
    input_variables=["drug_name", "usage", "caution", "interaction"],
    template=PROMPT_TEMPLATE
)

def process_data():
    print("🚀 Starting data processing...")
    
    # 1. Load existing CSV to avoid duplicates
    if os.path.exists(OUTPUT_CSV):
        existing_df = pd.read_csv(OUTPUT_CSV)
        existing_pairs = set(zip(existing_df['drug_name'], existing_df['food_name']))
    else:
        existing_df = pd.DataFrame(columns=[
            "drug_name","drug_ingredient","drug_category","food_name","food_category",
            "risk_level","interaction_mechanism","clinical_effect","recommendation",
            "alternative_food","source"
        ])
        existing_pairs = set()

    # 2. Find relevant items
    relevant_items = []
    files = sorted([f for f in os.listdir(RAW_DATA_DIR) if f.endswith('.json')])
    
    for file in files:
        with open(os.path.join(RAW_DATA_DIR, file), 'r', encoding='utf-8') as f:
            items = json.load(f)
            for item in items:
                # Combine text fields to search for keywords
                full_text = " ".join([
                    str(item.get('efcyQesitm', '')),
                    str(item.get('useMethodQesitm', '')),
                    str(item.get('atpnWarnQesitm', '')),
                    str(item.get('atpnQesitm', '')),
                    str(item.get('intrcQesitm', ''))
                ])
                
                if any(k in full_text for k in KEYWORDS):
                    relevant_items.append(item)

    print(f"🔍 Found {len(relevant_items)} items containing interaction keywords.")
    
    # 3. Process with LLM
    processed_count = 0
    batch_rows = []
    BATCH_SIZE = 10
    
    for item in relevant_items:
        if MAX_ITEMS_TO_PROCESS is not None and processed_count >= MAX_ITEMS_TO_PROCESS:
            print(f"🛑 Reached limit of {MAX_ITEMS_TO_PROCESS} items.")
            break
            
        drug_name = item.get('itemName')
        
        # Check if drug already fully processed (optimization)
        # Note: This is a simple check. Ideally we track processed drugs separately.
        # For now, we rely on duplicate pair checking inside.
        
        # Prepare input
        input_data = {
            "drug_name": drug_name,
            "usage": item.get('useMethodQesitm', 'N/A'),
            "caution": (str(item.get('atpnWarnQesitm', '')) + " " + str(item.get('atpnQesitm', ''))).strip(),
            "interaction": item.get('intrcQesitm', 'N/A')
        }
        
        try:
            print(f"🤖 Processing ({processed_count + 1}/{len(relevant_items)}): {drug_name}...")
            chain = prompt | llm
            response = chain.invoke(input_data)
            content = response.content.replace("```json", "").replace("```", "").strip()
            
            if content == "NO_INTERACTION":
                print("   -> No food interaction found.")
                processed_count += 1
                continue
                
            result = json.loads(content)
            
            for interaction in result.get('interactions', []):
                food_name = interaction.get('food_name')
                
                # Check duplicate
                if (drug_name, food_name) in existing_pairs:
                    print(f"   -> Skipping duplicate: {drug_name} + {food_name}")
                    continue
                
                row = {
                    "drug_name": drug_name,
                    "drug_ingredient": interaction.get('drug_ingredient'),
                    "drug_category": interaction.get('drug_category'),
                    "food_name": food_name,
                    "food_category": interaction.get('food_category'),
                    "risk_level": interaction.get('risk_level').lower(),
                    "interaction_mechanism": interaction.get('interaction_mechanism'),
                    "clinical_effect": interaction.get('clinical_effect'),
                    "recommendation": interaction.get('recommendation'),
                    "alternative_food": interaction.get('alternative_food'),
                    "source": "K-Pharm API (AI Processed)"
                }
                batch_rows.append(row)
                existing_pairs.add((drug_name, food_name)) # Update memory
                print(f"   ✅ Added: {food_name} ({row['risk_level']})")
            
            processed_count += 1
            
            # Incremental Save
            if len(batch_rows) >= BATCH_SIZE:
                new_df = pd.DataFrame(batch_rows)
                if os.path.exists(OUTPUT_CSV):
                    new_df.to_csv(OUTPUT_CSV, mode='a', header=False, index=False, encoding='utf-8-sig')
                else:
                    new_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
                print(f"💾 Saved batch of {len(batch_rows)} interactions.")
                batch_rows = [] # Reset batch
                
            time.sleep(2) # Increased rate limit buffer for Pro model
            
        except Exception as e:
            print(f"❌ Error processing {drug_name}: {e}")
            time.sleep(5)

    # Save remaining
    if batch_rows:
        new_df = pd.DataFrame(batch_rows)
        if os.path.exists(OUTPUT_CSV):
            new_df.to_csv(OUTPUT_CSV, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            new_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
        print(f"💾 Saved final batch of {len(batch_rows)} interactions.")

if __name__ == "__main__":
    process_data()
