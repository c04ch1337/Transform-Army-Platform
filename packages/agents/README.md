# Transform Army AI - Agent Definitions

**Version:** 1.0.0  
**Last Updated:** 2025-10-31

---

## Overview

This package contains the complete agent roster for Transform Army AI, including role definitions, operating policies, and configuration for the 6 base agents. These agents form the ground forces of the AI workforce, with squad coordination coming in later phases.

---

## Agent Roster

### Ground Forces (Phase A)

| Agent | Role | Primary Function | Squad |
|-------|------|-----------------|-------|
| **BDR Concierge** | Sales | Lead qualification & meeting booking | Sales Squad |
| **Support Concierge** | Support | Ticket triage & deflection | Support Squad |
| **Research Recon** | Intelligence | Company enrichment & research | Sales Squad |
| **Ops Sapper** | Operations | SLA monitoring & reporting | Ops Squad |
| **Knowledge Librarian** | Content | KB management & gap detection | Support Squad |
| **QA Auditor** | Quality | Output validation & scoring | All Squads |

---

## Directory Structure

```
packages/agents/
├── README.md                          # This file
├── agent-configs.json                 # Agent configurations
├── roles/                             # Role definitions
│   ├── bdr-concierge.md
│   ├── support-concierge.md
│   ├── research-recon.md
│   ├── ops-sapper.md
│   ├── knowledge-librarian.md
│   └── qa-auditor.md
└── policies/                          # Operating policies
    ├── bdr-concierge-policy.md
    ├── support-concierge-policy.md
    ├── research-recon-policy.md
    ├── ops-sapper-policy.md
    ├── knowledge-librarian-policy.md
    └── qa-auditor-policy.md
```

---

## Using Role Definitions

Role definitions ([`roles/`](roles/)) provide comprehensive specifications for each agent:

**What's Included:**
- Mission statement and core responsibilities
- Available tools and permissions
- Success metrics and targets
- Escalation triggers
- Example workflows
- Integration points for each platform phase

**Use Cases:**
- Designing agent prompts for Relevance AI
- Understanding agent capabilities and limitations
- Planning workflow coordination
- Defining success criteria
- Training and onboarding new team members

**Example:**
```markdown
# From bdr-concierge.md

## Qualification Criteria (BANT Framework)
- Budget: 0-30 points
- Authority: 0-25 points
- Need: 0-30 points
- Timeline: 0-15 points
Qualification Threshold: ≥70 for meeting booking
```

---

## Using Policy Documents

Policy documents ([`policies/`](policies/)) define how agents should operate:

**What's Included:**
- Decision criteria and rules
- Compliance requirements
- Quality standards
- Error handling procedures
- Data privacy and security guidelines
- Escalation protocols

**Use Cases:**
- Implementing agent business logic
- Ensuring compliance and quality
- Defining guardrails and constraints
- Creating eval rubrics for QA
- Auditing agent behavior

**Example:**
```markdown
# From support-concierge-policy.md

## Knowledge Base Search Strategy
Stage 1: Semantic Search (confidence threshold: 0.80)
Stage 2: Keyword Enhancement
Stage 3: Category Filtering
Stage 4: Fallback Strategy

IF confidence >= 0.80: Provide solution directly
ELIF confidence >= 0.70: Verify relevance first
ELSE: Escalate to human
```

---

## Using Agent Configurations

[`agent-configs.json`](agent-configs.json) contains machine-readable configuration:

**What's Included:**
- Agent IDs and metadata
- Model selection (primary/fallback)
- Tool permissions
- Threshold values
- Cost budgets
- SLA targets
- Squad assignments

**Use Cases:**
- Programmatic agent instantiation
- Dynamic configuration management
- Cost and performance monitoring
- Access control enforcement
- Integration with orchestration systems

**Example:**
```json
{
  "agent_id": "bdr-concierge",
  "model": {
    "primary": "gpt-4",
    "temperature": 0.3,
    "max_tokens": 2000
  },
  "thresholds": {
    "qualification_score": 70,
    "confidence_min": 0.7
  },
  "cost_budget": {
    "per_operation": 0.50
  }
}
```

---

## Implementation Guide

### Phase 1: Relevance AI Native

**Setup:**
1. Create agent in Relevance AI platform
2. Copy system prompt from [`../../prompt-pack/templates/`](../../prompt-pack/templates/)
3. Configure tools from agent's role definition
4. Set up knowledge tables per agent needs
5. Test with example scenarios from role docs

**Tools Configuration:**
- Use Relevance AI native integrations for Phase 1
- Map tool names to Relevance AI actions
- Configure authentication per provider

**Example Agent Creation:**
```
Agent Name: BDR Concierge
System Prompt: [From bdr-concierge-template.md]
Tools Enabled:
  - HubSpot CRM (native Relevance integration)
  - Google Calendar (native integration)
  - Email sending (native integration)
Knowledge: Sales qualification criteria table
```

### Phase 2: Adapter Layer

**Setup:**
1. Deploy adapter service ([`../../apps/adapter/`](../../apps/adapter/))
2. Update agent tool calls to use adapter endpoints
3. Configure provider routing in adapter
4. Enable audit logging and correlation IDs

**Tool Migration:**
```
Old: Direct HubSpot API call
New: POST /v1/crm/contacts/search via adapter
Benefits: Provider abstraction, retry logic, audit trail
```

### Phase 3: LangGraph Orchestration

**Setup:**
1. Define state machines for squad workflows
2. Configure agent coordination
3. Implement approval gates
4. Enable advanced monitoring

**Squad Workflow Example:**
```python
from langgraph.graph import StateGraph

# Sales Squad workflow
workflow = StateGraph(SalesSquadState)
workflow.add_node("qualify", bdr_concierge_agent)
workflow.add_node("enrich", research_recon_agent)
workflow.add_node("validate", qa_auditor_agent)
workflow.compile()
```

---

## Agent Customization

### Adjusting Qualification Criteria

**BDR Concierge BANT Scoring:**

Edit [`policies/bdr-concierge-policy.md`](policies/bdr-concierge-policy.md):

```markdown
# Current
Budget (30 points):
- 25-30: Annual budget > $50K
- 15-24: Budget $10K-$50K
- 0-14: Budget < $10K

# Adjust for your ICP
Budget (30 points):
- 25-30: Annual budget > $100K  # Higher threshold
- 15-24: Budget $50K-$100K
- 0-14: Budget < $50K
```

### Modifying SLA Targets

**Support Concierge Response Times:**

Edit [`agent-configs.json`](agent-configs.json):

```json
{
  "agent_id": "support-concierge",
  "sla": {
    "p1_response_minutes": 15,  // Change to 10 for faster P1
    "p2_response_minutes": 120, // Change to 60 for faster P2
    "p3_response_hours": 8,
    "p4_response_hours": 24
  }
}
```

### Adding New Tools

1. **Define in role definition:**
   ```markdown
   ## Available Tools
   - `new_tool.operation` - Description and when to use
   ```

2. **Add to policy:**
   ```markdown
   ## Tool Usage
   new_tool.operation:
     When: [conditions]
     Parameters: [list]
     Error handling: [approach]
   ```

3. **Update config:**
   ```json
   {
     "tools": ["existing_tools", "new_tool.operation"],
     "permissions": {
       "new_tool": ["read", "write"]
     }
   }
   ```

---

## Squad Configuration

### Sales Squad

**Members:** BDR Concierge (lead), Research Recon, QA Auditor

**Workflow:** Lead Qualification → Company Enrichment → Validation

**Coordination:**
```
1. BDR Concierge receives inbound lead
2. Extracts initial information
3. IF needs_enrichment: Calls Research Recon
4. Research provides company profile
5. BDR applies BANT scoring with enriched data
6. QA Auditor validates output quality
7. IF qualified: Meeting booked
8. ELSE: Added to nurture
```

### Support Squad

**Members:** Support Concierge (lead), Knowledge Librarian, QA Auditor

**Workflow:** Ticket Triage → Solution Lookup → Quality Check

**Coordination:**
```
1. Support Concierge receives ticket
2. Classifies priority and category
3. Searches knowledge base via Knowledge Librarian
4. IF high_confidence: Provides solution
5. ELSE: Escalates to human
6. QA Auditor validates response quality
7. Ticket resolved or escalated
```

### Ops Squad

**Members:** Ops Sapper (lead), Knowledge Librarian

**Workflow:** Monitoring → Detection → Alerting → Reporting

**Coordination:**
```
1. Ops Sapper monitors SLAs and metrics
2. Detects at-risk items or breaches
3. Sends alerts via Slack/Email
4. IF knowledge_gap: Flags to Knowledge Librarian
5. Generates daily/weekly reports
6. Tracks remediation progress
```

---

## Quality Assurance

All agents are evaluated by QA Auditor using rubrics defined in [`policies/qa-auditor-policy.md`](policies/qa-auditor-policy.md).

**Evaluation Dimensions:**
1. **Accuracy** (0-10): Facts correct, verified
2. **Completeness** (0-10): All elements present
3. **Format** (0-10): Professional structure
4. **Tone** (0-10): Appropriate voice
5. **Compliance** (0-10): Policies followed

**Quality Gates:**
- Score ≥ 9.0: Excellent (approve)
- Score 8.0-8.9: Good (approve)
- Score 7.0-7.9: Acceptable (approve with notes)
- Score 6.0-6.9: Needs improvement (flag)
- Score < 6.0: Unacceptable (block)

---

## Monitoring and Metrics

### Agent Performance Tracking

**Key Metrics per Agent:**

```
BDR Concierge:
- Qualification accuracy: ≥85%
- Meeting booking rate: ≥60%
- Response time: <5 minutes

Support Concierge:
- Deflection rate: ≥40%
- Answer accuracy: ≥95%
- First response: <2 minutes

Research Recon:
- Research depth score: ≥8/10
- Source quality: ≥90% Tier 1/2
- Actionability: ≥85%

Ops Sapper:
- Alert accuracy: ≥95%
- False positive rate: <5%
- Report timeliness: 100%

Knowledge Librarian:
- Coverage rate: ≥85%
- Freshness score: ≥90%
- Search effectiveness: ≥85%

QA Auditor:
- Detection accuracy: ≥95%
- False positive rate: ≤5%
- Rubric adherence: 100%
```

---

## Troubleshooting

### Agent Not Performing as Expected

1. **Check Configuration:**
   - Verify model settings in [`agent-configs.json`](agent-configs.json)
   - Ensure tool permissions are correct
   - Validate threshold values

2. **Review Logs:**
   - Check correlation IDs for request tracing
   - Look for error patterns
   - Verify tool execution success

3. **Validate Prompts:**
   - Ensure system prompt matches template
   - Check for prompt drift or modifications
   - Verify context is being passed correctly

4. **Test Tools:**
   - Manually test each tool endpoint
   - Verify authentication and permissions
   - Check for API rate limits or quotas

### Quality Issues

1. **Run QA Evaluation:**
   - Use QA Auditor to score recent outputs
   - Identify which rubric dimensions are low
   - Review specific examples

2. **Check for Drift:**
   - Compare recent performance to baseline
   - Look for pattern changes
   - Verify no unauthorized prompt changes

3. **Review Policies:**
   - Ensure policies are being followed
   - Check for ambiguous guidelines
   - Update policies if needed

---

## Best Practices

### DO:
✓ Keep role definitions and policies in sync
✓ Version control all configuration changes
✓ Test agents with diverse scenarios
✓ Monitor quality metrics continuously
✓ Document customizations clearly
✓ Review and update regularly (quarterly)
✓ Share learnings across agents

### DON'T:
✗ Modify configs without testing
✗ Skip quality evaluation
✗ Ignore escalation patterns
✗ Forget to update documentation
✗ Deploy without reviewing policies
✗ Overlook cost and performance metrics
✗ Neglect security and compliance

---

## Support and Resources

**Documentation:**
- [`../../docs/agent-orchestration.md`](../../docs/agent-orchestration.md) - Multi-agent coordination
- [`../../prompt-pack/system/`](../../prompt-pack/system/) - System-level prompts
- [`../../prompt-pack/templates/`](../../prompt-pack/templates/) - Agent-specific templates

**Related Packages:**
- [`../../apps/adapter/`](../../apps/adapter/) - Integration adapter service
- [`../../packages/schema/`](../../packages/schema/) - Shared data schemas
- [`../../apps/evals/`](../../apps/evals/) - Evaluation framework

**Getting Help:**
- Review agent role definition for capabilities
- Check policy document for decision criteria
- Consult orchestration docs for workflow patterns
- Review template for prompt examples

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-31 | Initial agent roster with 6 base agents |

---

## License

Internal use only - Transform Army AI Platform