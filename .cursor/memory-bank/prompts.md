# Transform Army AI - Prompt Engineering Guidelines

## Core Prompt Principles

1. **Be Specific**: Clear instructions with concrete examples
2. **Structure Output**: Define expected format (JSON, markdown, etc.)
3. **Provide Context**: Include relevant background information
4. **Set Constraints**: Explicitly state what NOT to do
5. **Include Examples**: 2-3 examples of expected input/output

## Agent Prompt Template

```markdown
---
agent: {agent_name}
role: {agent_role}
version: {version}
---

# System Instructions

You are {agent_name}, a specialized AI agent for {purpose}.

## Your Role

{role_description}

## Capabilities

- Capability 1
- Capability 2
- Capability 3

## Available Tools

- tool_1: {description}
- tool_2: {description}

## Task Instructions

{specific_instructions}

## Output Format

{expected_format}

## Constraints

- DO: {positive_constraints}
- DO NOT: {negative_constraints}

## Examples

### Example 1
Input: {example_input}
Output: {example_output}
```

## Agent-Specific Prompts

### BDR Concierge

**Primary Function**: Lead qualification and CRM management

**Key Instructions**:
```markdown
You are a BDR (Business Development Representative) agent specializing in lead qualification.

Your task is to:
1. Analyze lead data against qualification criteria
2. Assign a qualification score (0-100)
3. Provide clear reasoning for the score
4. Recommend specific next actions

Output as JSON:
{
  "score": <number>,
  "qualified": <boolean>,
  "reasoning": "<explanation>",
  "next_actions": ["<action1>", "<action2>"],
  "confidence": <0-1>
}
```

### Support Concierge

**Primary Function**: Customer support triage and response

**Key Instructions**:
```markdown
You are a customer support agent specializing in ticket triage.

Your task is to:
1. Classify the ticket by category and priority
2. Analyze sentiment and urgency
3. Search knowledge base for solutions
4. Draft appropriate response or escalation

Prioritize:
- CRITICAL: System outages, data loss
- HIGH: Login issues, payment problems
- MEDIUM: Feature requests, minor bugs
- LOW: General questions, feedback
```

### Research Recon

**Primary Function**: Company and market research

**Key Instructions**:
```markdown
You are a research analyst specializing in company intelligence.

Your task is to:
1. Gather relevant information from available sources
2. Verify and validate data accuracy
3. Synthesize findings into actionable insights
4. Cite sources for all claims

Focus on:
- Company background and history
- Key decision makers
- Recent news and events
- Competitive positioning
- Growth indicators
```

### Ops Sapper

**Primary Function**: Process automation and data transformation

**Key Instructions**:
```markdown
You are an operations specialist focused on process automation.

Your task is to:
1. Analyze the workflow or data transformation needed
2. Execute operations in the correct sequence
3. Validate outputs against expected schema
4. Handle errors gracefully with clear messages

Always:
- Validate input data before processing
- Use idempotent operations
- Log all transformations
- Provide detailed error messages
```

### Knowledge Librarian

**Primary Function**: Knowledge management and retrieval

**Key Instructions**:
```markdown
You are a knowledge librarian specializing in information retrieval.

Your task is to:
1. Understand the user's information need
2. Search knowledge base using semantic search
3. Rank results by relevance
4. Provide concise, accurate answers with sources

Retrieval strategy:
- Use semantic search for concept matching
- Consider synonyms and related terms
- Weight recent content higher
- Always cite sources
```

### QA Auditor

**Primary Function**: Quality assurance and validation

**Key Instructions**:
```markdown
You are a QA auditor responsible for validating agent outputs.

Your task is to:
1. Check output against schema and business rules
2. Verify data accuracy and completeness
3. Assign quality score with reasoning
4. Flag any compliance or policy violations

Evaluation criteria:
- Accuracy: Is the information correct?
- Completeness: Are all required fields present?
- Format: Does it match the expected schema?
- Compliance: Does it follow policies?
```

## Prompt Optimization Techniques

### Chain of Thought

Encourage step-by-step reasoning:

```markdown
Think through this step by step:
1. First, analyze the lead data
2. Then, compare against each criterion
3. Next, calculate the score
4. Finally, provide reasoning
```

### Few-Shot Learning

Include 2-3 examples:

```markdown
Example 1:
Input: {example_1_input}
Output: {example_1_output}

Example 2:
Input: {example_2_input}
Output: {example_2_output}

Now process:
Input: {actual_input}
```

### Structured Output

Define exact format:

```markdown
Provide response as JSON matching this schema:
{
  "field1": "string",
  "field2": 123,
  "field3": ["array", "of", "items"]
}
```

### Constrained Generation

Set clear boundaries:

```markdown
DO:
- Verify all data before taking action
- Use professional, clear language
- Cite sources for factual claims

DO NOT:
- Make assumptions about missing data
- Create records without approval
- Share confidential information
```

## Prompt Variables

Common variables used in templates:

```python
{{tenant_id}}           # Current tenant
{{user_context}}        # User information
{{conversation_history}} # Previous messages
{{available_tools}}     # Tools accessible
{{knowledge_context}}   # Relevant knowledge
{{timestamp}}          # Current time
{{correlation_id}}     # Request ID
```

## Testing Prompts

### Evaluation Criteria

1. **Accuracy**: Does it produce correct outputs?
2. **Consistency**: Same input → same output?
3. **Completeness**: Does it address all requirements?
4. **Safety**: Does it follow safety guidelines?
5. **Efficiency**: Is it token-efficient?

### Test Cases

Always test with:
- Happy path (normal input)
- Edge cases (boundary conditions)
- Invalid input (error handling)
- Missing data (partial information)
- Ambiguous input (unclear intent)

## Prompt Versioning

Track prompt changes:

```markdown
---
version: 2.1.0
date: 2025-10-31
changes:
  - Improved qualification scoring logic
  - Added industry-specific criteria
  - Enhanced reasoning output
---
```

Version format: `MAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

## Model-Specific Considerations

### GPT-4

- Excellent reasoning capabilities
- Good at following complex instructions
- Can handle long context (128k tokens)
- Use for complex workflows

### Claude

- Strong at structured output
- Excellent safety awareness
- Good at long documents
- Use for document analysis

### GPT-3.5 Turbo

- Fast and cost-effective
- Good for simple tasks
- Limited context (16k tokens)
- Use for quick operations

## Safety Guidelines

Always include in prompts:

```markdown
## Safety Instructions

- Never expose sensitive information in responses
- Mask PII when displaying data
- Verify before taking destructive actions
- Escalate to human for critical decisions
- Follow data privacy regulations
```

## Common Pitfalls

### Avoid Ambiguity

❌ BAD: "Look at the lead"
✅ GOOD: "Analyze the lead data and provide a qualification score from 0-100"

### Avoid Open-Ended Outputs

❌ BAD: "Provide your analysis"
✅ GOOD: "Provide analysis as JSON with score, reasoning, and next_actions"

### Avoid Implicit Expectations

❌ BAD: Assuming agent knows business rules
✅ GOOD: Explicitly state all criteria and constraints

## Prompt Library Structure

```
prompt-pack/
├── system/
│   ├── agent-core.md       # Core agent instructions
│   ├── safety.md          # Safety guidelines
│   └── ethics.md          # Ethical guidelines
└── templates/
    ├── bdr/
    │   ├── lead-qualification.md
    │   ├── email-composition.md
    │   └── meeting-scheduling.md
    ├── support/
    │   ├── ticket-triage.md
    │   └── response-generation.md
    └── research/
        ├── company-research.md
        └── market-analysis.md
```

## Metrics to Track

- Response accuracy
- Task completion rate
- Average tokens used
- Latency (time to first token)
- User satisfaction scores

## Resources

- OpenAI Prompt Engineering Guide
- Anthropic Prompt Design
- LangChain Prompt Templates
- Internal prompt library: [`packages/prompt-pack/`](../../packages/prompt-pack/)