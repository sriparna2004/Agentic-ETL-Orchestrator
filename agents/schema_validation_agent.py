from google.cloud import bigquery
import logging

class SchemaValidationAgent:
    def __init__(self,project_id: str):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.logger = logging.getLogger("SchemaValidationAgent")

    def validate(self, source_tables: list, output_table: str) -> dict:

        """
            Validates existence and accessibility of tables using BQ metadata.
            Corresponds to 'Schema & MCP Validation Agent' in mermaid-diagram.jpg.
        """

        results = {"status": "PASS", "errors": [], "table_details": {}}

        # Validate Source Tables

        for table_id in source_tables:
            try:
                table = self.client.get_table(table_id)
                results["table_details"][table_id] = {
                    "exists": True,
                    "num_rows": table.num_rows,
                    "schema_fields": [field.name for field in table.schema]
                }

            except Exception as e:
                results["status"] = "FAIL"
                results["errors"].append(f"Source table {table_id} inaccessible: {str(e)}")

        # Validate Output Table (if it exists)
        try:
            self.client.get_table(output_table)
            results["table_details"][output_table] = {"exists": True}
        except Exception:
            results["table_details"][output_table] = {"exists": False, "note": "Will be created"}

        return results

