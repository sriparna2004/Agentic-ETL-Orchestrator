import json
from vertexai.generative_models import GenerativeModel

class SchemaAccuracyAgent:
    def __init__(self, project_id: str):
        self.model = GenerativeModel("gemini-1.5-flash")

    def analyze(self, manifest: dict, schema_metadata: dict) -> dict:
        """
            Compares the manifest (the plan) against the schema_metadata (the reality).
            Detects hallucinations and logical mismatches.
        """

        prompt = f"""
                You are a Senior Data Engineer acting as an Auditor. 
                Your task is to detect if the PLAN (Manifest) relies on tables or columns that 
                do not exist or are logically incorrect based on the REALITY (Metadata).

                MANIFEST (The Plan):
                {json.dumps(manifest, indent=2)}

                REALITY (Actual BigQuery Schema Metadata):
                {json.dumps(schema_metadata, indent=2)}

                CRITICAL TASKS:
                1. Check for hallucinations: Does the manifest call a column that isn't in metadata?
                2. Check for type mismatches: Does the manifest try to aggregate a STRING column numerically?
                3. Logic critique: Does the requested aggregation align with the table grain?

                Return JSON ONLY:
                {{
                    "status": "PASS" | "FAIL",
                    "hallucinations_detected": ["List of missing/wrong columns"],
                    "critique": "A brief, professional Senior DE explanation of the findings.",
                    "retry_needed": true | false
                }}
                """

        response = self.model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        return json.loads(response.text)