# Central Orchestrator Design (Post-Intake Eval)

## Objective
Define the **Central Orchestrator** that receives requests after Intake Eval and controls routing, retries, eval-gated transitions, and Jira progress updates across all downstream agents.

## Entry Condition
The orchestrator starts processing only when Intake Eval returns:
- `status = PASS`
- `next_action = continue`

If Intake Eval returns `RETRY` or `ESCALATE_HUMAN`, the orchestrator does not proceed to downstream execution.

## Responsibilities
1. Maintain a canonical run state for each request.
2. Route work to the next agent in sequence.
3. Enforce eval gates after each agent completes.
4. Trigger bounded retries using critique/fix prompts.
5. Escalate to human when retries exceed limits or hard failures occur.
6. Post Jira work-in-progress updates and artifact links.
7. Emit final run summary (success/failure, scores, timestamps, links).

## Downstream Agent Chain (Initial)
1. **Schema & MCP Validation Agent**
2. **Planner Agent**
3. **Code Generation Agent**
4. **QA & Audit Agent**
5. **Deployment Agent**

Every stage must return a standardized eval output contract.

## Orchestrator State Model
```json
{
  "run_id": "orch_2026_05_01_0001",
  "request_id": "CX-142",
  "current_stage": "schema_validation",
  "stage_status": "in_progress",
  "overall_status": "running",
  "retry_count_by_stage": {
    "schema_validation": 0,
    "planner": 0,
    "codegen": 0,
    "qa_audit": 0,
    "deployment": 0
  },
  "stage_eval_history": [],
  "artifacts": {
    "pr_url": null,
    "bq_job_urls": [],
    "log_urls": [],
    "gcs_paths": []
  },
  "jira": {
    "ticket": "CX-142",
    "last_status": "In Progress",
    "last_comment_id": null
  },
  "timestamps": {
    "started_at_utc": "2026-05-01T00:00:00Z",
    "updated_at_utc": "2026-05-01T00:00:00Z"
  }
}
```

## Routing Policy
For each stage output (`eval_result`):

- **PASS path**
  - Record eval result and artifacts.
  - Update Jira comment with stage summary.
  - Route to next stage.

- **RETRY path**
  - If retry count `< max_retry_per_stage` (default: 2), re-run same stage with critique context.
  - If retry count exceeded, escalate human.

- **ESCALATE_HUMAN path**
  - Stop pipeline.
  - Mark overall status `blocked`.
  - Update Jira status to `Blocked` with reasons.

## Eval Gate Contract (Required from Every Stage)
```json
{
  "agent_name": "planner_agent",
  "status": "PASS",
  "overall_score": 0.91,
  "hard_errors": [],
  "warnings": [],
  "next_action": "continue",
  "artifacts": {
    "log_url": "https://...",
    "output_uri": "gs://..."
  },
  "timestamp_utc": "2026-05-01T00:00:00Z"
}
```

## Stage Transition Matrix
| Current Stage | Eval Status | Orchestrator Action | Next Stage |
|---|---|---|---|
| schema_validation | PASS | persist eval + Jira update | planner |
| schema_validation | RETRY | rerun with critique (if retries left) | schema_validation |
| schema_validation | ESCALATE_HUMAN | block run + Jira blocked | stop |
| planner | PASS | persist eval + Jira update | codegen |
| planner | RETRY | rerun with critique (if retries left) | planner |
| planner | ESCALATE_HUMAN | block run + Jira blocked | stop |
| codegen | PASS | persist eval + Jira update | qa_audit |
| codegen | RETRY | rerun with critique (if retries left) | codegen |
| codegen | ESCALATE_HUMAN | block run + Jira blocked | stop |
| qa_audit | PASS | persist eval + Jira update | deployment |
| qa_audit | RETRY | rerun with critique (if retries left) | qa_audit |
| qa_audit | ESCALATE_HUMAN | block run + Jira blocked | stop |
| deployment | PASS | close run + Jira ready for review | end_success |
| deployment | RETRY | rerun with critique (if retries left) | deployment |
| deployment | ESCALATE_HUMAN | block run + Jira blocked | stop |

## Jira Integration Pattern
At minimum, orchestrator posts updates:
1. On orchestration start: `In Progress`
2. After each stage eval: score + warnings + links
3. On success: `Ready for Review` + PR/artifact links
4. On escalation: `Blocked` + error reason + last logs

## Failure Handling
- **Transient errors**: retry stage (bounded).
- **Policy/validation errors**: no blind retries; require corrected input or escalate.
- **Idempotency**: use `run_id` and stage checkpointing to avoid duplicate execution.

## Observability and Audit
Track and store:
- stage-level latency
- stage-level token/cost usage (if available)
- score trends per stage
- retry counts
- final outcome and reason

## Next Implementation Step
Implement orchestrator as a LangGraph state machine with:
- one router node (decision node)
- one worker node per stage
- shared state store for checkpoints
- unified eval parser enforcing contract validation before transitions
