from google.cloud import bigquery
import json
import logging


class SqlValidationAgent:
    def __init__(self, project_id: str):
        # We use the native bigquery Client to communicate directly with GCP
        self.client = bigquery.Client(project=project_id)
        self.logger = logging.getLogger("SqlValidationAgent")

    def validate_query(self, generated_sql: str, byte_limit_gb: float = 10.0) -> dict:
        """
        Executes a zero-cost BigQuery Dry Run to validate syntax and calculate exact cost.
        Corresponds to 'Eval Gate: SQL Validation / Dry Run' in the architecture.
        """
        # Configure the job to be a dry run only
        job_config = bigquery.QueryJobConfig()
        job_config.dry_run = True
        job_config.use_query_cache = False

        try:
            # Trigger the dry run
            query_job = self.client.query(generated_sql, job_config=job_config)

            # If it compiles, extract the exact data volume metrics
            total_bytes = query_job.total_bytes_processed
            total_gb = total_bytes / (1024 ** 3)

            # FinOps Rule: Check if it exceeds our hard organizational boundary
            if total_gb > byte_limit_gb:
                return {
                    "status": "FAIL",
                    "reason": "FINOPS_LIMIT_EXCEEDED",
                    "message": f"Query is syntactically valid but would scan {total_gb:.4f} GB, exceeding the limit of {byte_limit_gb} GB.",
                    "bytes_processed": total_bytes,
                    "gb_processed": total_gb
                }

            return {
                "status": "PASS",
                "reason": "VALIDATION_SUCCESS",
                "message": f"SQL syntax and schema binding verified successfully. Estimated scan: {total_gb:.4f} GB.",
                "bytes_processed": total_bytes,
                "gb_processed": total_gb
            }

        except Exception as e:
            # Capture the exact compilation error from BigQuery backend
            return {
                "status": "FAIL",
                "reason": "COMPILATION_ERROR",
                "message": str(e),
                "bytes_processed": 0,
                "gb_processed": 0.0
            }


# --- Isolated Module Testing Suite ---
if __name__ == "__main__":
    PROJECT_ID = "project-22df5a0a-33c4-4b34-947"
    validator = SqlValidationAgent(PROJECT_ID)

    # Test Case 1: Bad Syntax (Missing FROM clause)
    bad_sql = "SELECT user_pseudo_id, event_date WHERE event_name = 'session_start'"
    print("🛠️ Testing Validation Agent with broken SQL...")
    result = validator.validate_query(bad_sql)
    print(json.dumps(result, indent=2))