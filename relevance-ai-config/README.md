# Relevance AI Configuration - Transform Army AI

**Version:** 1.0.0  
**Phase:** Phase 1 - Relevance-Native Deployment  
**Last Updated:** 2025-10-31

---

## Overview

This directory contains production-ready Relevance AI configuration artifacts for the Transform Army AI platform. These configurations enable rapid deployment of the 6-agent workforce using Relevance AI as the orchestration platform for Phase 1.

### What's Included

- **6 Agent Configurations** - Complete agent definitions with prompts, tools, and policies
- **5 Tool Integration Configs** - Vendor-agnostic tool definitions calling the adapter service
- **Knowledge Base Templates** - Schema and sample data for per-client knowledge bases
- **3 Multi-Agent Workflows** - Coordinated workflows for lead qualification, support triage, and ops monitoring

---

## Prerequisites

### Required Accounts & Services

1. **Relevance AI Account**
   - Sign up at [relevanceai.com](https://relevanceai.com)
   - Verify email and complete onboarding
   - Note your workspace ID and API key

2. **Adapter Service Deployed**
   - Deploy the FastAPI adapter service (see [`apps/adapter/README.md`](../apps/adapter/README.md))
   - Obtain adapter service URL (e.g., `https://adapter.yourdomain.com`)
   - Verify adapter is accessible and healthy

3. **Provider Credentials**
   - CRM: HubSpot API key OR Salesforce OAuth credentials
   - Helpdesk: Zendesk credentials OR Intercom API key
   - Calendar: Google Calendar OAuth OR Microsoft Graph credentials
   - Email: Gmail OAuth OR SendGrid API key

4. **Infrastructure**
   - PostgreSQL database for tenant configuration
   - Redis for caching (optional but recommended)
   - Slack workspace for alerts (optional)

---

## Quick Start

### 1. Clone and Prepare

```bash
# Navigate to the configuration directory
cd relevance-ai-config

# Set your environment variables
export RELEVANCE_API_KEY="your_relevance_api_key"
export ADAPTER_SERVICE_URL="https://adapter.yourdomain.com"
export TENANT_ID="client_001"
```

### 2. Deploy Adapter Service First

**IMPORTANT:** The adapter service must be running before configuring Relevance AI agents.

```bash
# Navigate to adapter directory
cd ../apps/adapter

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your provider credentials

# Run adapter service
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Verify health
curl http://localhost:8000/health
```

### 3. Import Agents to Relevance AI

**Via Relevance AI Dashboard:**

1. Log in to Relevance AI
2. Navigate to **Agents** → **Create Agent**
3. For each agent configuration file in [`agents/`](agents/):
   - Click **Import from JSON**
   - Upload the agent JSON file
   - Review configuration
   - Click **Create Agent**
4. Verify all 6 agents are created successfully

**Via Relevance AI API:**

```bash
# Script to import all agents
for agent_file in agents/*.json; do
  curl -X POST https://api.relevanceai.com/v1/agents \
    -H "Authorization: Bearer $RELEVANCE_API_KEY" \
    -H "Content-Type: application/json" \
    -d @"$agent_file"
done
```

### 4. Configure Tools

**Update Tool Endpoints:**

Before importing tools, replace placeholder values:

```bash
# Replace adapter URL in all tool configs
find tools/ -name "*.json" -type f -exec sed -i 's|{{ADAPTER_SERVICE_URL}}|https://adapter.yourdomain.com|g' {} \;

# Replace tenant ID
find tools/ -name "*.json" -type f -exec sed -i 's|{{TENANT_ID}}|client_001|g' {} \;
```

**Import Tools via Relevance AI:**

1. Navigate to **Tools** → **Custom Tools**
2. For each tool configuration in [`tools/`](tools/):
   - Click **Create Custom Tool**
   - Select **HTTP Tool**
   - Import configuration from JSON
   - Test the tool with sample data
   - Save and enable

### 5. Set Up Knowledge Base

**Create Knowledge Tables:**

1. Navigate to **Knowledge** → **Tables**
2. Click **Create Table**
3. Name: `kb_{tenant_id}_product_docs`
4. Import schema from [`knowledge/table-schema.json`](knowledge/table-schema.json)
5. Enable auto-vectorization
6. Repeat for other categories:
   - `kb_{tenant_id}_troubleshooting`
   - `kb_{tenant_id}_faq`
   - `kb_{tenant_id}_onboarding`

**Import Sample Data:**

1. Navigate to your knowledge table
2. Click **Import Data** → **JSON**
3. Upload [`knowledge/sample-data.json`](knowledge/sample-data.json)
4. Map fields to schema
5. Click **Import**
6. Wait for embedding generation (5-10 minutes)
7. Test search with query: "How to reset password"

### 6. Configure Workflows

**Import Workforce Workflows:**

1. Navigate to **Workforce** → **Create Workflow**
2. For each workflow in [`workflows/`](workflows/):
   - Click **Import from JSON**
   - Upload workflow configuration
   - Review agent sequence and variable passing
   - Configure trigger (webhook or schedule)
   - Test with sample data
   - Activate workflow

---

## Configuration Guide

### Environment Variables

Create a `.env` file with required configuration:

```bash
# Relevance AI
RELEVANCE_API_KEY=your_relevance_api_key
RELEVANCE_WORKSPACE_ID=your_workspace_id

# Adapter Service
ADAPTER_SERVICE_URL=https://adapter.yourdomain.com
ADAPTER_API_KEY=your_adapter_api_key

# Tenant Configuration
TENANT_ID=client_001
TENANT_NAME=Client Name

# Provider Credentials (stored in adapter service)
HUBSPOT_API_KEY=your_hubspot_key
ZENDESK_SUBDOMAIN=your_subdomain
ZENDESK_EMAIL=admin@yourdomain.com
ZENDESK_API_TOKEN=your_zendesk_token
GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json

# Optional: Slack Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Optional: BYO LLM
OPENAI_API_KEY=your_openai_key
```

### Per-Client Customization

Each client deployment requires:

1. **Unique Tenant ID**
   ```bash
   TENANT_ID=client_acme_001
   ```

2. **Isolated Knowledge Tables**
   ```
   kb_client_acme_001_product_docs
   kb_client_acme_001_troubleshooting
   kb_client_acme_001_faq
   ```

3. **Provider Credentials**
   - Store in adapter service database
   - Encrypt sensitive credentials
   - Associate with tenant ID

4. **Custom Agent Prompts** (Optional)
   - Modify system prompts in agent configs
   - Add client-specific policies
   - Customize email templates

### Tool Endpoint Configuration

All tools call the adapter service. Ensure adapter endpoints are configured:

**CRM Tools** → `/api/v1/crm/*`
**Helpdesk Tools** → `/api/v1/helpdesk/*`
**Calendar Tools** → `/api/v1/calendar/*`
**Email Tools** → `/api/v1/email/*`
**Knowledge Tools** → `/api/v1/knowledge/*`

**Verify Adapter Connectivity:**

```bash
# Test CRM endpoint
curl -X POST $ADAPTER_SERVICE_URL/api/v1/crm/contacts/search \
  -H "Authorization: Bearer $ADAPTER_API_KEY" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"query": "test@example.com"}'

# Should return 200 OK with search results
```

---

## Testing Procedures

### Smoke Tests for Each Agent

#### 1. BDR Concierge Smoke Test

```json
{
  "agent_id": "bdr-concierge",
  "input": {
    "lead_email": "test@example.com",
    "lead_name": "Test User",
    "company": "Test Corp",
    "message": "Interested in enterprise plan, have $50K budget approved, need by end of quarter",
    "lead_source": "website"
  }
}
```

**Expected Output:**
- Qualification score ≥ 70
- CRM contact created
- Meeting booked with sales rep
- Confirmation email sent
- Status: "qualified"

#### 2. Support Concierge Smoke Test

```json
{
  "agent_id": "support-concierge",
  "input": {
    "ticket_id": "TEST-001",
    "subject": "How do I reset my password?",
    "description": "I forgot my password and can't log in",
    "requester_email": "customer@example.com",
    "requester_name": "Customer Name"
  }
}
```

**Expected Output:**
- Priority: P2 or P3
- Category: "authentication"
- KB article found (confidence ≥ 0.80)
- Response posted to ticket
- Status: "deflected"

#### 3. Research Recon Smoke Test

```json
{
  "agent_id": "research-recon",
  "input": {
    "research_type": "company_profile",
    "company_name": "Salesforce",
    "company_domain": "salesforce.com",
    "depth": "quick"
  }
}
```

**Expected Output:**
- Company profile with overview
- Key executives identified
- Technology stack listed
- ≥5 sources cited
- Confidence: "high"

#### 4. Ops Sapper Smoke Test

```json
{
  "agent_id": "ops-sapper",
  "input": {
    "operation": "sla_check",
    "time_range": "last_1_hour"
  }
}
```

**Expected Output:**
- SLA metrics calculated
- At-risk tickets identified
- Alerts generated if needed
- Status: "healthy", "warning", or "critical"

#### 5. Knowledge Librarian Smoke Test

```json
{
  "agent_id": "knowledge-librarian",
  "input": {
    "operation": "create_article",
    "article_data": {
      "title": "Test Article",
      "content": "# Test\n\nThis is a test article.",
      "category": "getting_started",
      "tags": ["test"]
    }
  }
}
```

**Expected Output:**
- Article created
- Embeddings generated
- Article ID returned
- Status: "success"

#### 6. QA Auditor Smoke Test

```json
{
  "agent_id": "qa-auditor",
  "input": {
    "operation": "validate_output",
    "agent_id": "bdr-concierge",
    "output_data": {
      "status": "qualified",
      "qualification_score": 85,
      "reasoning": "Strong BANT across all criteria"
    }
  }
}
```

**Expected Output:**
- Quality score calculated
- Validation result: "approved"
- Rubric scores provided
- No blocking issues

### End-to-End Workflow Tests

#### Lead Qualification Workflow Test

```bash
# Trigger via webhook
curl -X POST $ADAPTER_SERVICE_URL/api/v1/workflows/lead-qualification/trigger \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@acme.com",
    "name": "John Doe",
    "company": "Acme Corp",
    "message": "Need enterprise solution for 500 users, $75K budget, urgency high",
    "source": "website",
    "title": "VP of Sales"
  }'
```

**Verify:**
1. BDR qualifies lead (Step 1)
2. Research enriches company data (Step 2)
3. BDR books meeting (Step 3)
4. QA validates quality (Step 4)
5. Total time < 15 minutes
6. Meeting confirmation sent

#### Support Triage Workflow Test

```bash
# Create test ticket in helpdesk
# Then verify workflow executes
```

**Verify:**
1. Support classifies and searches KB (Step 1)
2. Librarian checks for gaps if needed (Step 2)
3. Support responds or escalates (Step 3)
4. QA validates response quality (Step 4)
5. SLA met for priority level

### Tool Connectivity Verification

**Test Each Tool Category:**

```bash
# Test CRM connectivity
./scripts/test-crm-tools.sh

# Test Helpdesk connectivity
./scripts/test-helpdesk-tools.sh

# Test Calendar connectivity
./scripts/test-calendar-tools.sh

# Test Email connectivity
./scripts/test-email-tools.sh

# Test Knowledge connectivity
./scripts/test-knowledge-tools.sh
```

### Knowledge Base Search Validation

**Test Semantic Search:**

1. Navigate to Knowledge table
2. Test queries:
   - "how do I reset my password" → Should return password reset article
   - "can't log in" → Should return authentication articles
   - "connect my CRM" → Should return integration guide
3. Verify confidence scores ≥ 0.80 for good matches
4. Check that snippets are relevant

---

## Operational Guide

### Monitoring Agent Performance

**View Real-Time Activity:**

1. Relevance AI Dashboard → **Agents**
2. Click on agent name
3. View **Recent Executions** tab
4. Check execution status, duration, cost

**Key Metrics to Monitor:**

| Agent | Key Metric | Target | Alert If |
|-------|-----------|--------|----------|
| BDR Concierge | Qualification accuracy | ≥85% | <80% |
| Support Concierge | Deflection rate | ≥40% | <30% |
| Research Recon | Research depth | ≥8/10 | <7/10 |
| Ops Sapper | Alert accuracy | ≥95% | <90% |
| Knowledge Librarian | Freshness score | ≥90% | <85% |
| QA Auditor | Detection accuracy | ≥95% | <90% |

### Viewing Conversation Logs

**In Relevance AI:**

1. Navigate to **Agents** → [Agent Name]
2. Click **Conversations** tab
3. Filter by:
   - Date range
   - Status (success/failure)
   - Cost threshold
4. Click conversation to view:
   - Full input/output
   - Tool calls made
   - Execution trace
   - Cost breakdown

**Exporting Logs:**

```bash
# Via Relevance AI API
curl -X GET "https://api.relevanceai.com/v1/agents/{agent_id}/conversations?start_date=2025-10-01" \
  -H "Authorization: Bearer $RELEVANCE_API_KEY" \
  > agent_logs.json
```

### Debugging Failed Workflows

**When a Workflow Fails:**

1. **Identify Failed Step:**
   - Workforce → [Workflow Name] → Executions
   - Find failed execution
   - Note which step failed

2. **Review Error Details:**
   - Click on failed step
   - Review error message
   - Check input/output variables
   - Verify tool configuration

3. **Common Issues & Fixes:**

   **Adapter Connection Error:**
   - Verify adapter service is running
   - Check adapter URL in tool config
   - Verify API key is valid
   - Check network connectivity

   **Tool Authentication Error:**
   - Verify provider credentials in adapter
   - Re-authenticate OAuth connections
   - Check credential expiration
   - Verify tenant ID is correct

   **Variable Passing Error:**
   - Review variable mapping in workflow
   - Check that previous step output matches expected schema
   - Verify condition logic is correct

   **Timeout Error:**
   - Check if external API is slow
   - Increase timeout in tool config
   - Review adapter logs for delays

4. **Retry the Workflow:**
   - Fix the issue
   - Navigate to failed execution
   - Click **Retry**
   - Monitor execution

### Updating Agent Prompts

**When to Update:**
- Quality scores declining
- New features or processes added
- Customer feedback indicates confusion
- Policy changes

**How to Update:**

1. **Edit Agent Configuration:**
   - Agents → [Agent Name] → Edit
   - Modify `system_prompt` or `role_instructions`
   - Save changes

2. **Test Changes:**
   - Run smoke test with updated prompt
   - Verify output quality
   - Check QA scores

3. **Monitor Impact:**
   - Track quality metrics for 24 hours
   - Compare to baseline
   - Rollback if quality degrades

4. **Version Control:**
   - Update JSON file in this repo
   - Document changes in git commit
   - Tag version if significant change

### Managing Knowledge Base

**Adding New Articles:**

1. Navigate to **Knowledge** → Tables → `kb_{tenant_id}_category`
2. Click **Add Document**
3. Fill in required fields:
   - Title
   - Content (markdown)
   - Summary
   - Category
   - Tags (3-5)
4. Click **Save**
5. Wait for embedding generation
6. Test search to verify article is findable

**Updating Existing Articles:**

1. Find article in knowledge table
2. Click **Edit**
3. Update content
4. Update `updated_at` date
5. Save (embeddings regenerate automatically)

**Monitoring KB Health:**

- **Freshness:** Navigate to Knowledge → Analytics
- **Coverage:** Review gap analysis reports from Knowledge Librarian
- **Utilization:** Check article view counts
- **Quality:** Monitor helpfulness votes

---

## Production Deployment Checklist

Use the companion [`deployment-checklist.md`](deployment-checklist.md) for step-by-step deployment validation.

**Critical Pre-Launch Checks:**

- [ ] All 6 agents imported and active
- [ ] All tools tested and connected to adapter
- [ ] Knowledge base seeded with minimum 20 articles
- [ ] All 3 workflows configured and tested
- [ ] Provider credentials validated
- [ ] Smoke tests passed for each agent
- [ ] End-to-end workflow tests completed
- [ ] Monitoring and alerts configured
- [ ] Team trained on operational procedures
- [ ] Escalation contacts defined
- [ ] Backup and recovery procedures in place

---

## Troubleshooting Guide

### Common Issues

#### Issue: "Agent not responding"

**Symptoms:** Agent shows as active but doesn't execute

**Diagnosis:**
1. Check agent status in Relevance AI
2. Verify tool configurations
3. Check adapter service health
4. Review recent error logs

**Solutions:**
- Restart adapter service if unhealthy
- Re-import agent configuration
- Verify all required tools are enabled
- Check API rate limits not exceeded

#### Issue: "Tool authentication failed"

**Symptoms:** Tool calls return 401 or 403 errors

**Diagnosis:**
1. Check adapter service logs
2. Verify provider credentials
3. Test provider API directly

**Solutions:**
- Refresh OAuth tokens
- Re-enter API keys in adapter
- Check provider account status
- Verify scopes/permissions

#### Issue: "Knowledge base not returning results"

**Symptoms:** KB searches return empty or irrelevant results

**Diagnosis:**
1. Check if embeddings were generated
2. Verify articles are published
3. Test search with known article titles

**Solutions:**
- Regenerate embeddings for table
- Check article `published` status
- Adjust search confidence threshold
- Add more relevant tags to articles

#### Issue: "Workflow stuck or timeout"

**Symptoms:** Workflow doesn't complete

**Diagnosis:**
1. Check which step is stuck
2. Review step timeout settings
3. Check if waiting for approval

**Solutions:**
- Increase step timeout
- Verify approval gate configuration
- Check adapter service performance
- Review variable passing logic

### Getting Help

**Support Resources:**
- Documentation: [Transform Army AI Docs](https://docs.transform-army.ai)
- Adapter API Docs: [`docs/adapter-contract.md`](../docs/adapter-contract.md)
- Community: [Discord Server](#)
- Email: support@transform-army.ai

**When Contacting Support, Include:**
- Tenant ID
- Agent/workflow ID
- Timestamp of issue
- Error messages from logs
- Steps already attempted
- Relevant configuration files

---

## Migration Path: Phase 1 → Phase 2

### When to Migrate

**Trigger Points:**
- 5+ clients onboarded successfully
- Monthly run rate > $10K
- Need for advanced customization
- Desire for white-label branding
- On-premise deployment required

### Migration Overview

**Phase 2 adds:**
- Adapter layer for portability (already built!)
- PostgreSQL for tenant configuration
- Enhanced audit logging
- Advanced analytics
- Custom branding options

**What Changes:**
- Agents still in Relevance AI (no disruption)
- Tools now call adapter (seamless transition)
- Better multi-tenancy support
- Improved cost attribution

**What Stays the Same:**
- Agent prompts and logic
- Workflow definitions
- Knowledge base content
- Client-facing interfaces

### Migration Process

1. **Deploy Additional Infrastructure** (Week 1)
   - PostgreSQL database
   - Redis cache
   - Enhanced adapter service

2. **Update Tool Configurations** (Week 2)
   - Already using adapter! Just verify endpoints
   - Test connectivity
   - Enable audit logging

3. **Migrate Tenant Data** (Week 3)
   - Export configs from Relevance
   - Import to PostgreSQL
   - Dual-write during transition

4. **Validation** (Week 4)
   - Run all smoke tests
   - Verify workflows function identically
   - Check cost and performance
   - Get client approval

5. **Cutover** (Week 5)
   - Switch DNS/routing
   - Monitor closely for 48 hours
   - Keep Relevance as fallback

**No Client Disruption:**
- Agents continue working
- Same chat embeds
- Same functionality
- Better reliability

---

## Best Practices

### Security

- **Rotate API keys quarterly**
- **Use different keys for dev/staging/prod**
- **Never commit credentials to git**
- **Enable 2FA on all accounts**
- **Review access logs weekly**
- **Audit tool permissions monthly**

### Performance

- **Cache frequently used data** (calendar availability, company info)
- **Batch operations when possible**
- **Monitor token usage** and use appropriate models
- **Set reasonable timeouts** (30s for most tools, 60s for complex operations)
- **Use cost budgets** to prevent runaway spending

### Quality

- **Monitor QA scores daily**
- **Review blocked outputs immediately**
- **Track drift indicators weekly**
- **Update prompts based on feedback**
- **Maintain test coverage ≥80%**
- **Run regression tests before changes**

### Maintenance

- **Review knowledge base freshness weekly**
- **Update stale articles (>90 days)**
- **Process knowledge gaps from Support**
- **Archive unused content quarterly**
- **Update agent versions when available**
- **Test after any configuration change**

---

## Cost Management

### Expected Costs (Per Client/Month)

**Relevance AI Credits:**
- Base subscription: $299-$999/month
- Agent executions: $500-$2,000/month
- Knowledge storage: $50-$200/month
- **Total:** ~$850-$3,200/month per client

**Provider API Costs:**
- CRM API calls: ~$50/month
- Helpdesk API calls: ~$30/month
- Calendar API calls: ~$20/month
- Email sending: ~$30/month
- **Total:** ~$130/month

**LLM Costs (if using BYO key):**
- GPT-4 calls: ~$300-$800/month
- GPT-3.5 calls: ~$50-$150/month
- Embeddings: ~$20-$50/month
- **Total:** ~$370-$1,000/month

**Cost Optimization:**
- Use GPT-3.5 for simple tasks
- Cache expensive operations
- Set daily spend limits
- Monitor cost per agent
- Encourage clients to BYO LLM keys (70% savings)

---

## Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- Review agent execution logs
- Check error rates
- Monitor SLA compliance
- Respond to alerts

**Weekly:**
- Review QA reports
- Process knowledge gaps
- Update stale content
- Check cost trends

**Monthly:**
- Audit tool permissions
- Review agent performance metrics
- Update documentation
- Optimize prompts based on data

**Quarterly:**
- Rotate API keys
- Comprehensive security audit
- Performance optimization review
- Client satisfaction survey

### Escalation Contacts

**Technical Issues:**
- Adapter Service: devops@transform-army.ai
- Relevance AI: support@relevanceai.com
- Provider APIs: Contact respective support

**Operational Issues:**
- Client escalations: clientsuccess@transform-army.ai
- Quality issues: qa-team@transform-army.ai
- Billing: billing@transform-army.ai

---

## Appendix

### File Structure Reference

```
relevance-ai-config/
├── agents/                          # Agent configurations
│   ├── bdr-concierge.json          # Lead qualification agent
│   ├── support-concierge.json      # Support triage agent
│   ├── research-recon.json         # Research and intelligence
│   ├── ops-sapper.json             # Operational monitoring
│   ├── knowledge-librarian.json    # KB management
│   └── qa-auditor.json             # Quality assurance
│
├── tools/                           # Tool integrations
│   ├── crm-tools.json              # CRM operations
│   ├── helpdesk-tools.json         # Helpdesk operations
│   ├── calendar-tools.json         # Calendar operations
│   ├── email-tools.json            # Email operations
│   └── knowledge-tools.json        # Knowledge base operations
│
├── knowledge/                       # Knowledge base templates
│   ├── table-schema.json           # KB table structure
│   └── sample-data.json            # Sample articles
│
├── workflows/                       # Multi-agent workflows
│   ├── lead-qualification-workflow.json
│   ├── support-triage-workflow.json
│   └── ops-monitoring-workflow.json
│
├── README.md                        # This file
└── deployment-checklist.md         # Step-by-step deployment checklist
```

### Glossary

- **Agent:** AI entity with specific role and capabilities
- **Tool:** External capability (CRM, email, etc.) available to agents
- **Workflow:** Multi-agent coordination pattern
- **Knowledge Base:** RAG-enabled document store
- **Adapter Service:** Vendor-agnostic integration layer
- **Tenant:** Individual client with isolated configuration
- **Squad:** Group of agents working together
- **Correlation ID:** Unique identifier for request tracing

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-31 | Initial Relevance AI configuration artifacts |

---

## Next Steps

1. ✅ Review this documentation
2. ✅ Ensure adapter service is deployed
3. ✅ Gather all provider credentials
4. ✅ Follow deployment checklist step-by-step
5. ✅ Run all smoke tests
6. ✅ Test end-to-end workflows
7. ✅ Go live with first client
8. ✅ Monitor and optimize

**Questions?** Contact the Transform Army AI team at team@transform-army.ai

---

**Ready to deploy?** Start with [`deployment-checklist.md`](deployment-checklist.md) →