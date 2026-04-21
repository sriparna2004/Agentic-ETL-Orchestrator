import os
import yaml
from google.cloud import bigquery
from google.cloud import aiplatform
from google.api_core import exceptions

# --- CONFIGURATION ---
PROJECT_ID = "project-22df5a0a-33c4-4b34-947"
LOCATION = "us-central1"  # Default for Vertex AI
STANDARDS_PATH = "config/standards.yaml"

def check_system():
    print(f"🚀 Initializing Agentic-ETL Readiness Check for project: {PROJECT_ID}\n")
    all_clear = True

    # 1. Verify Local Standards File
    try:
        if not os.path.exists(STANDARDS_PATH):
            raise FileNotFoundError(f"Missing {STANDARDS_PATH}")
        with open(STANDARDS_PATH, 'r') as file:
            config = yaml.safe_load(file)
            print(f"✅ [Standards] Loaded successfully. Version: {config.get('version')}")
    except Exception as e:
        print(f"❌ [Standards] Error: {e}")
        all_clear = False

    # 2. Verify BigQuery Connection
    try:
        bq_client = bigquery.Client(project=PROJECT_ID)
        # Attempt to list datasets to verify connectivity & permissions
        datasets = list(bq_client.list_datasets(max_results=5))
        print(f"✅ [BigQuery] Connected. Found {len(datasets)} datasets.")
    except exceptions.Forbidden as e:
        print(f"❌ [BigQuery] Permission Denied: Ensure you have 'BigQuery Admin' or 'Data Editor' roles.")
        all_clear = False
    except Exception as e:
        print(f"❌ [BigQuery] Error: {e}")
        all_clear = False

    # 3. Verify Vertex AI (Gemini) Connection
    try:
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        # We check if we can initialize; the actual model call happens in the agents
        print(f"✅ [Vertex AI] Initialized in {LOCATION}.")
    except Exception as e:
        print(f"❌ [Vertex AI] Initialization Error: {e}")
        all_clear = False

    # --- FINAL VERDICT ---
    print("\n" + "="*40)
    if all_clear:
        print("🎉 ALL SYSTEMS GO: You are ready to build the Parser Agent!")
    else:
        print("⚠️  SYSTEM CHECK FAILED: Resolve the red marks above before proceeding.")
    print("="*40)

if __name__ == "__main__":
    check_system()
