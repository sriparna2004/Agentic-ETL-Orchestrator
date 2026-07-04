import json
import re
from datetime import datetime
from typing import Dict, Any, List
import yaml
from vertexai.generative_models import GenerativeModel
import vertexai


class IntakeEvalAgent:
    def __init__(self, project_id: str, location: str = "us-central1", prompts_dir: str = "prompts",prompt_version: str = "1.0"):

        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-1.5-flash")
        self.project_id = project_id
        self.prompt_loader  = PromptLoader(prompts_dir)
        self.prompt_version = prompt_version

        # Thresholds from your design doc
        self.thresholds = {
            "completeness": 0.95,
            "clarity": 0.80,
            "schema_readiness": 0.85,
            "scheduling_validity": 0.95,
            "governance": 0.90,
            "overall_min": 0.88
        }


    def _run_hard_validation(self, payload: Dict[str, Any]) -> List[str]:
            """Deterministic checks based on Design Doc section 'Hard Validation Rules'"""
            errors: List[str] = []

            # 1. Required Fields
            if not payload.get("request_name"): errors.append("request_name required.")
            if not payload.get("description"): errors.append("description required.")
            if not payload.get("source_tables"): errors.append("At least one source_table required.")

            # 2. Schedule Format (HH:MM)
            time_val = payload.get("scheduled_time")
            if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", str(time_val)):
                errors.append("schedule_time must match HH:MM 24-hour format.")

            #3. Refresh Frequency

            valid_freqs = ["hourly", "daily", "weekly", "monthly"]
            if payload.get("refresh_frequency") not in valid_freqs:
                errors.append(f"refresh_frequency must be one of: {', '.join(valid_freqs)}.")

            # 4. DQ Threshold

            dq = payload.get("dq_null_threshold_pct")
            if not (isinstance(dq, (int, float)) and 0 <= dq <= 100):
                errors.append("dq_null_threshold_pct must be between 0 and 100.")

            return errors

    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
            # 1. Start with Hard Validation
            hard_errors = self._run_hard_validation(payload)

            # 2. LLM Scoring for Subjective Dimensions (Clarity, Schema-Readiness)
            prompt = f"""
                    Evaluate this ETL request based on the following dimensions (Score 0.0 to 1.0):
                    - completeness: Are all metadata fields present?
                    - clarity: Does the description define metric intent and grain?
                    - schema_readiness: Do table names follow GA4/BigQuery naming conventions?
                    - scheduling_validity: Is the timezone and frequency logically sound?
                    - governance: Is the Jira ID present and valid?

                    PAYLOAD:
                    {json.dumps(payload, indent=2)}

                    Return a JSON object matching the Eval Output Contract. 
                    Include a 'warnings' list for scores below 0.9.
                    """
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            eval_output = json.loads(response.text)

            # 3. Decision Logic (PASS, RETRY, ESCALATE)
            # Inject hard errors if found
            eval_output["hard_errors"] = hard_errors

            # Final Decision Policy Implementation
            scores = eval_output["dimension_scores"]
            meets_minimums = all(scores[dim] >= self.thresholds[dim] for dim in self.thresholds if dim != "overall_min")

            if hard_errors:
                eval_output["status"] = "RETRY" if eval_output.get("retryable", True) else "ESCALATE_HUMAN"
                eval_output["next_action"] = "fix_hard_errors"
            elif eval_output["overall_score"] >= self.thresholds["overall_min"] and meets_minimums:
                eval_output["status"] = "PASS"
                eval_output["next_action"] = "continue"
            else:
                eval_output["status"] = "RETRY"
                eval_output["next_action"] = "request_clarification"

            eval_output["timestamp_utc"] = datetime.utcnow().isoformat() + "Z"
            return eval_output



