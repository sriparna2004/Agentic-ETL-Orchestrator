# Week 1 Use Cases: GA4 Aggregation Stories (CX R&D Focus)

## Purpose
This document finalizes Week 1 aggregation use cases and acceptance criteria for the Autonomous ETL agent running on GCP BigQuery (GA4 source).

## Global Operating Assumptions (applies to all use cases)
1. **Backfill strategy:** Full backfill.
2. **Timezone standard:** US Eastern Time (`America/New_York`).
3. **Null geo handling:** Keep null/blank geo values as `UNKNOWN`.
4. **Write strategy:** Incremental `MERGE` into target tables.
5. **Batch schedule:** Daily at **7:00 AM EST/EDT** (US Eastern local time).
6. **Data quality threshold:** Pipeline fails if null rate for critical fields is **> 10%**.
   - This threshold can be tuned later based on observed trend and baseline stability.

---

## US-06: Daily Active Users (DAU)

### User Story
As a CX R&D analyst, I need a daily summary table of unique users so that I can track engagement trends by device type.

### Source
- GA4 BigQuery export table pattern: `<project>.<dataset>.events_*`

### Target
- `cx_reporting.daily_unique_users`

### Aggregation Logic
- Metric: `dau = COUNT(DISTINCT user_pseudo_id)`
- Group by:
  - `event_date` (converted/reporting in US Eastern date context)
  - `device.category` as `device_category`

### Acceptance Criteria
- One row exists for each unique (`event_date`, `device_category`) combination.
- `dau` is non-negative.
- `event_date` is not null.
- Full backfill is supported.
- Job uses partition-aware filtering for efficient reads.
- Load is idempotent via `MERGE`.

---

## US-07: Average Engagement per Page

### User Story
As a CX R&D analyst, I need average engagement time per page URL so that I can identify high- and low-performing pages.

### Source
- GA4 BigQuery export table pattern: `<project>.<dataset>.events_*`
- `event_params` extraction required for:
  - `page_location`
  - `engagement_time_msec`

### Target
- `cx_reporting.page_engagement_stats`

### Aggregation Logic
- Filter: `event_name = 'page_view'`
- Extract event params via `UNNEST(event_params)`.
- Metric: `avg_engagement_time_msec = AVG(engagement_time_msec)`
- Group by: `page_location`

### Acceptance Criteria
- Only `page_view` events are included.
- Null/empty `page_location` values are excluded or standardized per rule.
- Numeric conversion for `engagement_time_msec` is safe (no hard query failure due to bad values).
- Result includes one row per unique `page_location`.
- Full backfill is supported.
- Load is idempotent via `MERGE`.
- Null rate of critical fields >10% triggers failure.

---

## US-08: Regional Traffic Spikes (Hourly)

### User Story
As a CX R&D analyst, I need hourly traffic by region/city so that I can monitor regional spikes and potential network load concerns.

### Source
- GA4 BigQuery export table pattern: `<project>.<dataset>.events_*`

### Target
- `cx_reporting.hourly_regional_traffic`

### Aggregation Logic
- Hour window in US Eastern timezone.
- `hour_bucket = TIMESTAMP_TRUNC(event_timestamp_converted_to_est, HOUR)`
- Metric: `event_count = COUNT(*)`
- Group by:
  - `hour_bucket`
  - `geo.region` (default `UNKNOWN` when null/blank)
  - `geo.city` (default `UNKNOWN` when null/blank)

### Acceptance Criteria
- One row exists per (`hour_bucket`, `region`, `city`) combination.
- Null/blank geo values are represented as `UNKNOWN`.
- Time bucketing reflects US Eastern local time.
- Full backfill is supported.
- Load is idempotent via `MERGE`.
- Null rate of critical fields >10% triggers failure.

---

## Shared Data Quality Rules
- **Critical field null checks:** fail when null rate >10%.
- **Uniqueness checks:** enforce expected grain per table.
- **Freshness check:** daily batch should complete after 7:00 AM US Eastern schedule.
- **Volume sanity:** compare with trailing trend (e.g., previous 7 days) and flag large deviations.

## Note on Threshold Adaptation
The 10% null threshold is the initial guardrail. It can be adjusted over time using observed distributions, seasonal behavior, and confidence intervals from recent runs.
