# Ops Sapper Agent - Operating Policies

**Agent ID:** `ops-sapper`  
**Version:** 1.0.0  
**Last Updated:** 2025-10-31

---

## Policy Overview

This document defines SLA monitoring procedures, alert criteria, reporting standards, and data retention policies for the Ops Sapper Agent.

---

## 1. SLA Definitions and Thresholds

### 1.1 Support Ticket SLAs

**Response Time SLA (Time to First Response):**
```
Priority | Target Time | Compliance Target | Alert Threshold
---------|-------------|-------------------|----------------
P1       | 15 minutes  | 95%              | 12 minutes
P2       | 2 hours     | 90%              | 1.75 hours
P3       | 8 hours     | 85%              | 7 hours
P4       | 24 hours    | 80%              | 22 hours
```

**Resolution Time SLA (Time to Resolution):**
```
Priority | Target Time | Compliance Target | Alert Threshold
---------|-------------|-------------------|----------------
P1       | 4 hours     | 90%              | 3.5 hours
P2       | 24 hours    | 85%              | 22 hours
P3       | 5 days      | 80%              | 4.5 days
P4       | 10 days     | 75%              | 9 days
```

### 1.2 SLA Clock Rules

**Clock Starts:**
- When ticket is created in system
- Timestamp recorded in UTC

**Clock Pauses:**
- When waiting for customer response
- During scheduled maintenance windows
- Outside business hours (if contract specifies)

**Clock Resumes:**
- When customer responds
- When maintenance window ends
- At start of business hours

**Clock Stops:**
- First response sent (Response SLA)
- Ticket marked as "Solved" (Resolution SLA)

**Business Hours Definition:**
- Default: Monday-Friday, 8 AM - 6 PM customer timezone
- Enterprise: 24/7 coverage
- Custom: Per contract terms

### 1.3 SLA Compliance Calculation

**Formula:**
```
compliance_rate = (tickets_within_sla / total_tickets) * 100

Example:
P1 tickets this month: 100
P1 tickets within 15 min: 96
Compliance: 96% ✓ (Target: 95%)
```

**Reporting Period:**
- Calculate daily for dashboards
- Report weekly for operations review
- Evaluate monthly for SLA compliance certification

---

## 2. Alert Priority Levels

### 2.1 Critical Alerts (Immediate Response Required)

**Trigger Conditions:**
- SLA breach imminent (<15 min for P1/P2)
- System integration failure
- Data corruption or loss detected
- Security incident flagged
- Daily cost >150% of budget
- Queue depth >200% of normal

**Alert Actions:**
```
1. Send Slack notification to @ops-oncall
2. Send email to operations manager
3. Create high-priority incident ticket
4. Log alert in incident management system
5. Escalate if no acknowledgment in 5 minutes
```

**Response Time Requirement:**
- Acknowledge: Within 5 minutes
- Initial action: Within 15 minutes
- Status update: Every 30 minutes until resolved

### 2.2 High Priority Alerts (Business Hours Response)

**Trigger Conditions:**
- Multiple tickets approaching SLA deadline
- Data quality score drops below 90%
- Process approval step skipped
- Duplicate record rate exceeds 5%
- Response time increases >50% above baseline
- 5+ workflows stalled >2 hours

**Alert Actions:**
```
1. Send Slack notification to #ops-alerts
2. Add to operations dashboard (red indicator)
3. Include in next hourly status check
4. Create standard priority ticket
5. Notify team lead
```

**Response Time Requirement:**
- Acknowledge: Within 1 hour
- Investigation start: Within 4 hours
- Resolution plan: Within 24 hours

### 2.3 Daily Digest (Scheduled Report)

**Delivery Schedule:**
- Time: 8:00 AM local time
- Recipients: Operations team, managers
- Format: Email with dashboard link

**Contents:**
- SLA compliance summary (past 24 hours)
- Data quality metrics
- Top issues by frequency
- Cost summary
- Recommendations

**No Immediate Action Required**
- For information and trending
- Reviewed during daily standup
- Action items added to backlog

---

## 3. Report Frequency and Format

### 3.1 Hourly SLA Checks

**Scope:**
- All open support tickets
- Ticket aging analysis
- At-risk ticket identification
- Queue distribution

**Output:**
- Internal log (not distributed)
- Alerts generated as needed
- Dashboard updated in real-time

### 3.2 Daily Reports

**SLA Status Report:**
```
Subject: Daily SLA Status - [Date]

OVERALL: ✓ 94% Compliance (Target: 90%)

BY PRIORITY:
P1: 96% (48/50 within SLA) ✓
P2: 92% (92/100 within SLA) ✓
P3: 88% (176/200 within SLA) ✓
P4: 84% (84/100 within SLA) ✓

AT-RISK TICKETS (Next 2 Hours):
- TICKET-12345: 8 min to breach [P1]
- TICKET-12346: 45 min to breach [P2]

BREACHES (Last 24h): 2
- TICKET-12340: P2, breached by 15 min (system outage)
- TICKET-12342: P3, breached by 3 hours (assigned to wrong queue)

Full details: [Dashboard URL]
```

### 3.3 Weekly Digests

**Operations Health Report:**
```
# Weekly Operations Digest - Week of [Date]

## Executive Summary
- Overall Health: ✓ GOOD
- SLA Compliance: 93% (Target: 90%) ✓
- Data Quality: 96% (Target: 95%) ✓
- Key Issues: Queue imbalance detected, rebalancing implemented

## SLA Performance
| Priority | This Week | Last Week | Target | Status |
|----------|-----------|-----------|--------|--------|
| P1       | 95%       | 94%       | 95%    | ✓      |
| P2       | 91%       | 89%       | 90%    | ✓      |
| P3       | 87%       | 88%       | 85%    | ✓      |
| P4       | 82%       | 80%       | 80%    | ✓      |

## Data Quality
- Completeness: 97%
- Duplicates found: 12 (0.5%)
- Stale records: 24 (1.0%)

## Top Issues (By Frequency)
1. Authentication errors: 45 tickets
2. Report generation timeout: 28 tickets
3. Integration sync delay: 19 tickets

## Cost & Efficiency
- Total spend: $2,340
- Per-ticket cost: $4.68
- Budget utilization: 78%

## Recommendations
1. Increase queue capacity during peak hours (2-4 PM)
2. Add KB article for authentication errors
3. Investigate report generation performance
```

### 3.4 Monthly Reports

**Executive Dashboard:**
- SLA trends (month-over-month)
- Cost analysis and attribution
- Capacity planning projections
- Strategic recommendations
- Compliance certifications

---

## 4. Data Retention Policies

### 4.1 Operational Data Retention

**Hot Storage (Immediate Access):**
- Duration: 90 days
- Location: Primary database
- Access: Unrestricted (authorized users)
- Includes: All metrics, logs, alerts

**Warm Storage (Archive):**
- Duration: 1 year
- Location: Archive database
- Access: On-demand retrieval
- Includes: Historical trends, compliance records

**Cold Storage (Compliance):**
- Duration: 7 years
- Location: Secure archive (S3/Glacier)
- Access: Request-based only
- Includes: Audit logs, incident reports

**Deletion Policy:**
- Personal data: Honor GDPR deletion requests
- Aggregated metrics: Retain indefinitely
- Incident reports: 7 years minimum (regulatory)
- Operational logs: Per retention schedule above

### 4.2 Alert History Retention

**Alert Records Must Include:**
- Alert ID and correlation ID
- Timestamp (UTC)
- Alert type and priority
- Trigger condition
- Affected systems/tickets
- Actions taken
- Resolution timestamp
- Acknowledgment by (user)

**Retention Period:**
- Critical alerts: 2 years
- High priority alerts: 1 year
- Daily digests: 90 days
- False positives: 30 days (for analysis)

---

## 5. Error Handling Procedures

### 5.1 Monitoring Failures

**When Monitoring Check Fails:**

**Transient Failure (Single Check):**
```
1. Log failure with error details
2. Retry operation immediately
3. If retry succeeds → Continue normally
4. If retry fails → Escalate to persistent failure
```

**Persistent Failure (3 Consecutive Checks):**
```
1. Create critical incident ticket
2. Alert operations team via Slack
3. Switch to backup monitoring if available
4. Investigate root cause
5. Notify affected stakeholders
6. Restore primary monitoring
7. Post-mortem after resolution
```

**Integration Outage:**
```
IF integration == "crm" OR integration == "helpdesk":
    # Critical - affects SLA monitoring
    priority = "P1"
    alert_immediate = True
    use_fallback_method = True
ELSE:
    priority = "P2"
    alert_business_hours = True
    queue_for_retry = True
```

### 5.2 False Positive Management

**When Alert is False Positive:**
1. Document why it was false positive
2. Update alert logic to prevent recurrence
3. Track false positive rate
4. If rate >5% → Review alert threshold
5. Apologize to alerted team if critical

**False Positive Tracking:**
- Target rate: <5% of all alerts
- Review weekly for patterns
- Adjust thresholds quarterly
- Balance sensitivity vs noise

### 5.3 Data Anomaly Handling

**Unexpected Data Patterns:**
```
IF metric_value > (baseline + 3*std_dev):
    flag_as_anomaly
    verify_data_source
    IF data_source_valid:
        alert_as_real_anomaly
    ELSE:
        log_data_quality_issue
        alert_data_team
```

**Anomaly Types:**
- Spike: Sudden increase >3σ
- Drop: Sudden decrease >3σ
- Flatline: No variation for extended period
- Oscillation: Rapid fluctuation beyond normal

---

## 6. Process Compliance Verification

### 6.1 Required Workflow Steps

**Critical Steps That Must Be Verified:**

**Support Tickets:**
- [ ] Ticket categorized within 15 minutes
- [ ] Priority assigned at creation
- [ ] First response sent within SLA
- [ ] Escalation includes full context
- [ ] Resolution documented
- [ ] Customer satisfaction survey sent

**Sales Opportunities:**
- [ ] Lead qualified before opportunity creation
- [ ] BANT criteria documented
- [ ] Approval obtained for discounts >10%
- [ ] Contract reviewed by legal (enterprise deals)
- [ ] Deal closed-won/lost reason documented

**Data Management:**
- [ ] Duplicate check before contact creation
- [ ] Required fields populated
- [ ] Data validation passed
- [ ] Changes logged in audit trail

### 6.2 Approval Gate Enforcement

**Discount Approval Matrix:**
```
Discount % | Approver Required
-----------|------------------
0-10%      | Sales Rep (auto-approved)
11-20%     | Sales Manager
21-30%     | VP Sales
>30%       | CFO
```

**Verification Process:**
```
IF approval_required AND approval_missing:
    block_transaction
    alert_responsible_party
    log_compliance_violation
    notify_manager
```

### 6.3 Audit Trail Requirements

**Every Significant Action Must Log:**
- What was done (action type)
- Who did it (user/agent ID)
- When (timestamp UTC)
- Why (business justification)
- What changed (before/after state)
- Approval status (if applicable)

**Immutable Audit Log:**
- Append-only (no deletions)
- Tamper-evident (checksums)
- Encrypted at rest
- Access controlled and logged

---

## 7. Alert Throttling and Deduplication

### 7.1 Throttling Rules

**Same Alert Type:**
- Max 1 alert per issue per hour
- After first alert, suppress duplicates
- Send summary every 4 hours if ongoing
- Resume normal alerts when issue changes

**Example:**
```
SLA Breach Alert for TICKET-123:
- First alert: Sent immediately
- Same ticket 10 min later: Suppressed
- Same ticket 65 min later: Send update
- Different ticket 5 min later: Send new alert
```

### 7.2 Alert Aggregation

**Multiple Related Issues:**
```
IF same_issue_type AND count >= 5:
    aggregate_into_single_alert
    message = "5 tickets approaching SLA breach (P2)"
    include_ticket_list
ELSE:
    send_individual_alerts
```

**Aggregation Window:**
- Time window: 15 minutes
- Max individual alerts: 5
- After threshold: Switch to aggregated

### 7.3 Escalation Ladder

**No Response to Alert:**
```
Time 0:   Alert sent to @ops-oncall
Time +5:  No ack → Escalate to operations manager
Time +15: No ack → Escalate to VP Operations
Time +30: No ack → Page executive on-call
```

**Auto-Acknowledgment:**
- Alert acknowledged automatically if action taken
- Manual acknowledgment not required for routine alerts
- Critical alerts require explicit human acknowledgment

---

## 8. Performance Optimization

### 8.1 Query Efficiency

**Monitoring Queries:**
- Use indexed fields for filtering
- Limit result sets appropriately
- Cache expensive calculations
- Use database read replicas
- Avoid full table scans

**Query Time Limits:**
- Simple queries: <1 second
- Complex aggregations: <10 seconds
- Report generation: <60 seconds
- If exceeded: Optimize or pre-calculate

### 8.2 Cost Management

**Budget Allocation:**
- Daily budget: $10
- Alert if spend >$8 in single day
- Investigate if >$12 (120% of budget)
- Optimize if consistent overspend

**Cost Optimization Strategies:**
- Use GPT-3.5 Turbo for routine checks
- Cache monitoring results (5 min TTL)
- Batch operations where possible
- Use database queries over API calls
- Monitor only what's necessary

### 8.3 Concurrency Management

**Parallel Operations:**
- Max 50 concurrent monitoring checks
- Queue additional checks if at limit
- Prioritize critical checks (P1/P2 SLA)
- Use connection pooling for databases

---

## 9. Quality Assurance

### 9.1 Alert Accuracy Standards

**Target Metrics:**
- True positive rate: ≥95%
- False positive rate: <5%
- Missed alerts: <1%
- Alert latency: <30 seconds

**Regular Validation:**
- Spot check 10 alerts per week
- Verify accuracy of measurements
- Confirm alert logic correctness
- Review false positive causes

### 9.2 Report Accuracy

**Pre-Delivery Checklist:**
- [ ] Data aggregation verified
- [ ] Calculations double-checked
- [ ] Trends accurate (compare to manual)
- [ ] Links functional
- [ ] Recipients list current
- [ ] Formatting consistent

**Automated Validation:**
- Cross-check totals with source data
- Verify percentages sum correctly
- Confirm date ranges accurate
- Test dashboard links

---

## 10. Continuous Improvement

### 10.1 Metrics Review

**Weekly:**
- Alert accuracy and usefulness
- False positive analysis
- Response time to alerts
- SLA compliance trends

**Monthly:**
- Process efficiency improvements
- New monitoring opportunities
- Tool optimization
- Cost per check analysis

**Quarterly:**
- Strategic planning
- Capacity forecasting
- Tool evaluation
- Policy updates

### 10.2 Feedback Integration

**Collect Feedback From:**
- Operations team on alert quality
- Managers on report usefulness
- Stakeholders on dashboard value
- Support team on SLA accuracy

**Act On Feedback:**
- Adjust alert thresholds
- Modify report formats
- Add new monitoring checks
- Remove low-value metrics

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-31 | Initial policy document |

---

## Related Documentation

- [`ops-sapper.md`](../roles/ops-sapper.md) - Role definition
- [`ops-sapper-template.md`](../../prompt-pack/templates/ops-sapper-template.md) - Prompt templates
- [SLA Definitions](../../../docs/sla-standards.md) - Company-wide SLA policies