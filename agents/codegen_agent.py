import json
from vertexai.generative_models import GenerativeModel


class CodeGenAgent:
    def __init__(self, project_id: str):
        # Using Gemini 1.5 Flash for rapid, accurate code generation
        self.model = GenerativeModel("gemini-1.5-flash")

    def generate_sql(self, manifest: dict, schema_metadata: dict, execution_plan: dict) -> dict:
        """
        Consumes the validated schema and architectural plan to produce optimized SQL.
        Corresponds to the 'CodeGen Agent' block in your architecture diagram.
        """

        prompt = f"""
        You are an Expert Staff Data Engineer specializing in Google Cloud BigQuery.
        Your job is to generate flawless, production-ready BigQuery Standard SQL based on an explicit Execution Plan and Schema Metadata.

        INPUT REQUIREMENTS:
        {json.dumps(manifest, indent=2)}

        VERIFIED SCHEMA METADATA:
        {json.dumps(schema_metadata, indent=2)}

        DETERMINISTIC EXECUTION PLAN:
        {json.dumps(execution_plan, indent=2)}

        CRITICAL SQL GENERATION RULES:
        1. Use Standard SQL syntax exclusively (all keywords like SELECT, FROM, WHERE, GROUP BY must be UPPERCASE).
        2. Break the logic down using clear, descriptive Common Table Expressions (CTEs) rather than deeply nested subqueries.
        3. If handling arrays/records (e.g., `event_params` or repeated fields), use explicit CROSS JOIN UNNEST syntax rather than comma joins.
        4. Apply the exact output target requested: {manifest.get('output_table')}.
        5. Respect any optimization tips from the execution plan (e.g., partitioning, clustering, or filtering by date ranges).
        6. Return ONLY the raw SQL string inside the JSON structure. Do not wrap the SQL string itself in markdown code blocks inside the JSON.

        Return a JSON object matching this contract exactly:
        {{
            "agent_name": "codegen_agent",
            "generated_sql": "SELECT ... FROM ...",
            "target_table": "string",
            "compilation_notes": "Brief notes on optimization or unnesting patterns used."
        }}
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1  # Low temperature for highly deterministic code generation
                }
            )

            return json.loads(response.text)

        except Exception as e:
            return {
                "agent_name": "codegen_agent",
                "generated_sql": "",
                "target_table": manifest.get("output_table", "UNKNOWN"),
                "compilation_notes": f"Generation failed via system exception: {str(e)}"
            }


# --- Independent Unit Test Line ---
if __name__ == "__main__":
    codegen = CodeGenAgent(project_id="project-22df5a0a-33c4-4b34-947")

    # Mock states representing the outputs from our previous agents
    mock_manifest = {
        "request_name": "US-06 Daily Active Users",
        "output_table": "cx_reporting.daily_unique_users",
        "refresh_frequency": "daily"
    }

    mock_schema = {
        "cx_raw.ga4_raw_table": {
            "exists": True,
            "schema_fields": ["user_pseudo_id", "event_date", "event_name", "event_params"]
        }
    }

    mock_plan = {
        "execution_steps": [
            "1. Filter events where event_name = 'session_start'",
            "2. Group by event_date to count DISTINCT user_pseudo_id",
            "3. Materialize results into target reporting table"
        ],
        "sql_strategy": "CREATE OR REPLACE TABLE cx_reporting.daily_unique_users AS",
        "cost_analysis": {
            "risk_level": "LOW",
            "optimization_tip": "Filter by event_date scan boundaries if partition exists."
        }
    }

    print("🛠️ Testing CodeGen Agent Isolation...")
    result = codegen.generate_sql(mock_manifest, mock_schema, mock_plan)
    print(json.dumps(result, indent=2))