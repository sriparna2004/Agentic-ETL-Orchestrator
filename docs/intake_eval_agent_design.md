# Intake Eval Agent Design (Stage 1)

## Objective
Define the **Eval Agent** for the Intake stage so every submitted request is quality-checked before passing to the orchestrator's next stage.

## Scope in Current Architecture
- Stage: **Intake & Analysis**
- Position: Runs immediately after intake form submission parsing.
- Decision: `PASS`, `RETRY`, or `ESCALATE_HUMAN`

## Inputs
The Intake Eval Agent receives a normalized payload from the intake UI/backend parser.

```json
{
  "request_name": "US-06 Daily Active Users",
  "jira_ticket": "CX-142",
  "description": "...",
  "source_tables": ["analytics_123456.events_*"] ,
  "output_table": "cx_reporting.daily_unique_users",
  "schedule_time": "07:00",
  "refresh_frequency": "daily",
  "timezone": "America/New_York",
  "dq_null_threshold_pct": 10
}
```

## Eval Dimensions and Scoring
Each dimension is scored from `0.0` to `1.0`.

1. **Completeness Score**
   - Required fields present and non-empty.
   - Expected minimum: `>= 0.95`

2. **Clarity Score**
   - Description includes metric intent, grain, and grouping/filter hints.
   - Expected minimum: `>= 0.80`

3. **Schema-Readiness Score**
   - Source table patterns look valid for GA4 BigQuery ingestion conventions.
   - Output table naming is compliant.
   - Expected minimum: `>= 0.85`

4. **Scheduling Validity Score**
   - Time format valid.
   - Refresh frequency is supported.
   - Timezone is recognized.
   - Expected minimum: `>= 0.95`

5. **Governance Score**
   - Jira ID format valid if supplied.
   - DQ threshold within accepted bounds.
   - Expected minimum: `>= 0.90`

## Decision Policy
- **PASS** when:
  - no hard errors, and
  - weighted score `>= 0.88`, and
  - all mandatory dimension minimums are met.
- **RETRY** when:
  - soft validation issues exist (missing details/ambiguous phrasing), and
  - automated clarification prompt can fix them.
- **ESCALATE_HUMAN** when:
  - repeated retries exceed max attempts, or
  - malformed/unsafe payload cannot be auto-corrected.

## Hard Validation Rules (Blocking)
1. `request_name` required.
2. `description` required.
3. At least one `source_table` required.
4. `schedule_time` must match `HH:MM` 24-hour format.
5. `refresh_frequency` must be one of: `hourly`, `daily`, `weekly`, `monthly`.
6. `timezone` required (default `America/New_York`).
7. `dq_null_threshold_pct` must be between `0` and `100`.

## Eval Output Contract
```json
{
  "agent_name": "intake_eval_agent",
  "status": "PASS",
  "overall_score": 0.93,
  "dimension_scores": {
    "completeness": 1.0,
    "clarity": 0.89,
    "schema_readiness": 0.92,
    "scheduling_validity": 1.0,
    "governance": 0.90
  },
  "hard_errors": [],
  "warnings": [
    "Description could be more explicit about aggregation grain."
  ],
  "next_action": "continue",
  "retryable": true,
  "retry_count": 0,
  "timestamp_utc": "2026-04-30T00:00:00Z"
}
```

## Clarification Prompt Template (for RETRY)
When status is `RETRY`, return actionable prompts:
- "Please specify aggregation grain (daily/hourly)."
- "Please confirm expected grouping dimensions."
- "Please provide output table if this is a persisted report."

## Orchestrator Handoff
If `PASS`, orchestrator routes to:
1. Schema/MCP Validation Agent
2. Planner Agent

If `RETRY`, orchestrator routes back to Intake with generated clarification prompts.

If `ESCALATE_HUMAN`, orchestrator updates Jira ticket status to `Blocked` with reasons.

## Jira Update Hooks
At the end of Intake Eval:
- Comment includes:
  - Eval status
  - Overall score
  - Top warnings/errors
  - Next action
- Suggested status mapping:
  - `PASS` -> keep `In Progress`
  - `RETRY` -> keep `In Progress` + clarification required
  - `ESCALATE_HUMAN` -> `Blocked`
