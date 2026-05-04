# Planning Agent Design with Eval Gate and Critique Loop (Stage 3)

## Objective
Define the **Planning Agent**, its **Eval Gate**, and a bounded **Critique Loop** so validated requirements are converted into executable ETL plans with strong logical correctness before code generation.

## Placement in Orchestration Flow
1. Intake Eval -> PASS
2. Schema & MCP Validation -> PASS
3. Central Orchestrator routes to **Planning Agent**
4. Planning Eval Gate returns `PASS` / `RETRY` / `ESCALATE_HUMAN`
5. If PASS -> return control to Central Orchestrator and proceed to Code Generation stage
6. If RETRY -> run Critique Loop and re-plan

## Planning Agent Responsibilities
1. Convert business request + schema contract into a staged ETL execution plan.
2. Define transformation steps, dependencies, and expected output grain.
3. Specify metric logic and grouping/filter rules explicitly.
4. Produce a plan contract that downstream code generation can execute deterministically.
5. Estimate risk areas (join blowups, double-count risk, partition misuse).

## Inputs
```json
{
  "run_id": "orch_2026_05_04_0002",
  "request": {
    "request_name": "US-08 Regional Traffic Spikes (Hourly)",
    "description": "..."
  },
  "schema_eval_output": {
    "status": "PASS",
    "schema_contract": {
      "resolved_tables": ["analytics_123456.events_20260503"],
      "required_fields": ["event_timestamp", "geo.city", "geo.region"],
      "nested_keys": []
    }
  },
  "constraints": {
    "timezone": "America/New_York",
    "write_mode": "MERGE",
    "dq_null_threshold_pct": 10,
    "refresh_frequency": "daily"
  },
  "retry_context": {
    "attempt": 0,
    "prior_critique": []
  }
}
```

## Planning Output Contract
```json
{
  "plan_id": "plan_2026_05_04_01",
  "target_table": "cx_reporting.hourly_regional_traffic",
  "grain": ["hour_bucket", "geo.region", "geo.city"],
  "steps": [
    {
      "id": "extract_base",
      "type": "extract",
      "description": "Read GA4 events_* with partition pruning"
    },
    {
      "id": "transform_time",
      "type": "transform",
      "description": "Convert event_timestamp to America/New_York and truncate to hour"
    },
    {
      "id": "aggregate",
      "type": "aggregate",
      "description": "COUNT(*) grouped by hour_bucket, region, city"
    },
    {
      "id": "publish",
      "type": "load",
      "description": "MERGE into target table"
    }
  ],
  "checks": {
    "grain_uniqueness": true,
    "partition_filter_required": true,
    "dq_null_threshold_pct": 10
  },
  "assumptions": [
    "Null region/city mapped to UNKNOWN",
    "Timezone handled in local US Eastern context"
  ]
}
```

## Eval Gate for Planning Stage
### Dimension Scores (0.0 to 1.0)
1. **Plan Completeness Score**
   - Steps, dependencies, output contract all present.
2. **Logical Correctness Score**
   - Metric definitions and transformations align with request.
3. **Schema Alignment Score**
   - All fields referenced exist in schema contract.
4. **Execution Feasibility Score**
   - Plan can be translated to SQL/PySpark without ambiguity.
5. **Risk Control Score**
   - Anti-pattern and data-quality safeguards explicitly addressed.

### Pass Criteria
- overall score `>= 0.90`
- no hard errors
- schema alignment score `= 1.0`
- execution feasibility score `>= 0.90`

### Retry Criteria
- no hard errors, but one or more criteria below threshold.
- critique loop identifies actionable fixes.

### Escalation Criteria
- hard errors remain after critique retries, or
- retry limit exceeded as per orchestrator policy.

## Hard Error Conditions
1. Plan references fields absent from schema contract.
2. Metric or grain definition conflicts with request intent.
3. Plan omits mandatory publish/load strategy.
4. Plan has unresolved dependency cycle.

## Critique Loop Design (Senior DE Reviewer)
### Purpose
Run a structured review after Planning Agent draft output and before final acceptance.

### Critique Checks
1. **Metric Integrity**: detect double counting or invalid denominator logic.
2. **Grain Integrity**: ensure grouping matches target grain.
3. **Join Safety**: prevent fanout and unintended cartesian effects.
4. **Partition Strategy**: enforce partition-aware source filtering.
5. **Timezone Consistency**: verify local-time aggregation logic.
6. **DQ Coverage**: check null-threshold and sanity checks included.

### Critique Outcomes
- `APPROVE`: no material issues.
- `REVISE`: issues found with fix instructions; return to Planning Agent.
- `BLOCK`: critical logic conflict; escalate if unresolved.

### Retry Boundaries
- default max critique retries: `2`
- if final retry still below thresholds -> `ESCALATE_HUMAN`

## Eval Output Contract
```json
{
  "agent_name": "planning_agent",
  "status": "RETRY",
  "overall_score": 0.86,
  "dimension_scores": {
    "plan_completeness": 0.92,
    "logical_correctness": 0.78,
    "schema_alignment": 1.0,
    "execution_feasibility": 0.88,
    "risk_control": 0.80
  },
  "hard_errors": [],
  "warnings": [
    "Potential double counting in conversion aggregation.",
    "Missing explicit partition filter step."
  ],
  "critique_result": "REVISE",
  "critique_feedback": [
    "Add partition predicate using _TABLE_SUFFIX window.",
    "Clarify distinctness key for conversion metric."
  ],
  "next_action": "retry",
  "retryable": true,
  "retry_count": 1,
  "timestamp_utc": "2026-05-04T00:00:00Z"
}
```

## Orchestrator Interaction
- **PASS**: persist plan + eval; route to Code Generation Agent.
- **RETRY**: pass critique feedback into next planning attempt.
- **ESCALATE_HUMAN**: mark run blocked; update Jira with critique summary.

## Jira Update Payload (Planning Stage)
For each planning attempt:
- Stage: `planning`
- Eval status and score
- Critique outcome (`APPROVE`/`REVISE`/`BLOCK`)
- Key warnings/errors
- Link to plan artifact
- Next action

## Next Implementation Step
Implement planning stage with:
1. Prompt template using request + schema contract + global constraints
2. Plan validator (JSON schema + rule checks)
3. Critique module (Senior DE rule engine / LLM reviewer)
4. Eval scorer and retry-controller hooks for central orchestrator
