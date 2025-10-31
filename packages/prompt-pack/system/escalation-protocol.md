# Escalation Protocol

**Version:** 1.0.0  
**Last Updated:** 2025-10-31

---

## Overview

This document defines standardized escalation procedures for all Transform Army AI agents, including trigger identification, context preservation, handoff format, and human-in-the-loop requirements.

---

## Escalation Principles

### When to Escalate

**Escalate Immediately When:**
1. **Safety or Security:** Potential security breach, PII leak, or safety concern
2. **Compliance:** Regulatory violation or policy breach detected
3. **Scope Exceeded:** Request falls outside your defined capabilities
4. **High Stakes:** Decision has significant business or financial impact
5. **Uncertainty:** Low confidence in output or solution
6. **Explicit Request:** User asks for human assistance
7. **Critical Error:** System failure preventing task completion

**Do NOT Escalate When:**
- You can complete the task within your scope
- Standard tools and procedures apply
- Confidence level is acceptable
- No policy violations present
- Within normal operating parameters

---

## Escalation Tiers

### Tier 1: Agent-to-Agent Escalation

**When:** Task requires different agent expertise

**Process:**
1. Identify appropriate agent for task
2. Package context and requirements
3. Hand off via coordination system
4. Monitor handoff completion
5. Integrate results

**Example:**
```
BDR Concierge → Research Recon
Need: Company enrichment data
Context: Lead qualification in progress
Expected: Company profile with decision-makers
```

### Tier 2: Agent-to-Supervisor Escalation

**When:** Requires squad lead or workflow commander decision

**Process:**
1. Summarize situation and blocker
2. Present options with recommendations
3. Wait for supervisor decision
4. Execute approved course of action
5. Document decision and outcome

**Example:**
```
Support Concierge → Support Squad Lead
Issue: Edge case not covered in KB
Options: 
  A) Create temporary workaround
  B) Escalate to engineering
  C) Schedule for next product update
Recommendation: Option B (impacts multiple customers)
```

### Tier 3: Agent-to-Human Escalation

**When:** Requires human judgment, approval, or expertise

**Process:**
1. Preserve complete context
2. Document attempted solutions
3. Explain why human needed
4. Provide clear handoff information
5. Set expectations with user
6. Transfer to appropriate human

**Example:**
```
BDR Concierge → Sales Manager
Situation: Enterprise deal with complex requirements
Why Human Needed: Custom pricing, multi-year contract
Context: [Complete lead data, conversation history]
Urgency: High (competitor bidding)
Recommended Action: Executive briefing within 48 hours
```

---

## Trigger Identification

### Automatic Escalation Triggers

**Security & Compliance:**
```python
IF (contains_pii_leak OR 
    security_vulnerability_detected OR 
    gdpr_violation OR 
    regulatory_breach):
    escalate_tier = "critical"
    escalate_to = "security_team"
    notification = "immediate_alert"
```

**Business Impact:**
```python
IF (deal_value > $50000 OR 
    enterprise_customer OR 
    strategic_account OR 
    c_level_contact):
    escalate_tier = "high_priority"
    escalate_to = "senior_sales"
    notification = "within_1_hour"
```

**Confidence Threshold:**
```python
IF (confidence_score < 0.70 OR 
    multiple_retry_failures OR 
    ambiguous_requirements):
    escalate_tier = "standard"
    escalate_to = "appropriate_human"
    notification = "business_hours"
```

**Technical Errors:**
```python
IF (critical_tool_failure OR 
    data_corruption OR 
    system_unavailable):
    escalate_tier = "urgent"
    escalate_to = "ops_team"
    notification = "immediate_alert"
```

### Manual Escalation Triggers

**Use Your Judgment:**
- Situation feels "off" or concerning
- Multiple conflicting signals
- Ethical concerns about request
- Potential for significant harm
- User expressing frustration or urgency
- Request is unusual or novel

**Trust Your Instincts:**
If something doesn't feel right, escalate. Better to escalate unnecessarily than to proceed incorrectly.

---

## Context Preservation

### What to Include in Escalation

**Essential Context:**
1. **What Happened:** Clear description of situation
2. **What Was Tried:** All attempted solutions
3. **Why Escalating:** Specific trigger and reasoning
4. **Current State:** Where things stand now
5. **What's Needed:** Clear ask from human
6. **When Needed:** Urgency and deadline

### Escalation Context Template

```markdown
# ESCALATION SUMMARY

## Basic Information
- **Escalation ID:** {{escalation_id}}
- **Agent:** {{agent_type}} ({{agent_id}})
- **Timestamp:** {{timestamp}}
- **Severity:** Critical|High|Medium|Low
- **Category:** {{category}}

## Situation Description
[Clear, concise description of what's happening]

## Original Request
[User's original request or task]

## Actions Taken
1. [First action] - Result: [outcome]
2. [Second action] - Result: [outcome]
3. [Third action] - Result: [outcome]

## Why Human Intervention Needed
[Specific reason requiring escalation]
- Trigger: [What triggered escalation]
- Impact: [Who/what is affected]
- Risk: [Potential consequences]
- Confidence: [Why uncertain]

## Relevant Context
- **Customer/Contact:** {{contact_info}}
- **Account Details:** {{account_tier, ARR, status}}
- **History:** {{relevant_past_interactions}}
- **Related Items:** {{ticket_ids, deal_ids, etc}}

## Attempted Solutions
### Solution 1: {{approach}}
- **Outcome:** {{result}}
- **Why Didn't Work:** {{reason}}

### Solution 2: {{approach}}
- **Outcome:** {{result}}
- **Why Didn't Work:** {{reason}}

## Available Options
1. **Option A:** {{description}}
   - Pros: {{benefits}}
   - Cons: {{drawbacks}}
   
2. **Option B:** {{description}}
   - Pros: {{benefits}}
   - Cons: {{drawbacks}}

## Recommendation
[Your recommended course of action with reasoning]

## Urgency Assessment
- **Timeline:** {{when_decision_needed}}
- **Impact if Delayed:** {{consequences}}
- **SLA Deadline:** {{if_applicable}}

## Supporting Data
- **Correlation ID:** {{correlation_id}}
- **Logs:** {{log_references}}
- **Screenshots:** {{if_applicable}}
- **Related Docs:** {{links}}

## Next Steps if Approved
1. [Action step 1]
2. [Action step 2]
3. [Action step 3]
```

---

## Handoff Format

### Structured Handoff Data

**Machine-Readable Format:**
```json
{
  "escalation_id": "esc_abc123",
  "correlation_id": "cor_xyz789",
  "timestamp": "2025-10-31T10:15:00Z",
  "agent": {
    "type": "support-concierge",
    "id": "agent_support_001",
    "version": "1.0.0"
  },
  "severity": "high",
  "category": "technical_escalation",
  "trigger": "no_kb_match_high_priority",
  "context": {
    "ticket_id": "TICKET-12345",
    "customer": {
      "id": "cust_456",
      "name": "Acme Corp",
      "tier": "enterprise",
      "arr": 50000
    },
    "issue": {
      "summary": "API integration not syncing",
      "priority": "P2",
      "impact": "5 users unable to work"
    }
  },
  "attempts": [
    {
      "action": "kb_search",
      "query": "API sync failure",
      "result": "no_high_confidence_match",
      "confidence": 0.65
    },
    {
      "action": "troubleshooting_steps",
      "steps_completed": ["check_auth", "verify_endpoint", "test_connection"],
      "result": "issue_persists"
    }
  ],
  "recommendation": {
    "action": "escalate_to_engineering",
    "reasoning": "Likely requires log analysis and code inspection",
    "urgency": "within_4_hours",
    "assigned_to": "engineering_team"
  }
}
```

### Human-Readable Format

**Slack/Email Notification:**
```
🔴 ESCALATION REQUIRED

Agent: Support Concierge
Priority: HIGH
Customer: Acme Corp (Enterprise, $50K ARR)

Issue:
API integration stopped syncing for 5 users

What I Tried:
✗ Searched KB (no good match, confidence: 65%)
✗ Standard troubleshooting (issue persists)

Why Escalating:
Likely requires log analysis and code review

Action Needed:
Engineering team investigation within 4 hours

Details: [Link to full context]
Ticket: TICKET-12345
```

---

## Human-in-the-Loop Requirements

### Approval Gates

**Require Human Approval For:**

**Financial Decisions:**
- Discounts >10%
- Refunds >$500
- Contract modifications
- Budget exceptions

**Strategic Decisions:**
- Enterprise deals
- Partnership agreements
- Policy changes
- Major escalations

**Sensitive Operations:**
- Data deletion requests
- Access privilege changes
- Security exceptions
- Compliance waivers

### Approval Process

**Request Approval:**
```markdown
APPROVAL REQUESTED

**Request:** {{what_needs_approval}}
**Requested By:** {{agent_id}}
**Reason:** {{justification}}

**Details:**
- Customer: {{customer_name}}
- Amount/Impact: {{quantified_impact}}
- Risk Level: {{low|medium|high}}
- Urgency: {{timeline}}

**Options:**
[ ] Approve as requested
[ ] Approve with modifications: _______________
[ ] Deny - Reason: _______________
[ ] Request more information

**Approver:** _______________
**Date:** _______________
```

**Wait for Approval:**
```python
def execute_with_approval(action, context):
    # Request approval
    approval_id = request_approval(
        action=action,
        context=context,
        urgency="high"
    )
    
    # Wait for decision (with timeout)
    decision = wait_for_approval(
        approval_id=approval_id,
        timeout_seconds=3600,  # 1 hour
        poll_interval=30  # Check every 30s
    )
    
    if decision.approved:
        # Execute approved action
        result = execute_action(action, decision.modifications)
        log_approval(approval_id, result)
        return result
    else:
        # Handle denial
        log_denial(approval_id, decision.reason)
        notify_user(decision.reason)
        return None
```

### Human Feedback Integration

**After Escalation Resolution:**
```markdown
ESCALATION FEEDBACK

**Escalation ID:** {{escalation_id}}
**Resolved By:** {{human_name}}
**Resolution:** {{what_was_done}}

**Quality Check:**
- Was escalation appropriate? Yes / No
- Was context sufficient? Yes / No
- What could improve? {{feedback}}

**Learnings:**
- What agent should do next time: {{guidance}}
- Process improvements needed: {{suggestions}}
```

---

## Escalation Workflows

### Workflow 1: Standard Escalation

```
1. Identify escalation trigger
2. Stop current processing
3. Gather complete context
4. Generate escalation summary
5. Determine escalation target
6. Package handoff data
7. Notify recipient
8. Inform user of escalation
9. Track escalation status
10. Resume when resolved or await instructions
```

### Workflow 2: Emergency Escalation

```
1. Detect critical issue
2. Immediately halt operations
3. Send critical alert (Slack + Email + SMS)
4. Preserve all state and context
5. Notify on-call team
6. Do not proceed without human clearance
7. Document incident
8. Follow post-incident protocol
```

### Workflow 3: Collaborative Escalation

```
1. Identify need for collaboration
2. Engage appropriate agent/human
3. Share context bidirectionally
4. Coordinate on solution
5. Integrate contributions
6. Validate combined output
7. Document collaboration
8. Complete task jointly
```

---

## Best Practices

### DO:
✓ Escalate early when uncertain
✓ Provide complete context
✓ Explain reasoning clearly
✓ Offer recommendations
✓ Set appropriate urgency
✓ Follow up on escalations
✓ Learn from resolutions
✓ Document patterns

### DON'T:
✗ Delay escalation to avoid "failure"
✗ Provide incomplete information
✗ Escalate without trying first
✗ Exaggerate urgency
✗ Escalate to wrong person
✗ Abandon after escalating
✗ Repeat same escalations
✗ Ignore escalation feedback

---

## Escalation Metrics

**Track and Monitor:**
- Escalation frequency by agent
- Escalation reasons (categorized)
- Time to resolution
- Escalation appropriateness score
- False escalation rate
- User satisfaction post-escalation

**Quality Indicators:**
- Appropriate escalations: >90%
- Context sufficiency: >95%
- Resolution success rate: >85%
- Escalation response time: <15 min (critical), <4 hours (standard)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-31 | Initial escalation protocol |