# Institution Analytics Backlog

This document lists the next backend analytics capabilities needed to fully support a data-driven admissions operating system for institutions.

## Goal

Enable non-technical admissions teams to answer:
- Which markets and demographics are performing best?
- Which channels drive qualified applications?
- Where are applications getting stuck in the funnel?
- Which reviewers/teams are overloaded?

## Current Data Sources Used

- `GET /institutions/me/dashboard` (`DashboardSummary`)
- `GET /institutions/me/analytics` (`AnalyticsData`)
- `GET /institutions/me/campaigns/:id/metrics` (`CampaignMetrics`)
- `GET /institutions/me/events` / `EventItem` (`rsvp_count`, `capacity`)

## Required Additions (Phase 2)

### 1) Applicant Demographics Rollups

API candidate: `GET /institutions/me/analytics/demographics`

Required dimensions:
- nationality
- country_of_residence
- region/state (if available)
- preferred_degree_level (optional)

Expected metrics:
- applications count
- admits count
- conversion rates by segment

### 2) Market Exposure and Attribution

API candidate: `GET /institutions/me/analytics/attribution`

Required dimensions:
- channel/source (campaign, event, organic, referral)
- campaign_id (optional join to campaign name)
- event_id (optional join to event name)

Expected metrics:
- impressions/exposure (if tracked)
- click/engagement count
- applications started/submitted
- admits and yield by source

### 3) Stage Duration and Bottleneck Tracking

API candidate: `GET /institutions/me/analytics/funnel-duration`

Required metrics:
- average time in each stage
- median time in each stage
- drop-off rate by stage
- queue size by stage over time

### 4) Reviewer Workload and Throughput

API candidate: `GET /institutions/me/analytics/reviewer-workload`

Required metrics:
- assigned applications per reviewer
- completed reviews per reviewer
- average decision turnaround
- SLA breach counts (if SLA configured)

## UX Mapping

- **Overview page**: show top-level alerts from workload and stage-duration signals.
- **Insights page**: add deep diagnostics for demographics, attribution, and throughput.
- **Applications workspace**: show contextual warnings (e.g., review backlog aging).

## Notes

- Keep all response payloads explicit and typed to avoid `Record<string, any>` ambiguity.
- Prefer stable keys (`program_id`, `segment_id`) in analytics responses, and include display names as companion fields.
