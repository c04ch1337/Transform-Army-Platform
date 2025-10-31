# QA Auditor Agent - Operating Policies

**Agent ID:** `qa-auditor`  
**Version:** 1.0.0  
**Last Updated:** 2025-10-31

---

## Policy Overview

This document defines rubric scoring methodology, test case generation rules, performance threshold definitions, reporting cadence, and remediation procedures for the QA Auditor Agent.

---

## 1. Rubric Scoring Methodology

### 1.1 General Quality Rubric (0-10 Scale)

**Five Evaluation Dimensions:**

**1. Accuracy (0-10 points)** - All facts correct, properly verified
**2. Completeness (0-10 points)** - All required elements present
**3. Format & Structure (0-10 points)** - Professional organization
**4. Tone & Style (0-10 points)** - Appropriate brand voice
**5. Compliance (0-10 points)** - All policies followed

**Final Score:** Average of five dimensions (0-10 scale)

**Quality Bands:**
- 9.0-10.0: Excellent
- 8.0-8.9: Good
- 7.0-7.9: Acceptable
- 6.0-6.9: Needs Improvement
- <6.0: Unacceptable (Block)

### 1.2 Scoring Consistency Requirements

**Every Evaluation Must:**
- Apply all five rubric dimensions
- Use objective criteria (no personal opinion)
- Provide specific evidence for scores
- Be reproducible (same input → same score)
- Document reasoning clearly

**Prohibited:**
- Subjective or emotional scoring
- Inconsistent application of criteria
- Skipping rubric dimensions
- Score inflation or deflation
- Bias toward specific agents

---

## 2. Test Case Generation Rules

### 2.1 When to Generate Test Cases

**Automatic Generation:**
- Quality score <6.0 (negative test case)
- Quality score >9.5 (positive test case)
- Edge case handled successfully
- Bug fixed (regression test)
- New feature deployed (smoke test)

### 2.2 Test Case Structure

**Required Fields:**
```json
{
  "test_id": "unique_identifier",
  "agent": "agent_type",
  "scenario": "description",
  "input": {/* test input */},
  "expected_output": {/* expected result */},
  "rubric_criteria": {/* min scores per dimension */},
  "tags": ["category", "priority"]
}
```

---

## 3. Performance Thresholds

**Agent Quality Targets:**
- BDR Concierge: ≥8.0/10
- Support Concierge: ≥8.0/10
- Research Recon: ≥8.5/10
- Ops Sapper: ≥8.5/10
- Knowledge Librarian: ≥8.0/10
- QA Auditor: ≥9.0/10

**Detection Accuracy:**
- True Positive Rate: ≥95%
- False Positive Rate: ≤5%
- False Negative Rate: ≤3%

---

## 4. Reporting Cadence

**Real-Time:** Quality blocks (<6.0 score)
**Hourly:** Quality trends and alerts
**Daily:** Quality summary report
**Weekly:** Comprehensive quality digest
**Monthly:** Strategic quality review

---

## 5. Remediation Procedures

**When Score <6.0:**
1. Block output immediately
2. Alert agent owner
3. Document specific issues
4. Create remediation task
5. Monitor subsequent outputs
6. Verify improvement

**When Score 6.0-6.9:**
1. Allow with warning
2. Flag for improvement
3. Track trend
4. Provide feedback
5. Review weekly

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-31 | Initial policy document |

---

## Related Documentation

- [`qa-auditor.md`](../roles/qa-auditor.md) - Role definition
- [`qa-auditor-template.md`](../../prompt-pack/templates/qa-auditor-template.md) - Prompt templates