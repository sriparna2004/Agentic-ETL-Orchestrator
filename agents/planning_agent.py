import json
from vertexai.generative_models import GenerativeModel

class PlanningAgent:
    def __init__(self, project_id: str):
        self.model = GenerativeModel("gemini-1.5-flash")

    def create_plan(self, manifest: dict, schema_metadata: dict) -> dict:
        """
            Translates verified requirements into an execution plan (DAG).
            Corresponds to 'Planning Agent' in mermaid-diagram.jpg.
         """

        prompt = f"""
                You are a Senior Data Architect. Create an execution plan for an ETL job.

                INPUT REQUIREMENTS:
                {json.dumps(manifest, indent=2)}

                VERIFIED SCHEMA:
                {json.dumps(schema_metadata, indent=2)}

                TASKS:
                1. Define the SQL steps (e.g., Unnesting, Filtering, Grouping).
                2. Define the execution order (The DAG).
                3. Identify any necessary intermediate tables (staging).
                4. COST ESTIMATION:
                - Analyze the 'num_rows' from schema_metadata.
                - Estimate the cost impact of the requested aggregation on this volume.
                - Return a 'risk_level' (LOW/MEDIUM/HIGH).
                - If HIGH, provide a specific optimization tip (e.g., 'Use a partition filter on event_date').
        
                Return JSON ONLY:
                {{
                     "execution_steps": ["step 1", "step 2", "step 3"],
                     "dependencies": ["source_table_name"],
                     "agg_logic": "description of how to aggregate",
                     "sql_strategy": "e.g., CREATE OR REPLACE TABLE...",
                     "cost_analysis": {{
                         "risk_level": "LOW",
                         "estimated_data_processed_gb": 0.5,
                         "optimization_tip": "string or null"
                    }}
                }}

                """

        response = self.model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        return json.loads(response.text)