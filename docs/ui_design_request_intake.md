# UI Design: ETL User Story Intake (Week 1)

## Objective
Design the first intake UI where a user can submit ETL user stories for autonomous processing.

## Implemented Prototype
- File: `ui/request_intake_form.html`
- Type: Static HTML prototype (form-first design)
- Scope: Week 1 user stories (US-06, US-07, US-08) with preset autofill

## Included Fields
1. Request Name
2. Description / User Story
3. Source Tables
4. Output Table (optional)
5. Expected Scheduling Time
6. Refresh Frequency
7. Jira Number (optional)
8. Timezone (default US Eastern)
9. Null-rate threshold

## UX Features
- **Preset selector** for US-06/07/08 to reduce manual entry
- **Save Draft** and **Submit to Orchestrator** actions
- Built-in **improvement recommendations** section

## Suggested Improvements (next iteration)
- Add schema picker from BigQuery metadata
- Add GA4 event_params extraction helper
- Add acceptance criteria checklist with validation status
- Add live SQL preview + estimated bytes scanned
- Add Jira sync toggle for work-in-progress updates and artifact links
- Add owner/approver and priority fields for governance

## Notes
This prototype is designed to be a front-end starting point and can be ported to Streamlit, React, or internal portal frameworks.
