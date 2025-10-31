# Relevance AI Deployment Checklist

**Version:** 1.0.0  
**Client:** ___________________________  
**Deployment Date:** ___________________________  
**Deployed By:** ___________________________

---

## Pre-Deployment Preparation

### ☐ 1. Account Setup

- [ ] Relevance AI account created
  - Account email: ___________________________
  - Workspace ID: ___________________________
  - API key obtained and stored securely
  
- [ ] Adapter service repository cloned
  - Location: ___________________________
  - Version: ___________________________

- [ ] Environment variables documented
  - Template: `.env.example` completed
  - Credentials vault location: ___________________________

### ☐ 2. Provider Credentials Gathered

**CRM System:**
- [ ] Provider selected: ☐ HubSpot ☐ Salesforce ☐ Other: __________
- [ ] API key/OAuth credentials obtained
- [ ] Tested connectivity to CRM API
- [ ] Required scopes/permissions verified
  - HubSpot: `crm.objects.contacts.write`, `crm.objects.contacts.read`
  - Salesforce: API Enabled, OAuth scopes configured

**Helpdesk System:**
- [ ] Provider selected: ☐ Zendesk ☐ Intercom ☐ Freshdesk ☐ Other: __________
- [ ] API credentials obtained
- [ ] Tested connectivity to helpdesk API
- [ ] Agent user created for API access

**Calendar System:**
- [ ] Provider selected: ☐ Google Calendar ☐ Outlook ☐ Other: __________
- [ ] OAuth credentials configured
- [ ] Service account created (if applicable)
- [ ] Calendar sharing permissions set

**Email System:**
- [ ] Provider selected: ☐ Gmail ☐ Outlook ☐ SendGrid ☐ Other: __________
- [ ] Sending credentials configured
- [ ] From address verified (noreply@domain.com)
- [ ] SPF/DKIM/DMARC records configured

### ☐ 3. Infrastructure Prerequisites

- [ ] PostgreSQL database provisioned
  - Version: 15+
  - Connection string: ___________________________
  - Initial schema created
  
- [ ] Redis cache provisioned (optional but recommended)
  - Connection string: ___________________________
  
- [ ] Slack workspace prepared (for alerts)
  - Webhook URL: ___________________________
  - Channels created: #ops-alerts, #sales-urgent, #support-escalations

---

## Adapter Service Deployment

### ☐ 4. Deploy Adapter Service

- [ ] Server/container provisioned
  - URL: ___________________________
  - SSL certificate installed
  - Firewall rules configured

- [ ] Dependencies installed
  ```bash
  cd apps/adapter
  pip install -r requirements.txt
  ```

- [ ] Environment configured
  ```bash
  cp .env.example .env
  # Edit .env with credentials
  ```

- [ ] Provider credentials loaded
  - [ ] CRM credentials in database
  - [ ] Helpdesk credentials in database
  - [ ] Calendar credentials in database
  - [ ] Email credentials in database

- [ ] Adapter service started
  ```bash
  uvicorn src.main:app --host 0.0.0.0 --port 8000
  ```

- [ ] Health check passed
  ```bash
  curl https://adapter.yourdomain.com/health
  # Should return: {"status": "healthy"}
  ```

### ☐ 5. Test Adapter Endpoints

- [ ] CRM endpoints tested
  ```bash
  # Test contact search
  curl -X POST $ADAPTER_URL/api/v1/crm/contacts/search \
    -H "Authorization: Bearer $API_KEY" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -d '{"query": "test@example.com"}'
  ```

- [ ] Helpdesk endpoints tested
  ```bash
  # Test ticket search
  curl -X POST $ADAPTER_URL/api/v1/helpdesk/tickets/search \
    -H "Authorization: Bearer $API_KEY" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -d '{"status": ["open"]}'
  ```

- [ ] Calendar endpoints tested
  ```bash
  # Test availability check
  curl -X POST $ADAPTER_URL/api/v1/calendar/availability \
    -H "Authorization: Bearer $API_KEY" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -d '{"query": {...}}'
  ```

- [ ] Email endpoints tested
  ```bash
  # Test email send
  curl -X POST $ADAPTER_URL/api/v1/email/send \
    -H "Authorization: Bearer $API_KEY" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -d '{"email": {...}}'
  ```

- [ ] Knowledge endpoints tested
  ```bash
  # Test knowledge search
  curl -X POST $ADAPTER_URL/api/v1/knowledge/search \
    -H "Authorization: Bearer $API_KEY" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -d '{"query": {"text": "test query"}}'
  ```

---

## Relevance AI Configuration

### ☐ 6. Update Configuration Files

- [ ] Update adapter URLs in all tool configs
  ```bash
  cd relevance-ai-config
  find tools/ -name "*.json" -exec sed -i 's|{{ADAPTER_SERVICE_URL}}|https://adapter.yourdomain.com|g' {} \;
  ```

- [ ] Update tenant ID in all configs
  ```bash
  find . -name "*.json" -exec sed -i 's|{{TENANT_ID}}|client_001|g' {} \;
  ```

- [ ] Update API key placeholders
  ```bash
  find . -name "*.json" -exec sed -i 's|{{API_KEY}}|your_actual_key|g' {} \;
  ```

- [ ] Review and customize agent prompts
  - [ ] BDR Concierge: Client-specific qualification criteria
  - [ ] Support Concierge: Client-specific categories
  - [ ] Research Recon: Industry focus areas
  - [ ] Update email templates with client branding

### ☐ 7. Import Agents to Relevance AI

**For each agent:**

- [ ] **BDR Concierge**
  - [ ] Navigate to Relevance AI → Agents → Create Agent
  - [ ] Import from `agents/bdr-concierge.json`
  - [ ] Review system prompt and role instructions
  - [ ] Verify all required tools are listed
  - [ ] Save and activate agent
  - [ ] Note agent ID: ___________________________

- [ ] **Support Concierge**
  - [ ] Import from `agents/support-concierge.json`
  - [ ] Verify KB access configured
  - [ ] Save and activate
  - [ ] Note agent ID: ___________________________

- [ ] **Research Recon**
  - [ ] Import from `agents/research-recon.json`
  - [ ] Verify web search tools available
  - [ ] Save and activate
  - [ ] Note agent ID: ___________________________

- [ ] **Ops Sapper**
  - [ ] Import from `agents/ops-sapper.json`
  - [ ] Configure scheduled execution
  - [ ] Save and activate
  - [ ] Note agent ID: ___________________________

- [ ] **Knowledge Librarian**
  - [ ] Import from `agents/knowledge-librarian.json`
  - [ ] Verify KB write permissions
  - [ ] Save and activate
  - [ ] Note agent ID: ___________________________

- [ ] **QA Auditor**
  - [ ] Import from `agents/qa-auditor.json`
  - [ ] Configure sampling rates
  - [ ] Save and activate
  - [ ] Note agent ID: ___________________________

### ☐ 8. Configure Tools

**For each tool category:**

- [ ] **CRM Tools**
  - [ ] Import `tools/crm-tools.json`
  - [ ] Configure endpoint URLs
  - [ ] Test `crm_search_contacts`
  - [ ] Test `crm_create_contact`
  - [ ] Test `crm_update_contact`
  - [ ] Test `crm_add_note`
  - [ ] Test `crm_create_deal`
  - [ ] All tests passed: ☐ Yes ☐ No

- [ ] **Helpdesk Tools**
  - [ ] Import `tools/helpdesk-tools.json`
  - [ ] Configure endpoint URLs
  - [ ] Test `helpdesk_read_ticket`
  - [ ] Test `helpdesk_create_ticket`
  - [ ] Test `helpdesk_update_ticket`
  - [ ] Test `helpdesk_add_comment`
  - [ ] Test `helpdesk_search_tickets`
  - [ ] All tests passed: ☐ Yes ☐ No

- [ ] **Calendar Tools**
  - [ ] Import `tools/calendar-tools.json`
  - [ ] Configure endpoint URLs
  - [ ] Test `calendar_check_availability`
  - [ ] Test `calendar_create_event`
  - [ ] Test `calendar_update_event`
  - [ ] Test `calendar_list_events`
  - [ ] All tests passed: ☐ Yes ☐ No

- [ ] **Email Tools**
  - [ ] Import `tools/email-tools.json`
  - [ ] Configure endpoint URLs
  - [ ] Test `email_send`
  - [ ] Test `email_search`
  - [ ] Test `email_validate`
  - [ ] Verify email deliverability
  - [ ] All tests passed: ☐ Yes ☐ No

- [ ] **Knowledge Tools**
  - [ ] Import `tools/knowledge-tools.json`
  - [ ] Configure endpoint URLs
  - [ ] Test `knowledge_search`
  - [ ] Test `knowledge_create_article`
  - [ ] Test `knowledge_update_article`
  - [ ] Test `knowledge_list_articles`
  - [ ] All tests passed: ☐ Yes ☐ No

### ☐ 9. Set Up Knowledge Base

- [ ] **Create Knowledge Tables**
  - [ ] Create table: `kb_{tenant_id}_product_docs`
  - [ ] Create table: `kb_{tenant_id}_troubleshooting`
  - [ ] Create table: `kb_{tenant_id}_faq`
  - [ ] Create table: `kb_{tenant_id}_onboarding`
  - [ ] Create table: `kb_{tenant_id}_api_docs`

- [ ] **Import Schema**
  - [ ] Import schema from `knowledge/table-schema.json`
  - [ ] Verify all fields created correctly
  - [ ] Enable auto-vectorization
  - [ ] Set embedding model to `text-embedding-ada-002`

- [ ] **Load Sample Data**
  - [ ] Import articles from `knowledge/sample-data.json`
  - [ ] Verify 5 articles imported
  - [ ] Wait for embedding generation (5-10 min)
  - [ ] Test search: "how to reset password"
  - [ ] Verify results returned with confidence ≥0.80

- [ ] **Add Client-Specific Content**
  - [ ] Import client's existing documentation
  - [ ] Create product-specific articles (minimum 15 total)
  - [ ] Add FAQ content
  - [ ] Add troubleshooting guides
  - [ ] Total articles: _________ (target: ≥20)

### ☐ 10. Configure Workflows

- [ ] **Lead Qualification Workflow**
  - [ ] Import `workflows/lead-qualification-workflow.json`
  - [ ] Configure webhook trigger URL
  - [ ] Map input variables from lead source
  - [ ] Set up approval gates
  - [ ] Configure alert channels
  - [ ] Test with sample lead
  - [ ] Verify all 4 steps execute
  - [ ] Check total time < 15 minutes

- [ ] **Support Triage Workflow**
  - [ ] Import `workflows/support-triage-workflow.json`
  - [ ] Configure webhook from helpdesk
  - [ ] Set up escalation routing
  - [ ] Configure KB search threshold (0.80)
  - [ ] Test with sample ticket
  - [ ] Verify deflection or escalation works
  - [ ] Check SLA compliance

- [ ] **Ops Monitoring Workflow**
  - [ ] Import `workflows/ops-monitoring-workflow.json`
  - [ ] Configure hourly SLA check schedule
  - [ ] Configure daily data quality check schedule
  - [ ] Configure weekly digest schedule
  - [ ] Set up alert routing (Slack, email)
  - [ ] Test manual execution
  - [ ] Verify alerts are sent correctly

---

## Testing & Validation

### ☐ 11. Smoke Tests

Run each agent smoke test and record results:

- [ ] **BDR Concierge Smoke Test**
  - Input: Test lead with high BANT score
  - Expected: Score ≥70, meeting booked, CRM updated
  - Result: ☐ Pass ☐ Fail
  - Notes: ___________________________

- [ ] **Support Concierge Smoke Test**
  - Input: Ticket about password reset
  - Expected: KB match found, solution provided
  - Result: ☐ Pass ☐ Fail
  - Notes: ___________________________

- [ ] **Research Recon Smoke Test**
  - Input: Company profile request
  - Expected: Profile with ≥5 sources
  - Result: ☐ Pass ☐ Fail
  - Notes: ___________________________

- [ ] **Ops Sapper Smoke Test**
  - Input: SLA check request
  - Expected: Metrics calculated, status returned
  - Result: ☐ Pass ☐ Fail
  - Notes: ___________________________

- [ ] **Knowledge Librarian Smoke Test**
  - Input: Create test article
  - Expected: Article created with embeddings
  - Result: ☐ Pass ☐ Fail
  - Notes: ___________________________

- [ ] **QA Auditor Smoke Test**
  - Input: Validate sample output
  - Expected: Quality score calculated
  - Result: ☐ Pass ☐ Fail
  - Notes: ___________________________

### ☐ 12. End-to-End Workflow Tests

- [ ] **Lead Qualification E2E Test**
  - [ ] Trigger workflow with qualified lead
  - [ ] Verify Step 1: BDR qualification completes
  - [ ] Verify Step 2: Research enrichment runs (if score ≥50)
  - [ ] Verify Step 3: Meeting booked in calendar
  - [ ] Verify Step 4: QA validation passes
  - [ ] Check CRM for new contact
  - [ ] Check calendar for new event
  - [ ] Verify confirmation email sent
  - [ ] Total workflow time: _________ (target: <15 min)
  - [ ] Overall result: ☐ Pass ☐ Fail

- [ ] **Support Triage E2E Test**
  - [ ] Create test ticket in helpdesk
  - [ ] Verify Step 1: Ticket classified and KB searched
  - [ ] Verify Step 2: Gap flagged if needed
  - [ ] Verify Step 3: Response posted or escalated
  - [ ] Verify Step 4: QA validation (if deflected)
  - [ ] Check helpdesk for response
  - [ ] Verify SLA met for priority
  - [ ] Result: ☐ Pass ☐ Fail

- [ ] **Ops Monitoring E2E Test**
  - [ ] Trigger manual SLA check
  - [ ] Verify Step 1: Metrics calculated
  - [ ] Verify Step 2: QA validates alerts
  - [ ] Check Slack for alert (if any at-risk tickets)
  - [ ] Verify metrics are accurate
  - [ ] Result: ☐ Pass ☐ Fail

### ☐ 13. Tool Connectivity Validation

- [ ] All CRM operations successful
  - Search: ☐ Pass ☐ Fail
  - Create: ☐ Pass ☐ Fail
  - Update: ☐ Pass ☐ Fail
  - Add Note: ☐ Pass ☐ Fail

- [ ] All Helpdesk operations successful
  - Read: ☐ Pass ☐ Fail
  - Create: ☐ Pass ☐ Fail
  - Update: ☐ Pass ☐ Fail
  - Add Comment: ☐ Pass ☐ Fail

- [ ] All Calendar operations successful
  - Check Availability: ☐ Pass ☐ Fail
  - Create Event: ☐ Pass ☐ Fail
  - Update Event: ☐ Pass ☐ Fail

- [ ] All Email operations successful
  - Send: ☐ Pass ☐ Fail
  - Validate: ☐ Pass ☐ Fail

- [ ] All Knowledge operations successful
  - Search: ☐ Pass ☐ Fail
  - Create Article: ☐ Pass ☐ Fail
  - Update Article: ☐ Pass ☐ Fail

### ☐ 14. Knowledge Base Search Validation

- [ ] Test semantic search accuracy
  - Query: "reset password" → Expected: Password reset article
  - Result: ☐ Pass ☐ Fail (Confidence: _______)
  
  - Query: "connect CRM" → Expected: Integration guide
  - Result: ☐ Pass ☐ Fail (Confidence: _______)
  
  - Query: "can't login" → Expected: Authentication articles
  - Result: ☐ Pass ☐ Fail (Confidence: _______)

- [ ] Verify embedding quality
  - [ ] All articles have embeddings
  - [ ] Embeddings dimension: 1536
  - [ ] Search returns relevant results
  - [ ] Confidence scores reasonable (0.70-0.95)

---

## Client-Specific Customization

### ☐ 15. Customize for Client

- [ ] **Agent Prompts**
  - [ ] Update company name in prompts
  - [ ] Customize qualification criteria (if needed)
  - [ ] Update support categories for client's product
  - [ ] Add client-specific policies

- [ ] **Email Templates**
  - [ ] Update sender name and email
  - [ ] Customize meeting confirmation template
  - [ ] Update support response templates
  - [ ] Add client branding/logo

- [ ] **Knowledge Base**
  - [ ] Add client product documentation
  - [ ] Create client-specific FAQ
  - [ ] Add integration guides for client's stack
  - [ ] Import existing help center content

- [ ] **Workflow Triggers**
  - [ ] Configure webhook URLs for client's systems
  - [ ] Set up form submission triggers
  - [ ] Configure email forwarding rules
  - [ ] Test trigger endpoints

- [ ] **Alert Channels**
  - [ ] Configure client's Slack workspace
  - [ ] Set up email distribution lists
  - [ ] Configure PagerDuty (if applicable)
  - [ ] Test alert delivery

---

## Production Enablement

### ☐ 16. Monitoring & Alerts

- [ ] **Configure Monitoring**
  - [ ] Set up Relevance AI usage alerts
  - [ ] Configure cost alerts (daily threshold)
  - [ ] Set up SLA breach alerts
  - [ ] Configure quality score alerts
  - [ ] Set up adapter service monitoring

- [ ] **Alert Channels Verified**
  - [ ] Slack webhooks tested
  - [ ] Email delivery confirmed
  - [ ] PagerDuty integration tested (if used)
  - [ ] Alert escalation paths documented

- [ ] **Dashboards Created**
  - [ ] Agent performance dashboard
  - [ ] Workflow execution dashboard
  - [ ] Cost tracking dashboard
  - [ ] SLA compliance dashboard

### ☐ 17. Documentation & Training

- [ ] **Operational Runbooks**
  - [ ] How to handle escalations
  - [ ] How to update agent prompts
  - [ ] How to add knowledge articles
  - [ ] How to troubleshoot common issues
  - [ ] Emergency contact list

- [ ] **Team Training Completed**
  - [ ] Operations team trained on monitoring
  - [ ] Support team trained on escalation handling
  - [ ] Sales team trained on lead routing
  - [ ] Stakeholders trained on analytics

- [ ] **Documentation Shared**
  - [ ] README.md shared with team
  - [ ] Deployment guide accessible
  - [ ] Troubleshooting guide distributed
  - [ ] Contact list published

### ☐ 18. Security & Compliance

- [ ] **Security Checklist**
  - [ ] API keys stored in secrets manager
  - [ ] TLS enabled for all endpoints
  - [ ] Audit logging enabled
  - [ ] Access controls configured (RBAC)
  - [ ] Data encryption verified
  - [ ] PII handling compliant with GDPR/CCPA

- [ ] **Compliance Verified**
  - [ ] Data retention policies configured
  - [ ] Audit trail functioning
  - [ ] Privacy policy updated
  - [ ] Terms of service accepted
  - [ ] Data processing agreement signed

### ☐ 19. Backup & Recovery

- [ ] **Backup Procedures**
  - [ ] Knowledge base export tested
  - [ ] Agent configurations backed up
  - [ ] Workflow definitions backed up
  - [ ] Provider credentials documented (securely)
  - [ ] Recovery procedures documented

- [ ] **Disaster Recovery Plan**
  - [ ] RTO defined: _________ hours
  - [ ] RPO defined: _________ minutes
  - [ ] Failover procedures documented
  - [ ] Recovery tested successfully
  - [ ] Team trained on recovery process

---

## Go-Live

### ☐ 20. Pre-Launch Final Checks

- [ ] **All Systems Go**
  - [ ] Adapter service healthy and accessible
  - [ ] All 6 agents active in Relevance AI
  - [ ] All tools configured and tested
  - [ ] Knowledge base populated (≥20 articles)
  - [ ] All 3 workflows active
  - [ ] Monitoring and alerts operational
  - [ ] Team trained and ready
  - [ ] Escalation contacts confirmed

- [ ] **Performance Baseline**
  - Average response time: _________ seconds
  - Agent availability: _________ %
  - Tool success rate: _________ %
  - Knowledge search accuracy: _________ %

### ☐ 21. Soft Launch (Internal Testing)

- [ ] **Week 1: Internal Testing**
  - [ ] Test with internal team members
  - [ ] Process 10+ test leads
  - [ ] Process 20+ test support tickets
  - [ ] Monitor performance closely
  - [ ] Address any issues found
  - [ ] Document lessons learned

- [ ] **Week 1 Results**
  - Issues found: _________
  - Issues resolved: _________
  - Performance: ☐ Meets expectations ☐ Needs improvement
  - Ready for production: ☐ Yes ☐ No

### ☐ 22. Production Launch

- [ ] **Enable Production Traffic**
  - [ ] Update DNS/routing to production
  - [ ] Enable webhooks from production systems
  - [ ] Activate chat embeds on client site
  - [ ] Start scheduled workflows
  - [ ] Enable production monitoring

- [ ] **First 24 Hours Monitoring**
  - Hour 1: Status check ☐ Healthy ☐ Issues: _________
  - Hour 4: Status check ☐ Healthy ☐ Issues: _________
  - Hour 12: Status check ☐ Healthy ☐ Issues: _________
  - Hour 24: Status check ☐ Healthy ☐ Issues: _________

- [ ] **First Week Validation**
  - Day 1: ☐ No critical issues
  - Day 3: ☐ Performance stable
  - Day 7: ☐ Client satisfied
  - Issues encountered: _________
  - Issues resolved: _________

---

## Post-Launch

### ☐ 23. Optimization

- [ ] **Week 2-4: Optimization Phase**
  - [ ] Review agent performance metrics
  - [ ] Analyze quality scores
  - [ ] Optimize prompts based on data
  - [ ] Adjust KB search thresholds
  - [ ] Fine-tune workflow timings
  - [ ] Update documentation with learnings

- [ ] **Cost Optimization**
  - [ ] Review cost per operation
  - [ ] Identify expensive operations
  - [ ] Implement caching where appropriate
  - [ ] Consider GPT-3.5 for simple tasks
  - [ ] Enable BYO LLM key if beneficial

### ☐ 24. Client Handoff

- [ ] **Documentation Package**
  - [ ] README with setup details
  - [ ] Operational runbooks
  - [ ] Troubleshooting guides
  - [ ] Contact list
  - [ ] SLA definitions

- [ ] **Training Completed**
  - [ ] Operators trained
  - [ ] Stakeholders briefed
  - [ ] Support team enabled
  - [ ] Q&A session held

- [ ] **Handoff Meeting**
  - [ ] Review architecture
  - [ ] Demo agent capabilities
  - [ ] Show monitoring dashboards
  - [ ] Answer questions
  - [ ] Confirm satisfaction

### ☐ 25. Ongoing Support Plan

- [ ] **Support Contacts Established**
  - Technical support: ___________________________
  - Account manager: ___________________________
  - Escalation contact: ___________________________
  - Emergency hotline: ___________________________

- [ ] **Maintenance Schedule**
  - [ ] Daily: Monitor dashboards
  - [ ] Weekly: Review metrics and reports
  - [ ] Monthly: Optimization review
  - [ ] Quarterly: Security audit

- [ ] **Success Metrics Defined**
  - Lead qualification accuracy: Target _____%, Actual _____%
  - Support deflection rate: Target _____%, Actual _____%
  - SLA compliance: Target _____%, Actual _____%
  - Customer satisfaction: Target _____%, Actual _____%
  - Cost per operation: Target $_____, Actual $_____

---

## Sign-Off

### Deployment Team

- [ ] **Technical Lead**
  - Name: ___________________________
  - Signature: ___________________________
  - Date: ___________________________

- [ ] **Operations Manager**
  - Name: ___________________________
  - Signature: ___________________________
  - Date: ___________________________

- [ ] **Client Stakeholder**
  - Name: ___________________________
  - Signature: ___________________________
  - Date: ___________________________

### Deployment Status

**Final Status:** ☐ Successful ☐ Partial ☐ Failed

**Notes:**
```
_____________________________________________________________

_____________________________________________________________

_____________________________________________________________
```

**Known Issues:**
```
_____________________________________________________________

_____________________________________________________________

_____________________________________________________________
```

**Next Steps:**
```
_____________________________________________________________

_____________________________________________________________

_____________________________________________________________
```

---

## Rollback Procedure

**If deployment fails or critical issues arise:**

1. **Immediate Actions:**
   - [ ] Disable affected agents in Relevance AI
   - [ ] Disable webhook triggers
   - [ ] Revert to manual processes
   - [ ] Notify stakeholders

2. **Preserve Data:**
   - [ ] Export conversation logs
   - [ ] Export audit trail
   - [ ] Backup current configurations
   - [ ] Document failure details

3. **Root Cause Analysis:**
   - [ ] Identify failure point
   - [ ] Document reproduction steps
   - [ ] Analyze logs and errors
   - [ ] Create fix plan

4. **Recovery:**
   - [ ] Fix identified issues
   - [ ] Retest in staging environment
   - [ ] Schedule re-deployment
   - [ ] Update checklist with learnings

---

## References

- **Architecture:** [`ARCHITECTURE.md`](../ARCHITECTURE.md)
- **Agent Definitions:** [`packages/agents/`](../packages/agents/)
- **Adapter Contract:** [`docs/adapter-contract.md`](../docs/adapter-contract.md)
- **Deployment Guide:** [`docs/deployment-guide.md`](../docs/deployment-guide.md)
- **Relevance AI Docs:** [relevanceai.com/docs](https://relevanceai.com/docs)

---

## Support

**Issues During Deployment:**
- Email: support@transform-army.ai
- Slack: #transform-army-support
- Emergency: +1-555-TRANSFORM

**Post-Deployment Support:**
- Account Manager: clientsuccess@transform-army.ai
- Technical Support: devops@transform-army.ai
- Billing Questions: billing@transform-army.ai

---

**Deployment Date:** _______________  
**Go-Live Date:** _______________  
**Next Review Date:** _______________