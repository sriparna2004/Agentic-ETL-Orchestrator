# PySpark Coding Agent Design with Eval + Refactor Retry Loop (Stage 4)

## Objective
Define the **PySpark Coding Agent**, its **Eval Agent**, and **Refactor-Retry Loop** so approved plans are translated into production-quality PySpark code with bounded self-correction before QA/Deployment.

## Placement in Flow
1. Intake Eval -> PASS
2. Schema & MCP Validation -> PASS
3. Planning + Critique -> PASS
4. Central Orchestrator routes to **PySpark Coding Agent**
5. Coding Eval Agent returns `PASS` / `RETRY` / `ESCALATE_HUMAN`
6. If RETRY -> Refactor pass and re-evaluate
7. If PASS -> return control to Central Orchestrator for QA/Audit stage

## PySpark Coding Agent Responsibilities
1. Convert approved planning contract into modular PySpark pipeline code.
2. Generate clear modules for extract, transform, aggregate, and load.
3. Implement partition-aware reads and idempotent target writes (`MERGE` strategy).
4. Include configuration and parameter hooks for environment portability.
5. Emit code artifacts + metadata for downstream evaluation.

## Inputs
```json
{
  "run_id": "orch_2026_05_04_0003",
  "planning_output": {
    "plan_id": "plan_2026_05_04_01",
    "target_table": "cx_reporting.hourly_regional_traffic",
    "grain": ["hour_bucket", "geo.region", "geo.city"],
    "steps": ["extract", "transform", "aggregate", "publish"],
    "checks": {
      "partition_filter_required": true,
      "dq_null_threshold_pct": 10
    }
  },
  "schema_contract": {
    "resolved_tables": ["analytics_123456.events_20260503"],
    "required_fields": ["event_timestamp", "geo.city", "geo.region"],
    "nested_keys": []
  },
  "runtime_constraints": {
    "timezone": "America/New_York",
    "refresh_frequency": "daily",
    "write_mode": "MERGE"
  },
  "retry_context": {
    "attempt": 0,
    "prior_eval_feedback": []
  }
}
```

## Code Artifact Outputs
1. `jobs/<request_slug>/main.py`
2. `jobs/<request_slug>/transforms.py`
3. `jobs/<request_slug>/io.py`
4. `jobs/<request_slug>/config.yaml`
5. `jobs/<request_slug>/README.md` (run instructions and assumptions)

## Coding Standards (Stage Rules)
1. No unresolved schema references.
2. No unused imports/variables.
3. Explicit partition predicate for source scans.
4. Explicit timezone conversion where required.
5. Deterministic aggregation and grouping semantics.
6. Idempotent write path and error-aware logging.

## Coding Eval Agent
The Coding Eval Agent runs automatically after code generation.

### Eval Dimensions (0.0 to 1.0)
1. **Compilation/Lint Score**
   - Python syntax and lint conformance.
2. **Plan Fidelity Score**
   - Generated logic matches planning contract.
3. **Schema Compliance Score**
   - Referenced columns/tables align with schema contract.
4. **Performance Safety Score**
   - Partition pruning and anti-pattern checks pass.
5. **Maintainability Score**
   - Modular structure, naming, comments, and readability.

### Pass Criteria
- overall score `>= 0.90`
- compilation/lint score `= 1.0`
- schema compliance score `= 1.0`
- no hard errors

### Retry Criteria
- hard errors absent but pass thresholds not met.
- refactor can resolve issues automatically.

### Escalation Criteria
- hard errors persist after retries.
- retry limit exceeded (`max_retry_per_stage` from orchestrator policy).

## Hard Error Conditions
1. Generated code cannot parse/compile.
2. References non-existent schema fields/tables.
3. Missing mandatory load/publish logic.
4. Contradicts approved plan grain/metrics.

## Eval Output Contract
```json
{
  "agent_name": "pyspark_coding_eval_agent",
  "status": "RETRY",
  "overall_score": 0.87,
  "dimension_scores": {
    "compilation_lint": 1.0,
    "plan_fidelity": 0.84,
    "schema_compliance": 1.0,
    "performance_safety": 0.78,
    "maintainability": 0.82
  },
  "hard_errors": [],
  "warnings": [
    "Source read missing explicit _TABLE_SUFFIX predicate.",
    "Transformation module has duplicated timestamp conversion logic."
  ],
  "refactor_actions": [
    "Inject partition filter helper in extract layer.",
    "Consolidate timezone conversion into shared utility function."
  ],
  "next_action": "retry",
  "retryable": true,
  "retry_count": 1,
  "artifacts": {
    "code_bundle_uri": "gs://.../codegen_attempt_1.zip",
    "lint_report_uri": "gs://.../lint_report.json"
  },
  "timestamp_utc": "2026-05-04T00:00:00Z"
}
```

## Refactor-Retry Loop
### Trigger
When Coding Eval status is `RETRY`.

### Refactor Agent Responsibilities
1. Apply eval feedback to generated PySpark modules.
2. Minimize code churn (targeted edits only).
3. Preserve plan fidelity while improving quality/compliance.
4. Re-run lint/static checks and emit a delta summary.

### Retry Sequence
1. Coding Agent generates draft.
2. Eval Agent scores draft.
3. If RETRY, Refactor Agent applies targeted changes.
4. Re-run Eval Agent.
5. Repeat until PASS or retry limit exceeded.

### Boundaries
- default max retries: `2`
- if still failing after max retries -> `ESCALATE_HUMAN`

## Orchestrator Interaction
- **PASS**: persist code artifact + eval, then route to QA/Audit Agent.
- **RETRY**: invoke refactor sub-step and re-evaluate in same stage.
- **ESCALATE_HUMAN**: mark run blocked, post Jira update with lint/eval reports.

## Jira Update Payload (Coding Stage)
For each codegen/refactor attempt:
- Stage: `pyspark_codegen`
- Attempt number
- Eval status and scores
- Key warnings/errors
- Refactor actions taken
- Artifact links (code bundle, lint report)
- Next action

## Next Implementation Step
Implement Stage 4 with:
1. plan-to-code generator templates
2. static code analysis runner (lint + custom anti-pattern checks)
3. eval scorer and structured feedback emitter
4. targeted refactor engine
5. orchestrator hooks for retry loop lifecycle
