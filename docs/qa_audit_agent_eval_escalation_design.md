# QA & Audit Agent Design with Eval Gate and Auto Human Escalation (Stage 5)

## Objective
Define the **QA & Audit Agent** and its **Eval Gate** so generated pipelines are validated for correctness, data quality, and audit readiness before deployment, with automatic escalation to human reviewers on failure.

## Placement in Flow
1. Intake Eval -> PASS
2. Schema & MCP Validation -> PASS
3. Planning + Critique -> PASS
4. PySpark Coding + Refactor -> PASS
5. Central Orchestrator routes to **QA & Audit Agent**
6. QA Eval Gate returns `PASS` or `ESCALATE_HUMAN`
7. If PASS -> return to Central Orchestrator and proceed to Deployment
8. If fail -> auto escalate to human (no retry loop for this stage)

## QA & Audit Agent Responsibilities
1. Execute unit and integration checks for generated transformations.
2. Validate metric logic against planning contract expectations.
3. Run data quality checks (null rates, uniqueness, row-volume sanity).
4. Verify schema compatibility of output table contract.
5. Generate audit artifact bundle for traceability.

## Inputs
```json
{
  "run_id": "orch_2026_05_04_0004",
  "request": {
    "request_name": "US-06 Daily Active Users"
  },
  "planning_output": {
    "target_table": "cx_reporting.daily_unique_users",
    "grain": ["event_date", "device_category"],
    "checks": {
      "dq_null_threshold_pct": 10
    }
  },
  "codegen_output": {
    "artifact_uri": "gs://.../code_bundle.zip",
    "entrypoint": "jobs/us06/main.py"
  },
  "runtime_context": {
    "timezone": "America/New_York",
    "refresh_frequency": "daily"
  }
}
```

## QA Test Categories
1. **Static Validation**
   - Lint/syntax verification status inherited from coding stage.
   - Dependency and import checks.

2. **Logic Validation**
   - Metric recomputation spot checks.
   - Grain consistency checks.
   - Group-by and distinctness sanity checks.

3. **Data Quality Validation**
   - Critical-field null-rate check (fail if >10%).
   - Duplicate key check at expected grain.
   - Row-count anomaly check against trailing baseline.

4. **Contract Validation**
   - Output schema/type compatibility.
   - Required columns present.
   - Naming and standards conformance.

5. **Audit Validation**
   - Ensure test evidence and run metadata are captured.
   - Generate scorecard and stage summary artifacts.

## Eval Gate (QA Stage)
### Dimension Scores (0.0 to 1.0)
1. **Test Pass Score**
2. **Data Quality Score**
3. **Contract Compliance Score**
4. **Audit Completeness Score**
5. **Operational Readiness Score**

### Pass Criteria
- overall score `>= 0.92`
- no hard errors
- data quality score `= 1.0`
- contract compliance score `= 1.0`

### Failure Policy
- Any failed hard check or below-threshold outcome triggers immediate `ESCALATE_HUMAN`.
- No automated retry loop in QA stage (to prevent silent quality regressions).

## Hard Error Conditions (Auto Escalate)
1. Null-rate critical threshold exceeded.
2. Duplicate violations at expected output grain.
3. Schema contract mismatch in output.
4. Metric mismatch against planning contract.
5. Missing required audit artifacts.

## Eval Output Contract
```json
{
  "agent_name": "qa_audit_eval_agent",
  "status": "ESCALATE_HUMAN",
  "overall_score": 0.79,
  "dimension_scores": {
    "test_pass": 0.90,
    "data_quality": 0.60,
    "contract_compliance": 1.0,
    "audit_completeness": 0.95,
    "operational_readiness": 0.80
  },
  "hard_errors": [
    "Null-rate for device_category is 14.2%, above threshold 10%.",
    "Duplicate keys detected for grain (event_date, device_category)."
  ],
  "warnings": [],
  "next_action": "escalate_human",
  "retryable": false,
  "artifacts": {
    "qa_report_uri": "gs://.../qa_report.json",
    "dq_report_uri": "gs://.../dq_report.json",
    "audit_bundle_uri": "gs://.../audit_bundle.zip"
  },
  "timestamp_utc": "2026-05-04T00:00:00Z"
}
```

## Orchestrator Interaction
- **PASS**: persist QA artifacts and route to Deployment Agent.
- **ESCALATE_HUMAN**: set run status to `blocked`, stop progression, and notify assigned reviewers.

## Jira Auto-Escalation Payload
On QA failure, orchestrator posts:
- Stage: `qa_audit`
- Status: `Blocked`
- Eval score summary
- Hard error list
- Links: QA report, DQ report, audit bundle, logs
- Required action owner + SLA timestamp

## Human Escalation Workflow
1. Assign ticket to on-call DE/reviewer group.
2. Provide remediation checklist derived from hard errors.
3. Require human sign-off and rerun approval before re-entry.
4. Re-entry point is QA stage after fixes are applied upstream.

## Next Implementation Step
Implement QA stage with:
1. test runner abstraction (unit + integration + DQ)
2. QA scorecard generator
3. eval gate policy evaluator (pass/escalate)
4. Jira escalation hook with structured payload
5. artifact publisher for audit evidence
