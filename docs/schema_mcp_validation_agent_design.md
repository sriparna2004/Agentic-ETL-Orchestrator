# Schema & MCP Validation Agent Design (Stage 2)

## Objective
Define the **Schema & MCP Validation Agent** and its **Eval Gate** so that only schema-grounded requests proceed, while failures are retried with targeted corrections.

## Placement in Flow
1. Intake submission
2. Intake Eval Agent -> PASS
3. Central Orchestrator routes to **Schema & MCP Validation Agent**
4. Schema Eval Gate returns `PASS` / `RETRY` / `ESCALATE_HUMAN`
5. If PASS -> return control to Central Orchestrator for next stage
6. If RETRY -> rerun Schema & MCP Validation Agent with critique context

## Agent Responsibilities
1. Resolve source tables from request payload.
2. Verify source objects exist in BigQuery.
3. Validate requested fields/dimensions/measures against actual schema.
4. Confirm nested GA4 fields (`event_params`, `user_properties`) are accessed correctly.
5. Detect hallucinated fields/tables and invalid references.
6. Emit normalized schema map for downstream Planner Agent.

## Inputs
```json
{
  "run_id": "orch_2026_05_04_0001",
  "request": {
    "request_name": "US-07 Average Engagement per Page",
    "source_tables": ["analytics_123456.events_*"],
    "description": "..."
  },
  "expected_outputs": {
    "output_table": "cx_reporting.page_engagement_stats"
  },
  "context": {
    "timezone": "America/New_York",
    "refresh_frequency": "daily"
  },
  "retry_context": {
    "attempt": 0,
    "last_warnings": []
  }
}
```

## MCP and BigQuery Validation Steps
1. **Dataset and table pattern check**
   - Validate `events_*` pattern and dataset accessibility.
2. **Physical schema retrieval**
   - Pull table metadata through MCP-backed catalog connector.
3. **Field resolution**
   - Map requested business terms to physical columns.
4. **Nested field validation**
   - Verify keys used for `event_params` extraction are present/expected.
5. **Query dry-run safety check**
   - Generate minimal dry-run SQL to ensure references compile.
6. **Schema contract output**
   - Produce canonical schema JSON for planner/codegen.

## Blocking Rules (Hard Fail)
1. Source dataset/table inaccessible.
2. No valid source table resolved.
3. Referenced mandatory field not found after mapping attempts.
4. Request depends on unsupported/unsafe pattern.

## Retryable Rules (Soft Fail)
1. Ambiguous business term can map to multiple fields.
2. Missing `event_params` key may be clarified by user/request context.
3. Non-blocking warning from dry-run that can be corrected by planner prompt.

## Eval Gate for Schema Stage
### Dimension Scores (0.0 to 1.0)
1. **Source Resolution Score**
2. **Field Match Score**
3. **Nested Parameter Confidence Score**
4. **Dry-Run Validity Score**
5. **Schema Contract Completeness Score**

### Pass Criteria
- overall score `>= 0.90`
- no hard errors
- dry-run validity score `= 1.0`
- source resolution score `= 1.0`

### Retry Criteria
- hard errors absent, but any pass criterion not met.
- targeted fixes can be generated automatically.

### Escalation Criteria
- hard errors present, or
- retry attempts exceed `max_retry_per_stage` from orchestrator policy.

## Eval Output Contract
```json
{
  "agent_name": "schema_mcp_validation_agent",
  "status": "PASS",
  "overall_score": 0.94,
  "dimension_scores": {
    "source_resolution": 1.0,
    "field_match": 0.91,
    "nested_param_confidence": 0.90,
    "dry_run_validity": 1.0,
    "schema_contract_completeness": 0.92
  },
  "hard_errors": [],
  "warnings": [],
  "next_action": "continue",
  "schema_contract": {
    "resolved_tables": ["analytics_123456.events_20260503"],
    "required_fields": ["event_name", "event_timestamp", "user_pseudo_id"],
    "nested_keys": ["page_location", "engagement_time_msec"]
  },
  "artifacts": {
    "metadata_snapshot_uri": "gs://.../schema_snapshot.json",
    "dry_run_job_url": "https://console.cloud.google.com/bigquery?..."
  },
  "retryable": true,
  "retry_count": 0,
  "timestamp_utc": "2026-05-04T00:00:00Z"
}
```

## Orchestrator Interaction
- **On PASS**: Orchestrator records eval + artifacts and routes to Planner Agent.
- **On RETRY**: Orchestrator sends critique context back to Schema/MCP Validation Agent.
- **On ESCALATE_HUMAN**: Orchestrator sets Jira to `Blocked` and stops execution.

## Retry Prompt Examples
- "Confirm whether `engagement_time_msec` should be sourced from `event_params` int_value."
- "Clarify if output requires event-level or session-level grain."
- "Provide exact dataset/project for `events_*` source."

## Jira Update Payload (Schema Stage)
For every schema stage completion event:
- Stage: `schema_mcp_validation`
- Status: PASS/RETRY/ESCALATE_HUMAN
- Overall score
- Hard errors/warnings
- Links: dry-run job, schema snapshot
- Next action

## Next Implementation Step
Implement this agent with:
1. MCP-backed metadata client abstraction
2. BigQuery dry-run helper
3. schema-contract serializer
4. eval scorer returning the standardized contract above
