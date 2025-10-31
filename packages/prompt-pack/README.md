# Transform Army AI - Prompt Pack

System prompts and templates for agent interactions.

## Overview

The prompt pack provides a centralized repository of prompts, templates, and instructions that define agent behaviors and capabilities. Prompts are version-controlled, tested, and optimized for consistency and performance.

## Directory Structure

```
prompt-pack/
├── system/             # System-level prompts
│   ├── agent-core.md  # Core agent instructions
│   ├── safety.md      # Safety guidelines
│   └── ethics.md      # Ethical guidelines
└── templates/         # Prompt templates
    ├── bdr/           # BDR agent templates
    ├── support/       # Support agent templates
    ├── research/      # Research agent templates
    ├── ops/           # Ops agent templates
    ├── librarian/     # Librarian agent templates
    └── qa/            # QA agent templates
```

## System Prompts

### Agent Core Instructions

Foundational instructions all agents inherit:

```markdown
# Agent Core Instructions

You are an AI agent working as part of the Transform Army AI platform.

## Core Principles
1. **Accuracy First**: Verify information before acting
2. **Transparency**: Explain your reasoning and limitations
3. **Safety**: Never take destructive actions without approval
4. **Privacy**: Respect data privacy and confidentiality
5. **Helpfulness**: Provide value in every interaction

## Capabilities
- Access to external tools and integrations
- Ability to search knowledge bases
- Coordination with other agents
- Human escalation when needed

## Limitations
- Cannot access data outside your tenant scope
- Cannot perform actions requiring approval without confirmation
- Cannot guarantee 100% accuracy
- Must operate within rate limits
```

### Safety Guidelines

Safety instructions for all agents:

```markdown
# Safety Guidelines

## Data Handling
- Never expose sensitive information in logs
- Mask PII when displaying data
- Respect data retention policies
- Follow encryption requirements

## Action Safety
- Verify before creating/updating records
- Never delete without explicit approval
- Check for duplicates before creating
- Validate input data

## Error Handling
- Fail gracefully with clear error messages
- Log errors for debugging
- Escalate critical failures
- Never expose internal errors to users
```

## Prompt Templates

### Template Structure

Each agent has role-specific prompt templates:

```
templates/
└── bdr/
    ├── lead-qualification.md
    ├── email-composition.md
    ├── meeting-scheduling.md
    └── crm-enrichment.md
```

### Template Format

Templates use a consistent format with variables:

```markdown
---
name: Lead Qualification
agent: BDR Concierge
version: 1.0.0
input_variables:
  - lead_data
  - qualification_criteria
output_format: json
---

# Lead Qualification Task

You are a BDR agent tasked with qualifying the following lead:

## Lead Information
{{lead_data}}

## Qualification Criteria
{{qualification_criteria}}

## Your Task
1. Analyze the lead data against qualification criteria
2. Assign a qualification score (0-100)
3. Provide reasoning for the score
4. Recommend next actions

## Output Format
Provide your response as JSON:
{
  "score": <number>,
  "qualified": <boolean>,
  "reasoning": "<string>",
  "next_actions": ["<action1>", "<action2>"],
  "confidence": <number>
}
```

## Agent-Specific Templates

### BDR Concierge Templates

1. **Lead Qualification**: Score and qualify inbound leads
2. **Email Composition**: Draft outreach emails
3. **Meeting Scheduling**: Coordinate meeting times
4. **CRM Enrichment**: Enrich contact data

### Support Concierge Templates

1. **Ticket Triage**: Classify and prioritize tickets
2. **Response Generation**: Draft support responses
3. **Knowledge Search**: Find relevant help articles
4. **Escalation Assessment**: Determine when to escalate

### Research Recon Templates

1. **Company Research**: Gather company intelligence
2. **Market Analysis**: Analyze market trends
3. **Competitive Intel**: Research competitors
4. **Data Enrichment**: Validate and enrich data

### Ops Sapper Templates

1. **Process Automation**: Automate workflows
2. **Data Transformation**: Transform data formats
3. **Integration Setup**: Configure integrations
4. **Error Recovery**: Handle and recover from errors

### Knowledge Librarian Templates

1. **Document Indexing**: Index and categorize documents
2. **Semantic Search**: Perform semantic searches
3. **Content Curation**: Curate relevant content
4. **Knowledge Updates**: Maintain knowledge base

### QA Auditor Templates

1. **Output Validation**: Validate agent outputs
2. **Quality Scoring**: Score output quality
3. **Compliance Check**: Check regulatory compliance
4. **Error Detection**: Detect errors and anomalies

## Template Variables

Common template variables:

```yaml
# Input variables
{{tenant_id}}          # Current tenant identifier
{{user_context}}       # User/requester context
{{conversation_history}} # Previous conversation
{{available_tools}}    # Tools available to agent
{{knowledge_context}}  # Relevant knowledge base content

# Configuration variables
{{temperature}}        # Model temperature
{{max_tokens}}        # Maximum response tokens
{{model}}             # Model identifier

# Environment variables
{{timestamp}}         # Current timestamp
{{correlation_id}}    # Request correlation ID
```

## Prompt Engineering Best Practices

### 1. Clear Instructions

```markdown
✓ GOOD: "Analyze the lead data and provide a score from 0-100"
✗ BAD: "Look at this lead"
```

### 2. Structured Output

```markdown
✓ GOOD: Specify JSON schema for responses
✗ BAD: Accept any format
```

### 3. Examples

```markdown
Include 2-3 examples of expected input/output
```

### 4. Constraints

```markdown
Explicitly state what the agent should NOT do
```

### 5. Context

```markdown
Provide relevant context and background information
```

## Prompt Testing

### Test Framework

```python
from prompt_pack.testing import PromptTest

def test_lead_qualification():
    """Test lead qualification prompt."""
    prompt = load_template("bdr/lead-qualification.md")
    
    result = prompt.render({
        "lead_data": sample_lead,
        "qualification_criteria": criteria
    })
    
    assert "score" in result
    assert 0 <= result["score"] <= 100
```

### Evaluation Metrics

- **Accuracy**: Does it produce correct outputs?
- **Consistency**: Same inputs → same outputs?
- **Completeness**: Does it address all requirements?
- **Clarity**: Is the output clear and actionable?
- **Safety**: Does it follow safety guidelines?

## Prompt Versioning

Prompts are versioned for tracking changes:

```
templates/
└── bdr/
    └── lead-qualification/
        ├── v1.0.0.md
        ├── v1.1.0.md
        └── v2.0.0.md
```

Version format: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, improvements

## Contributing

When adding new prompts:

1. Follow the template format
2. Include input/output examples
3. Add tests for the prompt
4. Document variables used
5. Version appropriately
6. Update this README

## License

MIT License - see [LICENSE](../../LICENSE) for details.