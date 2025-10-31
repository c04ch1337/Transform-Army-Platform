# Transform Army AI - Evaluation Harness

QA and evaluation system for testing agent performance, quality, and reliability.

## Overview

The evaluation harness provides systematic testing and quality assurance for Transform Army AI agents. It includes test scenarios, scoring rubrics, and automated test runners to ensure agent behaviors meet quality standards.

## Features

- **Test Scenarios**: Predefined test cases for each agent role
- **Scoring Rubrics**: Quantitative evaluation metrics
- **Automated Testing**: Continuous evaluation of agent performance
- **Performance Benchmarks**: Track agent improvements over time
- **Quality Gates**: Prevent regressions before deployment

## Getting Started

### Prerequisites

- Python 3.11+
- Access to adapter service API
- Test data fixtures

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## Project Structure

```
tests/
├── agents/         # Agent-specific test suites
│   ├── test_bdr_concierge.py
│   ├── test_support_concierge.py
│   ├── test_research_recon.py
│   ├── test_ops_sapper.py
│   ├── test_knowledge_librarian.py
│   └── test_qa_auditor.py
├── integration/    # Integration tests
├── performance/    # Performance benchmarks
└── fixtures/       # Test data

rubrics/
├── accuracy.yml    # Accuracy scoring criteria
├── latency.yml     # Response time criteria
├── quality.yml     # Output quality criteria
└── compliance.yml  # Policy compliance criteria
```

## Test Categories

### Unit Tests
Test individual agent capabilities and tool integrations.

```bash
pytest tests/agents/ -v
```

### Integration Tests
Test multi-agent workflows and system interactions.

```bash
pytest tests/integration/ -v
```

### Performance Tests
Benchmark response times and throughput.

```bash
pytest tests/performance/ -v --benchmark
```

## Scoring Rubrics

### Accuracy Rubric

Evaluates correctness of agent outputs:
- Information extraction accuracy
- Data transformation correctness
- Decision-making quality

### Latency Rubric

Evaluates response time performance:
- P50, P95, P99 latencies
- Time to first token
- End-to-end completion time

### Quality Rubric

Evaluates output quality:
- Response completeness
- Formatting consistency
- Error handling
- User experience

### Compliance Rubric

Evaluates policy adherence:
- Data privacy compliance
- Security best practices
- Business rule enforcement

## Writing Tests

### Basic Test Structure

```python
import pytest
from evals.fixtures import sample_lead
from evals.rubrics import score_response

async def test_bdr_lead_qualification():
    """Test BDR agent lead qualification."""
    # Arrange
    lead = sample_lead()
    
    # Act
    result = await bdr_agent.qualify_lead(lead)
    
    # Assert
    assert result.score >= 0.7
    assert result.reasoning is not None
    
    # Evaluate
    quality_score = score_response(result, rubric="quality")
    assert quality_score >= 0.8
```

### Running Specific Tests

```bash
# Run BDR agent tests
pytest tests/agents/test_bdr_concierge.py -v

# Run with coverage
pytest --cov=tests --cov-report=html

# Run performance benchmarks
pytest tests/performance/ --benchmark-only
```

## Evaluation Metrics

### Agent Performance Metrics

- **Accuracy**: % of correct outputs
- **Precision**: % of relevant results
- **Recall**: % of captured relevant items
- **F1 Score**: Harmonic mean of precision/recall
- **Latency**: Response time distribution
- **Error Rate**: % of failed requests

### Quality Metrics

- **Completeness**: % of required fields populated
- **Consistency**: Format adherence score
- **Clarity**: Readability score
- **Usefulness**: User satisfaction score

## Continuous Evaluation

Tests run automatically on:
- Every pull request
- Nightly builds
- Production deployments (smoke tests)

### Quality Gates

- Minimum accuracy: 85%
- Maximum P95 latency: 5 seconds
- Maximum error rate: 1%
- Minimum quality score: 0.8

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Realistic Data**: Use production-like test data
3. **Clear Assertions**: Test one behavior per test
4. **Performance**: Include latency benchmarks
5. **Documentation**: Explain test purpose and expectations

## Contributing

When adding new tests:
1. Follow existing test structure
2. Add appropriate rubric evaluations
3. Document expected behaviors
4. Include edge cases
5. Update test documentation

## License

MIT License - see [LICENSE](../../LICENSE) for details.