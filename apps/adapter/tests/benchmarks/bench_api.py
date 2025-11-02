"""
API Performance Benchmarks for Transform Army AI.

Benchmarks all API endpoints, measuring response times, database query performance,
provider calls, and serialization overhead.

Performance Targets:
- API response time: < 200ms (p95)
- Database query: < 50ms (p95)
- Provider calls: < 1s (p95)
"""

import asyncio
import json
import uuid
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.models.workflow import Workflow, WorkflowStatus
from src.core.config import settings


# Test client setup
@pytest.fixture
def client():
    """Create test client for API benchmarks."""
    return TestClient(app)


@pytest.fixture
def mock_tenant_id():
    """Generate a test tenant ID."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_headers(mock_tenant_id):
    """Create mock headers for API requests."""
    return {
        "X-Tenant-ID": mock_tenant_id,
        "X-API-Key": "test-api-key",
        "Content-Type": "application/json"
    }


# Health Endpoint Benchmarks
def test_bench_health_endpoint(benchmark, client):
    """
    Benchmark health check endpoint.
    
    Target: < 50ms
    """
    def health_check():
        response = client.get("/health")
        assert response.status_code == 200
        return response
    
    result = benchmark.pedantic(health_check, iterations=100, rounds=10, warmup_rounds=5)
    assert result.status_code == 200


def test_bench_health_detailed_endpoint(benchmark, client):
    """
    Benchmark detailed health check endpoint.
    
    Target: < 100ms (includes DB checks)
    """
    def health_detailed():
        response = client.get("/health/detailed")
        return response
    
    result = benchmark.pedantic(health_detailed, iterations=50, rounds=10, warmup_rounds=3)


# CRM Endpoint Benchmarks
@patch('src.providers.crm.hubspot.HubSpotProvider.get_contacts')
def test_bench_crm_list_contacts(mock_get_contacts, benchmark, client, mock_headers):
    """
    Benchmark CRM contact listing endpoint.
    
    Target: < 200ms (p95)
    """
    mock_get_contacts.return_value = {
        "contacts": [
            {"id": str(uuid.uuid4()), "email": f"test{i}@example.com", "name": f"Test {i}"}
            for i in range(10)
        ],
        "total": 10
    }
    
    def list_contacts():
        response = client.get("/api/v1/crm/contacts", headers=mock_headers)
        assert response.status_code == 200
        return response
    
    result = benchmark.pedantic(list_contacts, iterations=100, rounds=10, warmup_rounds=5)


@patch('src.providers.crm.hubspot.HubSpotProvider.create_contact')
def test_bench_crm_create_contact(mock_create, benchmark, client, mock_headers):
    """
    Benchmark CRM contact creation endpoint.
    
    Target: < 300ms (includes external API call)
    """
    mock_create.return_value = {
        "id": str(uuid.uuid4()),
        "email": "new@example.com",
        "name": "New Contact"
    }
    
    contact_data = {
        "email": "new@example.com",
        "first_name": "New",
        "last_name": "Contact",
        "company": "Test Corp"
    }
    
    def create_contact():
        response = client.post(
            "/api/v1/crm/contacts",
            headers=mock_headers,
            json=contact_data
        )
        return response
    
    result = benchmark.pedantic(create_contact, iterations=50, rounds=10, warmup_rounds=3)


# Helpdesk Endpoint Benchmarks
@patch('src.providers.helpdesk.zendesk.ZendeskProvider.list_tickets')
def test_bench_helpdesk_list_tickets(mock_list, benchmark, client, mock_headers):
    """
    Benchmark helpdesk ticket listing endpoint.
    
    Target: < 200ms (p95)
    """
    mock_list.return_value = {
        "tickets": [
            {
                "id": str(uuid.uuid4()),
                "subject": f"Ticket {i}",
                "status": "open",
                "priority": "normal"
            }
            for i in range(20)
        ],
        "total": 20
    }
    
    def list_tickets():
        response = client.get("/api/v1/helpdesk/tickets", headers=mock_headers)
        assert response.status_code == 200
        return response
    
    result = benchmark.pedantic(list_tickets, iterations=100, rounds=10, warmup_rounds=5)


@patch('src.providers.helpdesk.zendesk.ZendeskProvider.create_ticket')
def test_bench_helpdesk_create_ticket(mock_create, benchmark, client, mock_headers):
    """
    Benchmark helpdesk ticket creation endpoint.
    
    Target: < 300ms
    """
    mock_create.return_value = {
        "id": str(uuid.uuid4()),
        "subject": "Test Ticket",
        "status": "new"
    }
    
    ticket_data = {
        "subject": "Test Ticket",
        "description": "Test description",
        "priority": "normal",
        "requester_email": "test@example.com"
    }
    
    def create_ticket():
        response = client.post(
            "/api/v1/helpdesk/tickets",
            headers=mock_headers,
            json=ticket_data
        )
        return response
    
    result = benchmark.pedantic(create_ticket, iterations=50, rounds=10, warmup_rounds=3)


# Workflow Endpoint Benchmarks
@patch('src.repositories.workflow.WorkflowRepository.list_workflows')
def test_bench_workflow_list(mock_list, benchmark, client, mock_headers):
    """
    Benchmark workflow listing endpoint.
    
    Target: < 150ms
    """
    mock_list.return_value = [
        Mock(
            id=uuid.uuid4(),
            name=f"Workflow {i}",
            status=WorkflowStatus.ACTIVE,
            definition={"steps": []},
        )
        for i in range(10)
    ]
    
    def list_workflows():
        response = client.get("/api/v1/workflows", headers=mock_headers)
        return response
    
    result = benchmark.pedantic(list_workflows, iterations=100, rounds=10, warmup_rounds=5)


# Serialization Benchmarks
def test_bench_json_serialization_small(benchmark):
    """
    Benchmark JSON serialization of small payloads.
    
    Target: < 1ms
    """
    data = {
        "id": str(uuid.uuid4()),
        "name": "Test",
        "value": 123,
        "active": True
    }
    
    result = benchmark.pedantic(lambda: json.dumps(data), iterations=1000, rounds=10)


def test_bench_json_serialization_medium(benchmark):
    """
    Benchmark JSON serialization of medium payloads.
    
    Target: < 5ms
    """
    data = {
        "contacts": [
            {
                "id": str(uuid.uuid4()),
                "email": f"test{i}@example.com",
                "name": f"Test User {i}",
                "company": f"Company {i}",
                "metadata": {"key1": "value1", "key2": "value2"}
            }
            for i in range(50)
        ]
    }
    
    result = benchmark.pedantic(lambda: json.dumps(data), iterations=500, rounds=10)


def test_bench_json_serialization_large(benchmark):
    """
    Benchmark JSON serialization of large payloads.
    
    Target: < 20ms
    """
    data = {
        "workflows": [
            {
                "id": str(uuid.uuid4()),
                "name": f"Workflow {i}",
                "definition": {
                    "steps": [
                        {
                            "id": str(uuid.uuid4()),
                            "name": f"Step {j}",
                            "agent_id": str(uuid.uuid4()),
                            "config": {"param1": "value1", "param2": "value2"}
                        }
                        for j in range(10)
                    ]
                },
                "metadata": {"created_by": "system", "tags": ["test", "benchmark"]}
            }
            for i in range(100)
        ]
    }
    
    result = benchmark.pedantic(lambda: json.dumps(data), iterations=100, rounds=10)


def test_bench_json_deserialization_small(benchmark):
    """
    Benchmark JSON deserialization of small payloads.
    
    Target: < 1ms
    """
    json_str = json.dumps({
        "id": str(uuid.uuid4()),
        "name": "Test",
        "value": 123,
        "active": True
    })
    
    result = benchmark.pedantic(lambda: json.loads(json_str), iterations=1000, rounds=10)


def test_bench_json_deserialization_medium(benchmark):
    """
    Benchmark JSON deserialization of medium payloads.
    
    Target: < 10ms
    """
    json_str = json.dumps({
        "contacts": [
            {
                "id": str(uuid.uuid4()),
                "email": f"test{i}@example.com",
                "name": f"Test User {i}",
                "company": f"Company {i}",
                "metadata": {"key1": "value1", "key2": "value2"}
            }
            for i in range(50)
        ]
    })
    
    result = benchmark.pedantic(lambda: json.loads(json_str), iterations=500, rounds=10)


# Response Time Distribution Benchmarks
@pytest.mark.parametrize("endpoint", [
    "/health",
    "/api/v1/crm/contacts",
    "/api/v1/helpdesk/tickets",
    "/api/v1/workflows"
])
def test_bench_endpoint_response_time_distribution(benchmark, client, mock_headers, endpoint):
    """
    Benchmark response time distribution for key endpoints.
    
    Measures: min, max, mean, median, stddev, percentiles
    Target: p95 < 200ms
    """
    with patch('src.providers.crm.hubspot.HubSpotProvider.get_contacts', return_value={"contacts": [], "total": 0}), \
         patch('src.providers.helpdesk.zendesk.ZendeskProvider.list_tickets', return_value={"tickets": [], "total": 0}), \
         patch('src.repositories.workflow.WorkflowRepository.list_workflows', return_value=[]):
        
        def make_request():
            response = client.get(endpoint, headers=mock_headers)
            return response
        
        result = benchmark.pedantic(make_request, iterations=200, rounds=10, warmup_rounds=5)


# Middleware Overhead Benchmarks
def test_bench_middleware_overhead(benchmark, client):
    """
    Benchmark middleware processing overhead.
    
    Measures the overhead added by all middleware layers.
    Target: < 20ms overhead
    """
    def request_with_middleware():
        response = client.get("/")
        assert response.status_code == 200
        return response
    
    result = benchmark.pedantic(request_with_middleware, iterations=200, rounds=10, warmup_rounds=5)


# Concurrent Request Benchmarks
def test_bench_concurrent_requests(benchmark, client, mock_headers):
    """
    Benchmark concurrent request handling.
    
    Tests system performance under concurrent load.
    Target: < 300ms per request under 10 concurrent requests
    """
    import concurrent.futures
    
    with patch('src.providers.crm.hubspot.HubSpotProvider.get_contacts', return_value={"contacts": [], "total": 0}):
        def make_concurrent_requests():
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(client.get, "/api/v1/crm/contacts", headers=mock_headers)
                    for _ in range(10)
                ]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            return results
        
        result = benchmark.pedantic(make_concurrent_requests, iterations=20, rounds=5, warmup_rounds=2)


# Error Handling Performance
def test_bench_error_handling(benchmark, client, mock_headers):
    """
    Benchmark error handling performance.
    
    Ensures error responses are fast.
    Target: < 50ms for error responses
    """
    def trigger_error():
        # Request to non-existent endpoint
        response = client.get("/api/v1/nonexistent", headers=mock_headers)
        assert response.status_code == 404
        return response
    
    result = benchmark.pedantic(trigger_error, iterations=100, rounds=10, warmup_rounds=5)


# Validation Performance
def test_bench_request_validation(benchmark, client, mock_headers):
    """
    Benchmark request validation performance.
    
    Target: < 5ms for validation
    """
    invalid_data = {
        "email": "not-an-email",  # Invalid email
        "name": "",  # Empty name
    }
    
    with patch('src.providers.crm.hubspot.HubSpotProvider.create_contact'):
        def validate_request():
            response = client.post(
                "/api/v1/crm/contacts",
                headers=mock_headers,
                json=invalid_data
            )
            return response
        
        result = benchmark.pedantic(validate_request, iterations=200, rounds=10, warmup_rounds=5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])