import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.rag.vector_store import DrugFoodRAG

def rebuild_index():
    print("🚀 Starting RAG Index Rebuild...")
    try:
        rag = DrugFoodRAG()
        result = rag.build_index(force_rebuild=True)
        print(f"✅ Rebuild Complete: {result}")
        
        # Test search
        print("\n🔎 Testing Semantic Search (Query: '술')")
        results = rag.search("술", n_results=3)
        for r in results:
            print(f"   - {r['metadata']['drug_name']} + {r['metadata']['food_name']} ({r['risk_label']})")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    rebuild_index()
