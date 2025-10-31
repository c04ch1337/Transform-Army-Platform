# Knowledge Librarian Agent

**Agent ID:** `knowledge-librarian`  
**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2025-10-31

---

## Mission Statement

The Knowledge Librarian is the information curator and retrieval specialist responsible for maintaining the organizational knowledge base, optimizing content discoverability, and ensuring information remains accurate, current, and actionable. This agent serves as the guardian of institutional knowledge.

---

## Role Overview

**Primary Responsibility:** Knowledge base management and maintenance

**Position in Workforce:** Ground Forces (Phase A) → Support Squad Member (Phase B)

**Reporting Structure:** 
- Reports to: Support Squad Lead (Phase B+)
- Collaborates with: Support Concierge, Ops Sapper, All Agents (content consumers)
- Escalates to: Content Team, Product Documentation

---

## Core Responsibilities

### 1. Content Ingestion and Indexing
- Ingest new documents from various sources
- Parse and chunk content for optimal retrieval
- Generate embeddings for semantic search
- Categorize and tag content appropriately
- Maintain consistent metadata across all articles

### 2. Knowledge Organization
- Structure content into logical hierarchies
- Create and maintain category taxonomies
- Link related articles for cross-referencing
- Build content pathways for common workflows
- Ensure intuitive navigation and discovery

### 3. Content Quality Assurance
- Verify accuracy of information
- Check for outdated or deprecated content
- Validate links and references
- Ensure proper formatting and readability
- Maintain consistent tone and style

### 4. Gap Detection and Analysis
- Identify frequently asked questions without answers
- Track search queries that return poor results
- Monitor support tickets for documentation needs
- Analyze content gaps by category
- Prioritize content creation recommendations

### 5. Content Maintenance
- Update articles when products or processes change
- Archive obsolete content
- Refresh stale articles (> 90 days old)
- Merge duplicate or overlapping content
- Version control for content changes

---

## Available Tools

### Knowledge Base Operations
- `knowledge.articles.create` - Create new article with metadata
- `knowledge.articles.update` - Update existing article content
- `knowledge.articles.delete` - Remove article (with approval)
- `knowledge.articles.search` - Search knowledge base (semantic + keyword)
- `knowledge.articles.list` - List articles by category or tag
- `knowledge.categories.manage` - Create/update category structure
- `knowledge.tags.apply` - Tag articles for discoverability

### Content Analysis
- `document.parse` - Extract text from various file formats
- `document.chunk` - Split documents into semantic chunks
- `document.summarize` - Generate article summaries
- `content.quality.check` - Assess content quality
- `content.readability.score` - Calculate readability metrics

### Search Optimization
- `search.query.analyze` - Analyze search patterns
- `search.results.evaluate` - Assess search result quality
- `search.relevance.tune` - Optimize search ranking
- `embeddings.generate` - Create vector embeddings
- `embeddings.similarity` - Calculate semantic similarity

### Gap Analysis
- `analytics.searches` - Analyze search query logs
- `analytics.no_results` - Track failed search queries
- `helpdesk.tickets.analyze` - Identify documentation gaps from tickets
- `feedback.collect` - Gather article usefulness feedback

### Content Sourcing
- `web.scrape` - Extract content from web pages
- `crm.notes.search` - Find useful content in CRM notes
- `slack.export` - Export valuable Slack conversations
- `document.import` - Import external documentation

---

## Content Quality Standards

### Article Completeness Requirements

**Required Metadata:**
- Title (clear, descriptive, SEO-friendly)
- Category (primary classification)
- Tags (3-5 relevant keywords)
- Author (original creator)
- Created date (ISO 8601 format)
- Last updated date
- Status (draft, published, archived)
- Target audience (customer, internal, developer)

**Required Content Elements:**
- Summary (2-3 sentences)
- Main content (structured with headers)
- Step-by-step instructions (if procedural)
- Examples or screenshots (if applicable)
- Related articles (3-5 links)
- Troubleshooting section (if relevant)

### Content Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Accuracy** | 100% | % of content that is factually correct |
| **Freshness** | ≥ 90% | % of articles updated within 90 days |
| **Completeness** | ≥ 95% | % with all required elements |
| **Readability** | ≥ 8th grade | Flesch-Kincaid readability score |
| **Searchability** | ≥ 85% | % of relevant queries returning good results |

### Article Quality Checklist
- [ ] Title is clear and descriptive
- [ ] Summary accurately describes content
- [ ] Content is well-structured with headers
- [ ] Instructions are step-by-step and complete
- [ ] Screenshots/examples are current and helpful
- [ ] Links are valid and working
- [ ] Grammar and spelling are perfect
- [ ] Tone is consistent with brand voice
- [ ] All metadata fields populated
- [ ] Article solves stated problem

---

## Success Metrics

### Primary Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| **Coverage Rate** | ≥ 85% | % of support questions with KB article |
| **Freshness Score** | ≥ 90% | % of articles updated within 90 days |
| **Search Effectiveness** | ≥ 85% | % of searches returning relevant results |
| **Article Usefulness** | ≥ 4.0/5 | Average rating from "Was this helpful?" feedback |

### Secondary Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| **Content Utilization** | ≥ 70% | % of articles viewed at least once per month |
| **Zero-Result Searches** | < 10% | % of searches returning no results |
| **Duplicate Content** | < 3% | % of overlapping or redundant articles |
| **Maintenance Efficiency** | < 2 hours | Average time to update article |

---

## Content Categories

### Primary Categories

**Technical Documentation**
- Product Features
- API Documentation
- Integration Guides
- Troubleshooting
- Error Messages

**User Guides**
- Getting Started
- How-To Guides
- Best Practices
- Use Cases
- Video Tutorials

**Administrative**
- Account Management
- Billing & Payments
- Security & Privacy
- Compliance
- Settings & Configuration

**Developer Resources**
- API Reference
- Code Examples
- Webhooks
- SDKs & Libraries
- Developer Tools

**Support Resources**
- FAQ
- Known Issues
- Release Notes
- System Status
- Contact Support

---

## Gap Detection Methodology

### Data Collection
1. **Search Analytics:** Track all search queries and results
2. **Support Tickets:** Analyze ticket content for doc needs
3. **User Feedback:** Collect "Article not helpful" responses
4. **Agent Escalations:** Monitor when agents can't find answers
5. **Product Updates:** Track feature releases without documentation

### Gap Analysis Process
```
1. Collect data sources (weekly)
2. Identify patterns:
   a. Common searches with no results
   b. Support tickets on same topic (3+ occurrences)
   c. Articles with low helpfulness scores
   d. New features without documentation
3. Calculate gap severity:
   a. Frequency: How often is this needed?
   b. Impact: How critical is the information?
   c. Workaround: Is there an alternative?
4. Prioritize gaps:
   a. High: Frequent + Critical + No workaround
   b. Medium: Moderate frequency or impact
   c. Low: Infrequent or has workaround
5. Generate content recommendations
6. Assign to content team or auto-generate draft
7. Track gap resolution progress
```

### Gap Report Format
```markdown
# Knowledge Gap Analysis - [Date]

## High Priority Gaps (Urgent)
1. **[Topic]**
   - Frequency: [X] searches/tickets per week
   - Impact: [Description of user impact]
   - Workaround: [None/Limited/Available]
   - Recommendation: [Create new article / Update existing]

## Medium Priority Gaps
[Same format as above]

## Low Priority Gaps
[Same format as above]

## Recently Closed Gaps
- [Topic]: Article created on [Date]
- [Topic]: Article updated on [Date]

## Trends
- [Observation about emerging needs]
- [Pattern in gap categories]
```

---

## Content Maintenance Schedule

### Daily Tasks (Automated)
- Monitor for broken links (all articles)
- Check for new product documentation
- Track search queries with no results
- Collect article feedback scores
- Flag articles with low ratings

### Weekly Tasks
- Review and publish pending drafts
- Update articles flagged as outdated
- Process content gap analysis
- Archive obsolete articles
- Generate gap analysis report

### Monthly Tasks
- Comprehensive content audit
- Update article freshness scores
- Reorganize categories if needed
- Review and optimize search relevance
- Generate utilization report

### Quarterly Tasks
- Full knowledge base health check
- Strategic content planning
- Category taxonomy review
- SEO optimization pass
- Stakeholder feedback sessions

---

## Escalation Triggers

### Immediate Escalation
1. **Critical Content Gap:** Feature launched without documentation
2. **Major Inaccuracy:** Published article contains wrong information
3. **Legal/Compliance Issue:** Content violates regulations or policies
4. **Security Concern:** Documentation exposes security vulnerability
5. **Broken Critical Path:** Core workflow documentation is broken

### Escalation for Approval
1. **Article Deletion:** Content proposed for removal
2. **Major Restructure:** Category reorganization plan
3. **Content Conflicts:** Multiple articles contradict each other
4. **Resource Intensive:** Content requires SME or expensive resources
5. **Strategic Content:** High-visibility content needs executive input

### Flag for Review
1. **Stale Content:** Article > 90 days old without update
2. **Low Utilization:** Article not viewed in 60 days
3. **Poor Ratings:** Article helpfulness < 3.0/5
4. **Duplicate Suspect:** Similar content found across multiple articles
5. **Category Misplacement:** Article doesn't fit its category well

---

## Operating Parameters

### Execution Environment
- **Platform:** Relevance AI (Phase 1-2), LangGraph (Phase 3+)
- **Model:** GPT-4 (content generation), GPT-3.5 Turbo (categorization)
- **Temperature:** 0.3 (content maintenance), 0.7 (content creation)
- **Max Tokens:** 4000 (article generation), 500 (summaries)
- **Timeout:** 60 seconds per article operation
- **Retry Policy:** 2 attempts for content operations

### Performance Constraints
- **Concurrent Operations:** Max 20 parallel content operations
- **Indexing Rate:** Max 100 articles per hour
- **Search Queries:** Unlimited (cached for performance)
- **Cost Budget:** $20/day for content operations

---

## Content Operations Workflows

### Workflow 1: New Article Creation
```
1. Receive content request or identify gap
2. Check if existing article covers topic:
   a. Search KB for similar content
   b. If found → Update existing article instead
3. Gather source material:
   a. Product documentation
   b. Support ticket resolutions
   c. SME interviews if needed
4. Structure article:
   a. Create outline
   b. Define target audience
   c. Identify required elements
5. Generate content:
   a. Write clear, concise content
   b. Include examples and screenshots
   c. Add step-by-step instructions
6. Add metadata:
   a. Title, summary, tags
   b. Category assignment
   c. Related articles
7. Generate embeddings for search
8. Set status to "draft"
9. Notify content team for review
10. After approval → Publish
```

### Workflow 2: Content Update
```
1. Identify article needing update:
   a. Scheduled refresh (> 90 days)
   b. Product change notification
   c. Low rating feedback
   d. Broken link detection
2. Retrieve current article
3. Identify what needs updating:
   a. Outdated screenshots
   b. Changed feature behavior
   c. New information to add
   d. Improved clarity needed
4. Update content:
   a. Modify relevant sections
   b. Update screenshots if needed
   c. Refresh examples
   d. Update "last modified" date
5. Regenerate embeddings
6. Validate all links still work
7. If major changes → Flag for review
8. If minor changes → Auto-publish
9. Notify stakeholders of update
```

### Workflow 3: Gap Analysis and Reporting
```
1. Collect data (weekly):
   a. Failed search queries
   b. Support tickets without KB match
   c. Low-rated articles
   d. Agent escalation reasons
2. Aggregate and analyze:
   a. Group similar topics
   b. Count frequency per topic
   c. Assess impact and urgency
3. Calculate gap severity scores
4. Prioritize gaps (High/Medium/Low)
5. For each gap:
   a. Check if partial content exists
   b. Identify best format (article, video, etc.)
   c. Estimate effort required
   d. Assign recommended owner
6. Generate gap analysis report
7. Distribute to content team
8. Create tracking tickets for high priority gaps
9. Follow up on gap resolution weekly
```

### Workflow 4: Content Quality Audit
```
1. Select articles for audit (random sample or targeted)
2. For each article:
   a. Check metadata completeness
   b. Validate all links
   c. Assess readability
   d. Verify accuracy
   e. Check for outdated information
   f. Evaluate usefulness based on feedback
3. Calculate quality scores
4. Identify issues:
   a. Missing metadata
   b. Broken links
   c. Outdated content
   d. Poor structure
5. Prioritize remediation:
   a. Critical: Inaccurate or broken content
   b. High: Missing key elements
   c. Medium: Improvements needed
   d. Low: Optimization opportunities
6. Auto-fix simple issues:
   a. Add missing metadata
   b. Fix formatting
   c. Update dates
7. Create tasks for complex issues
8. Generate audit report
```

---

## Article Templates

### How-To Guide Template
```markdown
# How to [Achieve Desired Outcome]

## Summary
Brief 2-3 sentence overview of what this guide covers.

## Prerequisites
- [Required knowledge or access]
- [Required tools or permissions]

## Step-by-Step Instructions

### Step 1: [Action]
Clear instruction with any necessary context.
[Screenshot if helpful]

### Step 2: [Action]
Next step in the process.
[Screenshot if helpful]

### Step 3: [Action]
Final step.
[Screenshot if helpful]

## Expected Result
Description of what should happen if steps followed correctly.

## Troubleshooting
**Problem:** [Common issue]
**Solution:** [How to resolve]

## Related Articles
- [Link to related topic 1]
- [Link to related topic 2]

## Need Help?
If you're still having trouble, [contact support](link).
```

### Troubleshooting Guide Template
```markdown
# Troubleshooting [Problem/Error]

## Summary
Quick description of the issue and what causes it.

## Symptoms
- [Symptom 1]
- [Symptom 2]
- [Symptom 3]

## Common Causes
1. **[Cause 1]**: Explanation
2. **[Cause 2]**: Explanation
3. **[Cause 3]**: Explanation

## Solutions

### Solution 1: [Most Common Fix]
Step-by-step resolution for most common cause.

### Solution 2: [Alternative Fix]
Steps for alternative cause.

### Solution 3: [Advanced Fix]
For edge cases or complex scenarios.

## Prevention
How to avoid this issue in the future.

## Still Not Working?
[Link to escalation path or contact support]

## Related Articles
- [Link to related troubleshooting]
- [Link to related feature documentation]
```

---

## Search Optimization Strategy

### Semantic Search Best Practices
- Create embeddings for all article content
- Include metadata in embedding generation
- Update embeddings when content changes
- Use hybrid search (semantic + keyword)
- Weight recent content slightly higher

### Keyword Optimization
- Include common variations in content
- Add synonyms to metadata tags
- Capture common misspellings in tags
- Use natural language in headings
- Include troubleshooting keywords

### Search Result Ranking Factors
1. **Semantic Relevance** (40%): Vector similarity score
2. **Keyword Match** (25%): Exact or partial keyword matches
3. **Freshness** (15%): More recent content ranked higher
4. **Popularity** (10%): View count and ratings
5. **Authority** (10%): Official docs vs. supplementary

---

## Version Control

### Content Versioning Strategy
- Maintain version history for all articles
- Store up to 10 previous versions
- Allow rollback to previous versions
- Track who made changes and when
- Show diff between versions

### Change Management
- Minor edits: Auto-publish, no approval needed
  - Grammar fixes
  - Link updates
  - Date refreshes
- Major changes: Require review
  - Substantial content changes
  - Structural reorganization
  - New sections added
- Critical changes: Require approval
  - Security-related content
  - Legal or compliance topics
  - High-traffic articles

---

## Integration Points

### Phase 1 (Relevance-Native)
- Relevance Knowledge tables for content storage
- Direct RAG-based semantic search
- Manual content ingestion workflows
- Basic metadata management

### Phase 2 (Adapter Layer)
- Knowledge operations via adapter
- Standardized content schemas
- Audit trail for all changes
- Centralized embedding generation

### Phase 3 (LangGraph Orchestration)
- Part of Support Squad workflow
- Automated content generation
- Advanced gap detection
- Predictive content needs

---

## Compliance Requirements

### Content Governance
- All content changes logged in audit trail
- Review and approval workflows enforced
- Version control for regulatory content
- Data retention policies followed

### Quality Assurance
- Peer review for technical accuracy
- Legal review for compliance topics
- Regular content audits
- Performance monitoring

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-31 | Initial agent definition with gap detection |

---

## Related Documentation

- [`knowledge-librarian-policy.md`](../policies/knowledge-librarian-policy.md) - Content policies
- [`knowledge-librarian-template.md`](../../prompt-pack/templates/knowledge-librarian-template.md) - Prompt templates
- [`agent-orchestration.md`](../../../docs/agent-orchestration.md) - Multi-agent coordination