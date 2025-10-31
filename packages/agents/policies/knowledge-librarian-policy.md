# Knowledge Librarian Agent - Operating Policies

**Agent ID:** `knowledge-librarian`  
**Version:** 1.0.0  
**Last Updated:** 2025-10-31

---

## Policy Overview

This document defines content quality standards, indexing procedures, update frequency guidelines, version control practices, and access control rules for the Knowledge Librarian Agent.

---

## 1. Document Indexing Standards

### 1.1 Content Ingestion Process

**Pre-Ingestion Checklist:**
- [ ] Source is authorized (approved content owner)
- [ ] Content is appropriate for knowledge base
- [ ] No confidential or proprietary information (unless internal KB)
- [ ] Copyright/licensing allows inclusion
- [ ] Content format is supported
- [ ] Duplicates checked and resolved

**Ingestion Workflow:**
```
1. Receive content (document, URL, text)
2. Validate source authorization
3. Extract text and metadata
4. Check for duplicate content (90% similarity threshold)
5. IF duplicate → Update existing article
6. IF new → Proceed with indexing
7. Parse and chunk content appropriately
8. Generate embeddings for semantic search
9. Assign category and tags
10. Set status to "draft" for review
11. Notify content team for approval
```

### 1.2 Content Chunking Strategy

**Chunk Size Guidelines:**
- Target: 500-1000 tokens per chunk
- Minimum: 200 tokens (avoid too small)
- Maximum: 2000 tokens (avoid too large)
- Preserve paragraph boundaries
- Keep code blocks intact
- Maintain list structure

**Chunking Rules:**
```
IF content_type == "technical_doc":
    chunk_by = "heading"  # Split on H2/H3 headers
ELIF content_type == "how_to_guide":
    chunk_by = "step"  # Split on numbered steps
ELIF content_type == "reference":
    chunk_by = "section"  # Logical sections
ELSE:
    chunk_by = "paragraph"  # Default paragraphs
```

### 1.3 Metadata Requirements

**Required Metadata Fields:**
```json
{
  "title": "Clear, descriptive title (required)",
  "summary": "2-3 sentence summary (required)",
  "category": "Primary category (required)",
  "tags": ["tag1", "tag2", "tag3"],  // 3-5 tags (required)
  "author": "Content creator (required)",
  "created_date": "2025-10-31T00:00:00Z (required)",
  "updated_date": "2025-10-31T00:00:00Z (required)",
  "status": "draft|published|archived (required)",
  "audience": "customer|internal|developer (required)",
  "version": "1.0.0 (required)"
}
```

**Optional Metadata:**
```json
{
  "product_version": "Applicable product version",
  "related_articles": ["article_id_1", "article_id_2"],
  "prerequisites": ["Required knowledge"],
  "difficulty": "beginner|intermediate|advanced",
  "estimated_time": "5 minutes",
  "video_url": "Tutorial video URL",
  "last_reviewed_date": "2025-10-31"
}
```

---

## 2. Content Quality Criteria

### 2.1 Accuracy Standards

**Fact Verification:**
- All technical information verified against product documentation
- Code examples tested and confirmed working
- Screenshots match current UI version
- Links verified as functional
- Statistics and data points sourced

**Review Process:**
```
IF content_type == "technical" OR "security":
    require_sme_review = True
    require_technical_test = True
ELIF content_type == "process" OR "policy":
    require_manager_approval = True
ELSE:
    require_peer_review = True
```

### 2.2 Completeness Requirements

**Article Must Include:**
- Clear, descriptive title
- Concise summary (2-3 sentences)
- Main content organized with headers
- Step-by-step instructions (if procedural)
- Examples or screenshots (if applicable)
- Troubleshooting section (if relevant)
- Related articles (3-5 links minimum)
- "Was this helpful?" feedback mechanism

**Missing Element Policy:**
```
IF critical_element_missing:
    block_publication
    return_to_author_with_feedback
ELIF optional_element_missing:
    flag_for_enhancement
    allow_publication_with_note
```

### 2.3 Readability Standards

**Target Readability:**
- Reading level: 8th grade (Flesch-Kincaid)
- Sentence length: Average <20 words
- Paragraph length: 2-4 sentences
- Active voice: ≥80% of sentences
- Jargon: Defined on first use

**Readability Tools:**
- Automated: Flesch-Kincaid scoring
- Manual: Peer readability review
- Test: User comprehension testing

**Readability Thresholds:**
```
score = flesch_kincaid_grade_level(content)

IF score <= 8:
    readability = "excellent"
ELIF score <= 10:
    readability = "good"
ELIF score <= 12:
    readability = "acceptable"
ELSE:
    readability = "needs_simplification"
    flag_for_rewrite = True
```

---

## 3. Update Frequency Guidelines

### 3.1 Scheduled Reviews

**Review Cadence by Content Type:**

**Critical Content (Monthly Review):**
- Security procedures
- Compliance documentation
- API authentication guides
- Data privacy policies
- Integration setup guides

**High-Priority Content (Quarterly Review):**
- Core feature documentation
- Getting started guides
- FAQ articles
- Troubleshooting guides
- Best practices

**Standard Content (Semi-Annual Review):**
- Advanced feature docs
- Use case examples
- Product comparisons
- Historical release notes

**Archived Content (Annual Review):**
- Deprecated features
- Legacy documentation
- Historical references

### 3.2 Trigger-Based Updates

**Immediate Update Required:**
- Product feature changes
- Security vulnerability patched
- Process/policy changes
- Regulatory requirement changes
- Critical error in content reported

**Update Within 48 Hours:**
- UI changes in screenshots
- Feature enhancements
- Known issues resolved
- New FAQ items identified
- Broken links detected

**Update Within 7 Days:**
- Minor improvements suggested
- Additional examples requested
- Related articles added
- Formatting enhancements
- SEO optimization

### 3.3 Freshness Scoring

**Freshness Calculation:**
```
days_since_update = current_date - last_updated_date
priority_weight = content_priority_level  // 1-5

freshness_score = 100 - (days_since_update * priority_weight / 30)

Interpretation:
90-100: Fresh (excellent)
75-89:  Current (good)
60-74:  Aging (needs attention)
<60:    Stale (urgent update needed)
```

**Auto-Flagging:**
```
IF freshness_score < 60:
    create_update_task
    assign_to_content_owner
    notify_content_team
    add_banner_to_article("This article may be outdated")
```

---

## 4. Version Control Practices

### 4.1 Versioning Strategy

**Version Number Format: MAJOR.MINOR.PATCH**

**Version Increments:**
- **MAJOR (X.0.0):** Complete rewrite, structural changes, deprecated features
- **MINOR (1.X.0):** New sections added, significant updates, scope expansion
- **PATCH (1.0.X):** Corrections, clarifications, minor updates, formatting fixes

**Version Examples:**
```
1.0.0 → Initial publication
1.0.1 → Fixed typo, updated screenshot
1.1.0 → Added new troubleshooting section
2.0.0 → Complete rewrite for new product version
```

### 4.2 Change Tracking

**Required Change Documentation:**
```json
{
  "version": "1.2.3",
  "date": "2025-10-31",
  "author": "knowledge_librarian",
  "change_type": "minor|major|patch",
  "description": "Added section on new integration method",
  "sections_modified": ["Integration Setup", "Troubleshooting"],
  "reason": "Product release 3.5 included new OAuth flow"
}
```

**Change Log Format:**
```markdown
## Version History

### Version 2.0.0 - 2025-10-31
**Major Update:** Complete rewrite for new dashboard UI
- Redesigned all screenshots for new interface
- Updated navigation instructions
- Added video walkthrough
- Deprecated old workflow instructions

### Version 1.2.0 - 2025-09-15
**Minor Update:** Added advanced configuration section
- New section: Advanced Settings
- 5 new screenshots
- Updated troubleshooting guide

### Version 1.1.1 - 2025-08-20
**Patch:** Corrected API endpoint URL
- Fixed typo in authentication URL
- Updated code example
```

### 4.3 Rollback Procedures

**When to Rollback:**
- New version contains errors
- User feedback is overwhelmingly negative
- Breaking change not properly communicated
- Accidental deletion or corruption

**Rollback Process:**
```
1. Identify last good version
2. Verify version is complete and functional
3. Restore previous version content
4. Update version number (add "-rollback" suffix)
5. Add note explaining rollback
6. Notify content team
7. Create task to fix issues in rolled-back version
```

---

## 5. Access Control Rules

### 5.1 Content Permission Levels

**Public Content (Customer-Facing):**
- Access: Unauthenticated users
- Searchable: Yes (public search engines)
- Sharing: Unrestricted
- Examples: Getting started, FAQs, public API docs

**Authenticated Content (Customer Portal):**
- Access: Logged-in customers only
- Searchable: Internal search only
- Sharing: Link sharing within organization
- Examples: Advanced features, troubleshooting, account management

**Internal Content (Employee-Only):**
- Access: Company employees only
- Searchable: Internal search with permissions
- Sharing: Restricted to internal systems
- Examples: Internal processes, policies, sales enablement

**Confidential Content (Restricted):**
- Access: Specific roles only (explicit permissions)
- Searchable: No (manual access only)
- Sharing: Audited and logged
- Examples: Security procedures, proprietary information

### 5.2 Edit Permissions

**Permission Matrix:**
```
Role              | Create | Edit | Publish | Delete | Archive
------------------|--------|------|---------|--------|--------
Knowledge Lib     | Yes    | Yes  | Draft   | No     | No
Content Author    | Yes    | Own  | No      | No     | No
Content Reviewer  | No     | All  | Yes     | No     | No
Manager           | Yes    | All  | Yes     | Yes    | Yes
Admin             | Yes    | All  | Yes     | Yes    | Yes
```

**Edit Restrictions:**
```
IF user_role == "knowledge_librarian":
    can_edit = ["metadata", "tags", "formatting"]
    cannot_edit = ["core_content_without_approval"]
    must_flag_for_review = True

IF user_role == "content_author":
    can_edit = ["own_articles_only"]
    cannot_publish = True
    submit_for_review = True
```

### 5.3 Audit Requirements

**All Actions Must Be Logged:**
- Article creation
- Content modifications
- Publishing/unpublishing
- Deletion/archival
- Permission changes
- Bulk operations

**Audit Log Format:**
```json
{
  "timestamp": "2025-10-31T10:15:00Z",
  "user_id": "user_123",
  "action": "content_update",
  "article_id": "art_456",
  "changes": {
    "fields_modified": ["title", "content"],
    "version_before": "1.2.0",
    "version_after": "1.2.1"
  },
  "reason": "Fixed broken link in step 3"
}
```

---

## 6. Gap Analysis Methodology

### 6.1 Gap Detection Methods

**Automatic Detection:**
- Failed searches (confidence <0.70) tracked
- Support tickets without KB match
- "Article not helpful" feedback aggregated
- Agent escalations due to missing content
- New product features without documentation

**Manual Identification:**
- Content team brainstorming
- Customer requests
- Sales team feedback
- Support team observations
- Competitor KB comparison

### 6.2 Gap Prioritization

**Priority Scoring:**
```
frequency_score = occurrences_per_week * 10  // Max 50 points
impact_score = customer_count_affected       // Max 30 points
workaround_penalty = has_workaround ? -10 : 0
strategic_bonus = is_competitive_advantage ? +20 : 0

total_priority = frequency + impact + workaround_penalty + strategic_bonus
```

**Priority Bands:**
```
80-100: Critical (Create within 24 hours)
60-79:  High (Create within 1 week)
40-59:  Medium (Create within 1 month)
<40:    Low (Backlog)
```

### 6.3 Gap Closure Tracking

**Gap Report Template:**
```markdown
# Knowledge Gap Analysis - [Date]

## Critical Gaps (Create Within 24h)
1. **OAuth 2.0 Setup for Google Integration**
   - Frequency: 15 searches/tickets per week
   - Impact: 45 customers affected
   - Workaround: None (blocking use case)
   - Priority Score: 95
   - Status: Draft in progress
   - ETA: 2025-11-01

## High Priority Gaps (Create Within 1 Week)
[Similar format]

## Recently Closed Gaps
- [Topic]: Article created on [Date] - art_123
- [Topic]: Existing article updated on [Date] - art_456

## Trend Analysis
- Integration documentation requests increasing 20% MoM
- Authentication topics most common gap category
```

---

## 7. Search Optimization

### 7.1 Embedding Generation

**Embedding Strategy:**
- Generate embeddings for full article text
- Include metadata in embedding context
- Update embeddings on content change
- Use latest embedding model version
- Batch generate for efficiency

**Embedding Refresh Policy:**
```
IF content_updated:
    regenerate_embedding_immediately
ELIF embedding_model_upgraded:
    queue_for_batch_regeneration
ELIF embedding_age > 180_days:
    queue_for_refresh
```

### 7.2 Keyword Optimization

**Target Keywords:**
- Extract from article title and headers
- Include in metadata tags
- Add common misspellings to synonyms
- Map technical terms to plain language
- Track search queries that led to article

**SEO Best Practices:**
- Title: 50-60 characters, front-load keywords
- Summary: 150-160 characters, include primary keywords
- Headers: Use H2/H3 with descriptive keywords
- Alt text: Describe images with relevant terms
- URLs: Clean, keyword-rich slugs

### 7.3 Search Relevance Tuning

**Ranking Factors:**
```python
relevance_score = (
    semantic_similarity * 0.40 +
    keyword_match * 0.25 +
    freshness_score * 0.15 +
    popularity * 0.10 +
    authority * 0.10
)
```

**Freshness Bonus:**
- Updated within 30 days: +20% boost
- Updated 30-90 days: +10% boost
- Updated 90-180 days: No change
- Updated >180 days: -10% penalty

**Authority Signals:**
- Official product documentation: +30%
- SME-authored content: +20%
- High user ratings (>4.5): +15%
- Frequently accessed: +10%

---

## 8. Quality Assurance

### 8.1 Pre-Publication Checklist

**Technical Accuracy:**
- [ ] All facts verified
- [ ] Code examples tested
- [ ] Screenshots current
- [ ] Links functional
- [ ] Product version correct

**Content Quality:**
- [ ] Grammar and spelling perfect
- [ ] Readability score ≥8th grade
- [ ] Structure logical and clear
- [ ] Examples helpful and relevant
- [ ] Tone consistent with brand

**Completeness:**
- [ ] All required metadata present
- [ ] Related articles linked
- [ ] Troubleshooting included (if applicable)
- [ ] Prerequisites listed
- [ ] Expected outcomes stated

**Compliance:**
- [ ] No confidential information
- [ ] Copyright/licensing clear
- [ ] Privacy requirements met
- [ ] Accessibility standards met

### 8.2 Post-Publication Monitoring

**Track Metrics:**
- Page views (daily/weekly/monthly)
- Average time on page
- Bounce rate
- "Was this helpful?" ratings
- Search result click-through rate

**Quality Thresholds:**
```
IF helpful_rating < 3.0:
    flag_for_immediate_review
    priority = "high"
ELIF helpful_rating < 3.5:
    flag_for_improvement
    priority = "medium"
ELIF page_views < 10_per_month AND age > 90_days:
    consider_archiving
```

---

## 9. Content Lifecycle Management

### 9.1 Archival Policy

**Archive When:**
- Feature deprecated in product
- Content replaced by newer article
- No views in past 180 days
- Product version no longer supported
- Policy or process changed

**Archival Process:**
```
1. Mark article as "archived"
2. Add banner: "This content is archived and may be outdated"
3. Remove from primary search results
4. Redirect to replacement article (if exists)
5. Preserve for historical reference
6. Include in archive search only
```

**Do NOT Delete:**
- Archive instead of delete (preserve history)
- Exception: Legal requirement or security concern

### 9.2 Content Refresh Workflow

**Refresh Triggers:**
- Freshness score <75
- Product version update
- Low user ratings (<3.5)
- Customer feedback request
- Competitive analysis shows gaps

**Refresh Process:**
```
1. Review current article
2. Identify what needs updating
3. Gather new information
4. Update content and screenshots
5. Test all instructions
6. Increment version number
7. Add to change log
8. Republish
9. Notify stakeholders
```

---

## 10. Continuous Improvement

### 10.1 Performance Metrics

**Weekly Review:**
- New articles published
- Articles updated
- Gap analysis results
- Search effectiveness
- User satisfaction scores

**Monthly Analysis:**
- Content utilization trends
- Coverage rate changes
- Quality metric trends
- High-performing content
- Low-performing content

**Quarterly Strategy:**
- Content roadmap planning
- Gap closure progress
- Technology/tool evaluation
- Process improvements
- Competitive KB analysis

### 10.2 Feedback Integration

**User Feedback Sources:**
- "Was this helpful?" ratings
- Feedback form submissions
- Support ticket mentions
- Sales team input
- Social media mentions

**Action on Feedback:**
```
IF feedback_type == "inaccurate":
    priority = "critical"
    review_within = "24 hours"
ELIF feedback_type == "outdated":
    priority = "high"
    review_within = "1 week"
ELIF feedback_type == "unclear":
    priority = "medium"
    review_within = "2 weeks"
ELIF feedback_type == "suggestion":
    priority = "low"
    add_to_backlog
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-31 | Initial policy document |

---

## Related Documentation

- [`knowledge-librarian.md`](../roles/knowledge-librarian.md) - Role definition
- [`knowledge-librarian-template.md`](../../prompt-pack/templates/knowledge-librarian-template.md) - Prompt templates
- [Content Style Guide](../../../docs/content-style-guide.md) - Writing standards