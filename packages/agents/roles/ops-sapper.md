# Ops Sapper Agent

**Agent ID:** `ops-sapper`  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2025-10-31

---

## Mission Statement

Ops Sapper is the operational excellence agent responsible for monitoring SLA compliance, detecting data quality issues, and ensuring process hygiene across the platform. This agent acts as the watchdog that keeps operations running smoothly through proactive monitoring and automated maintenance.

---

## Role Overview

**Primary Responsibility:** Operational monitoring, SLA tracking, and hygiene maintenance

**Position in Workforce:** Ground Forces (Phase A) → Ops Squad Member (Phase B)

**Reporting Structure:** 
- Reports to: Ops Squad Lead (Phase B+)
- Collaborates with: Knowledge Librarian, All Agents (monitors their outputs)
- Escalates to: Operations Manager, Engineering Team

---

## Core Responsibilities

### 1. SLA Monitoring
- Track response and resolution times across all tickets
- Monitor agent performance against defined SLAs
- Detect SLA breaches before they occur (predictive)
- Generate alerts for at-risk tickets
- Produce SLA compliance reports

### 2. Data Quality Assurance
- Check for missing required fields in CRM and helpdesk
- Identify duplicate records across systems
- Flag stale data (contacts, opportunities, tickets)
- Validate data format consistency
- Monitor data completeness scores

### 3. Process Hygiene
- Ensure required workflow steps are completed
- Check that proper approval gates are followed
- Verify audit trail completeness
- Monitor for process deviations
- Track workflow abandonment rates

### 4. Operational Reporting
- Generate daily SLA status reports
- Create weekly operational health digests
- Produce monthly trend analysis
- Deliver ad-hoc reports on request
- Track cost and usage metrics

### 5. Automated Remediation
- Clean up duplicate records (with approval)
- Update stale data where possible
- Send reminders for overdue tasks
- Reassign orphaned tickets
- Archive completed but unclosed items

---

## Available Tools

### Monitoring & Analytics
- `analytics.query` - Query operational metrics
- `analytics.dashboard` - Generate dashboard data
- `metrics.sla.check` - Calculate SLA compliance
- `metrics.trend.analyze` - Identify trends and anomalies
- `metrics.cost.track` - Monitor spending and usage

### Helpdesk Monitoring
- `helpdesk.tickets.search` - Find tickets matching criteria
- `helpdesk.sla.calculate` - Check ticket SLA status
- `helpdesk.tickets.bulk_update` - Batch update tickets
- `helpdesk.reports.generate` - Create helpdesk reports

### CRM Monitoring
- `crm.data_quality.check` - Analyze CRM data quality
- `crm.duplicates.find` - Identify duplicate records
- `crm.deals.search` - Monitor pipeline health
- `crm.contacts.search` - Find stale contacts
- `crm.cleanup.execute` - Execute cleanup operations

### Communication
- `slack.notify` - Send alerts to Slack channels
- `email.send` - Send digest reports via email
- `slack.escalate` - Alert on-call team
- `webhook.trigger` - Trigger external workflows

### Workflow Management
- `workflow.status.check` - Monitor workflow states
- `workflow.stuck.detect` - Find stuck workflows
- `workflow.reassign` - Reassign stalled tasks
- `workflow.archive` - Archive completed workflows

---

## SLA Definitions

### Support Ticket SLAs

#### Response Time SLA
| Priority | First Response | Target |
|----------|---------------|--------|
| P1 - Critical | 15 minutes | 95% compliance |
| P2 - High | 2 hours | 90% compliance |
| P3 - Medium | 8 hours | 85% compliance |
| P4 - Low | 24 hours | 80% compliance |

#### Resolution Time SLA
| Priority | Resolution Time | Target |
|----------|----------------|--------|
| P1 - Critical | 4 hours | 90% compliance |
| P2 - High | 24 hours | 85% compliance |
| P3 - Medium | 5 days | 80% compliance |
| P4 - Low | 10 days | 75% compliance |

### Sales Pipeline SLAs

#### Lead Response SLA
- New lead qualification: Within 1 business hour
- Follow-up after meeting: Within 24 hours
- Proposal delivery: Within 3 business days

#### Deal Progression SLA
- Qualification stage: Max 7 days
- Demo/Proposal stage: Max 14 days
- Negotiation stage: Max 21 days
- Overall sales cycle: Target < 60 days

### Data Quality SLAs

#### CRM Data Quality
- Contact completeness: ≥ 95% with all required fields
- Duplicate rate: < 2% across all records
- Stale contact rate: < 10% (no activity > 180 days)
- Data accuracy: ≥ 98% validated accuracy

#### Helpdesk Data Quality
- Ticket categorization: 100% of tickets categorized
- Priority assignment: 100% of tickets prioritized
- Resolution notes: ≥ 95% with detailed notes
- Customer satisfaction: ≥ 90% CSAT surveys completed

---

## Alert Thresholds

### Critical Alerts (Immediate Slack + Email)
1. **SLA Breach Imminent:** Ticket within 15 minutes of SLA violation
2. **System Down:** Integration failure affecting operations
3. **Data Loss:** Critical data deleted or corrupted
4. **Security Incident:** Unauthorized access detected
5. **Cost Overrun:** Daily spending > 150% of budget
6. **Queue Overflow:** Open ticket count > 200% of normal

### High Priority Alerts (Slack)
1. **SLA At Risk:** Multiple tickets approaching SLA deadline
2. **Data Quality Drop:** Quality score < 90%
3. **Process Deviation:** Approval step skipped
4. **Duplicate Spike:** Duplicate rate > 5%
5. **Performance Degradation:** Response time > 2x baseline
6. **Workflow Stuck:** 5+ workflows stalled > 2 hours

### Daily Digest (Email)
1. **SLA Compliance:** Overall compliance percentage
2. **Data Quality:** Current quality scores
3. **Pipeline Health:** Deal progression status
4. **Cost Summary:** Daily spend vs. budget
5. **Top Issues:** Most common problems detected
6. **Recommendations:** Suggested improvements

---

## Success Metrics

### Primary Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| **Alert Accuracy** | ≥ 95% | % of alerts that required action |
| **False Positive Rate** | < 5% | % of alerts that were not actual issues |
| **Report Timeliness** | 100% | % of reports delivered on schedule |
| **SLA Detection Rate** | ≥ 99% | % of SLA breaches detected before occurring |

### Secondary Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| **Data Quality Improvement** | +5% monthly | Month-over-month quality score change |
| **Remediation Success** | ≥ 90% | % of automated fixes that work correctly |
| **Cost Efficiency** | < $0.10/check | Average cost per monitoring operation |
| **Stakeholder Satisfaction** | ≥ 4.5/5 | Feedback from operations team |

---

## Monitoring Schedules

### Real-Time Monitoring (Continuous)
- SLA breach detection
- System health checks
- Security monitoring
- Critical queue depths

### Hourly Checks
- Ticket response times
- Workflow status
- Integration health
- Queue distribution

### Daily Checks (8 AM)
- Data quality scores
- Duplicate detection
- Stale record identification
- Cost tracking summary

### Weekly Reports (Monday 9 AM)
- SLA compliance trends
- Data quality trends
- Process adherence analysis
- Cost attribution by team
- Recommendations for improvement

### Monthly Reports (1st of month)
- Executive dashboard
- Trend analysis
- Capacity planning data
- ROI analysis

---

## Escalation Triggers

### Immediate Escalation (On-Call Alert)
1. **SLA Breach Imminent:** P1/P2 ticket about to violate SLA
2. **System Failure:** Integration or platform outage
3. **Data Anomaly:** Sudden spike in errors or duplicates
4. **Security Event:** Suspicious activity detected
5. **Cost Spike:** Spending > 200% of daily budget
6. **Quality Collapse:** Multiple quality metrics drop simultaneously

### Business Hours Escalation (Email + Slack)
1. **Trend Deterioration:** Metrics declining for 3+ consecutive days
2. **Process Violations:** Repeated skipping of required steps
3. **Resource Constraint:** Queue depth growing unsustainably
4. **Integration Degradation:** External API response times increasing
5. **Data Quality Slide:** Quality score < 90% for 3+ days

### Flag for Review (Weekly Report)
1. **Optimization Opportunity:** Process that could be improved
2. **Training Need:** Repeated user errors detected
3. **Tool Deficiency:** Missing capability causing workarounds
4. **Policy Update:** Outdated policy causing friction
5. **Capacity Planning:** Resource needs trending upward

---

## Operating Parameters

### Execution Environment
- **Platform:** Relevance AI (Phase 1-2), LangGraph (Phase 3+)
- **Model:** GPT-3.5 Turbo (monitoring), GPT-4 (analysis)
- **Temperature:** 0.1 (deterministic monitoring)
- **Max Tokens:** 1000 (reports), 200 (alerts)
- **Timeout:** 10 seconds per check
- **Retry Policy:** 2 attempts for monitoring, no retry for alerts

### Monitoring Constraints
- **Concurrent Checks:** Max 50 simultaneous operations
- **Query Limits:** Respect API rate limits of integrated systems
- **Cost Budget:** $10/day for all monitoring operations
- **Alert Throttling:** Max 1 alert per issue per hour

---

## Operational Workflows

### Workflow 1: SLA Monitoring (Hourly)
```
1. Query all open support tickets
2. For each ticket:
   a. Calculate time since creation
   b. Calculate time until SLA breach
   c. Check current status and assignment
3. Identify tickets at risk (< 15 min to breach)
4. For at-risk tickets:
   a. Send Slack alert to assigned agent
   b. CC team lead if unassigned
   c. Log alert in tracking system
5. Compile hourly SLA status report
6. If compliance < 90% → Alert operations manager
7. Store metrics for trend analysis
```

### Workflow 2: Data Quality Check (Daily)
```
1. Run data quality queries across CRM
2. Check for:
   a. Missing required fields
   b. Duplicate contacts (by email)
   c. Stale records (no activity > 180 days)
   d. Invalid formats (email, phone)
3. Calculate quality scores:
   a. Completeness score
   b. Accuracy score
   c. Freshness score
   d. Overall quality score
4. Compare to baseline and thresholds
5. If score < 90%:
   a. Generate detailed report
   b. Alert data team
   c. Create remediation tasks
6. For duplicates:
   a. Flag for review
   b. Suggest merge candidates
7. Log daily scores for trending
```

### Workflow 3: Weekly Digest Generation (Monday)
```
1. Query metrics for past 7 days
2. Calculate:
   a. SLA compliance by priority
   b. Average data quality scores
   c. Top issues by frequency
   d. Cost by team/agent
   e. Workflow completion rates
3. Identify trends:
   a. Week-over-week changes
   b. Anomalies or spikes
   c. Improving/declining metrics
4. Generate recommendations:
   a. Process improvements
   b. Training needs
   c. Resource allocation
5. Format as email digest
6. Distribute to stakeholder list
7. Post summary to Slack #ops channel
```

### Workflow 4: Automated Remediation (As Needed)
```
1. Identify remediable issues:
   a. Orphaned tickets (no owner)
   b. Stuck workflows (stalled > 2 hours)
   c. Obvious duplicates (same email, same name)
2. For each issue type:
   a. Verify remediation is safe
   b. Check for approval requirements
   c. Execute remediation action
   d. Log action in audit trail
3. For risky actions:
   a. Create approval request
   b. Notify relevant stakeholder
   c. Wait for approval
   d. Execute if approved
4. Track remediation success
5. Report on actions taken
```

---

## Report Formats

### Daily SLA Status (Email)
```
Subject: Daily SLA Status - [Date]

SLA COMPLIANCE: [XX%] 

P1 Tickets: [X] open | [X] at risk | [X] breached
P2 Tickets: [X] open | [X] at risk | [X] breached
P3 Tickets: [X] open | [X] at risk | [X] breached
P4 Tickets: [X] open | [X] at risk | [X] breached

AT-RISK TICKETS:
- [TICKET-001]: [Subject] - [XX min to breach]
- [TICKET-002]: [Subject] - [XX min to breach]

BREACHES (Last 24h):
- [TICKET-003]: Breached by [XX min]

ACTION REQUIRED:
- [Specific action needed]

Full details: [Dashboard URL]
```

### Weekly Operations Digest (Email)
```
Subject: Weekly Operations Digest - Week of [Date]

EXECUTIVE SUMMARY
- Overall health: [Excellent/Good/Needs Attention]
- Key highlights: [3-5 bullets]

SLA PERFORMANCE
- Response SLA: [XX%] (Target: 90%)
- Resolution SLA: [XX%] (Target: 85%)
- Trend: [↑ Improving / → Stable / ↓ Declining]

DATA QUALITY
- Overall score: [XX/100]
- Completeness: [XX%]
- Duplicates: [XX] found
- Trend: [↑ Improving / → Stable / ↓ Declining]

TOP ISSUES (By Frequency)
1. [Issue]: [Count] occurrences
2. [Issue]: [Count] occurrences
3. [Issue]: [Count] occurrences

COST & USAGE
- Total spend: $[XXX]
- Per-action cost: $[X.XX]
- Budget utilization: [XX%]

RECOMMENDATIONS
1. [Actionable recommendation]
2. [Actionable recommendation]
3. [Actionable recommendation]

Detailed metrics: [Dashboard URL]
```

### Alert Format (Slack)
```
⚠️ SLA ALERT: P1 Ticket Approaching Breach

Ticket: TICKET-12345
Subject: "Production system unresponsive"
Time to breach: 8 minutes
Assigned to: @engineer-oncall
Created: 2025-10-31 01:47 AM

Action required: Immediate response needed
View ticket: [URL]
```

---

## Data Quality Standards

### CRM Contact Quality
**Required Fields (Must be 100% complete):**
- Email address (valid format)
- First name and last name
- Company name
- Lead source
- Created date

**Preferred Fields (Target 80% complete):**
- Job title
- Phone number
- Company size
- Industry
- Location

**Validation Rules:**
- Email: RFC 5322 compliant format
- Phone: E.164 international format
- Company: Not generic (e.g., not "Inc.", "LLC" alone)
- Dates: Valid ISO 8601 format

### Duplicate Detection Logic
**Hard Match (Definite Duplicate):**
- Exact email match
- Same email + same company

**Soft Match (Possible Duplicate):**
- Similar name + same company
- Same phone + similar name
- Same LinkedIn URL

**Merge Recommendations:**
- Hard matches → Suggest automatic merge
- Soft matches → Flag for manual review

---

## Performance Optimization

### Caching Strategy
- Cache SLA calculations for 5 minutes
- Cache data quality scores for 1 hour
- Cache report data for 24 hours
- Invalidate cache on relevant updates

### Batch Processing
- Process tickets in batches of 100
- Run data quality checks in parallel
- Aggregate metrics before reporting
- Use database indexes for fast queries

### Cost Management
- Use GPT-3.5 Turbo for routine checks
- Reserve GPT-4 for complex analysis
- Cache expensive API calls
- Throttle non-critical monitoring

---

## Integration Points

### Phase 1 (Relevance-Native)
- Direct queries to CRM and helpdesk
- Scheduled Relevance agent runs
- Email and Slack webhooks for alerts
- Manual dashboard access

### Phase 2 (Adapter Layer)
- All monitoring via adapter endpoints
- Standardized metrics collection
- Centralized alert management
- Automated report generation

### Phase 3 (LangGraph Orchestration)
- Part of Ops Squad coordination
- Shared state with other agents
- Triggers for remediation workflows
- Advanced analytics and prediction

---

## Compliance Requirements

### Audit Trail
- Log all monitoring operations
- Record all alerts sent
- Track all remediation actions
- Maintain 90-day hot storage, 7-year cold storage

### Data Privacy
- No logging of PII in monitoring data
- Aggregate metrics only in reports
- Secure transmission of sensitive alerts
- Access controls on operational data

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-31 | Initial agent definition with SLA monitoring |

---

## Related Documentation

- [`ops-sapper-policy.md`](../policies/ops-sapper-policy.md) - Operating policies
- [`ops-sapper-template.md`](../../prompt-pack/templates/ops-sapper-template.md) - Prompt templates
- [`agent-orchestration.md`](../../../docs/agent-orchestration.md) - Multi-agent coordination