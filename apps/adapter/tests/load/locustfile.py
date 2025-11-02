"""
Locust Load Testing Suite for Transform Army AI Adapter Service

This module provides comprehensive load testing scenarios for the adapter service,
simulating realistic user behavior across all endpoints.

Test Scenarios:
- Smoke Test: 1 user, 1 minute (sanity check)
- Load Test: 100 users, 10 minutes (average load)
- Stress Test: Ramp to 500 users, 20 minutes (breaking point)
- Spike Test: Sudden jump to 200 users (traffic spike)
- Soak Test: 50 users, 2 hours (memory leaks)

Run Examples:
    # Smoke test
    locust -f locustfile.py --headless -u 1 -r 1 -t 1m --host=http://localhost:8000
    
    # Load test
    locust -f locustfile.py --headless -u 100 -r 10 -t 10m --host=http://localhost:8000
    
    # UI mode
    locust -f locustfile.py --host=http://localhost:8000
"""

import json
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from locust import HttpUser, TaskSet, between, tag, task, events
from locust.exception import RescheduleTask


class APIHeaders:
    """Generate standardized headers for API requests"""
    
    @staticmethod
    def get_headers(tenant_id: str = "tenant_001", include_idempotency: bool = False) -> Dict[str, str]:
        """Get standard headers for API requests"""
        correlation_id = f"cor_locust_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer ta_test_{tenant_id}",
            "X-Correlation-ID": correlation_id,
            "X-Tenant-ID": tenant_id
        }
        
        if include_idempotency:
            headers["X-Idempotency-Key"] = f"idm_locust_{uuid.uuid4()}"
        
        return headers


class HealthCheckTasks(TaskSet):
    """Health check and monitoring tasks"""
    
    @tag("health", "monitoring")
    @task(5)
    def health_check(self):
        """Check service health"""
        self.client.get(
            "/health",
            name="Health Check"
        )
    
    @tag("health", "monitoring")
    @task(1)
    def root_endpoint(self):
        """Check root endpoint"""
        self.client.get(
            "/",
            name="Root Endpoint"
        )
    
    @tag("monitoring")
    @task(2)
    def metrics_endpoint(self):
        """Check metrics endpoint"""
        self.client.get(
            "/metrics",
            name="Metrics"
        )


class CRMTasks(TaskSet):
    """CRM operations tasks"""
    
    contact_ids = []
    
    @tag("crm", "create")
    @task(10)
    def create_contact(self):
        """Create a new CRM contact"""
        contact_data = {
            "idempotency_key": f"idm_contact_{uuid.uuid4()}",
            "correlation_id": f"cor_crm_{int(time.time())}_{uuid.uuid4().hex[:8]}",
            "contact": {
                "email": f"loadtest.{uuid.uuid4().hex[:8]}@example.com",
                "first_name": f"LoadTest{random.randint(1, 1000)}",
                "last_name": f"User{random.randint(1, 1000)}",
                "company": random.choice(["Acme Corp", "Tech Innovations", "Global Solutions"]),
                "phone": f"+1-555-{random.randint(1000, 9999)}",
                "title": random.choice(["VP Sales", "Director", "Manager", "Engineer"]),
                "custom_fields": {
                    "lead_source": random.choice(["website", "referral", "campaign"]),
                    "lead_score": random.randint(50, 100)
                }
            },
            "options": {
                "dedupe_by": ["email"],
                "update_if_exists": False
            }
        }
        
        with self.client.post(
            "/api/v1/crm/contacts",
            json=contact_data,
            headers=APIHeaders.get_headers(include_idempotency=True),
            catch_response=True,
            name="CRM: Create Contact"
        ) as response:
            if response.status_code in [200, 201]:
                result = response.json()
                if "result" in result and "id" in result["result"]:
                    self.contact_ids.append(result["result"]["id"])
                response.success()
            elif response.status_code == 409:
                # Conflict is acceptable in load testing
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @tag("crm", "read")
    @task(15)
    def search_contacts(self):
        """Search for contacts"""
        search_terms = [
            "loadtest",
            "example.com",
            "Acme",
            "VP",
            "Tech"
        ]
        
        params = {
            "query": random.choice(search_terms),
            "limit": 10
        }
        
        self.client.get(
            "/api/v1/crm/contacts/search",
            params=params,
            headers=APIHeaders.get_headers(),
            name="CRM: Search Contacts"
        )
    
    @tag("crm", "update")
    @task(5)
    def add_note_to_contact(self):
        """Add note to a contact"""
        if not self.contact_ids:
            raise RescheduleTask()
        
        contact_id = random.choice(self.contact_ids)
        note_data = {
            "idempotency_key": f"idm_note_{uuid.uuid4()}",
            "correlation_id": f"cor_note_{int(time.time())}",
            "note": {
                "content": f"Load test note at {datetime.utcnow().isoformat()}",
                "type": "call_note",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        self.client.post(
            f"/api/v1/crm/contacts/{contact_id}/notes",
            json=note_data,
            headers=APIHeaders.get_headers(include_idempotency=True),
            name="CRM: Add Contact Note"
        )
    
    @tag("crm", "create")
    @task(3)
    def create_deal(self):
        """Create a new deal/opportunity"""
        deal_data = {
            "idempotency_key": f"idm_deal_{uuid.uuid4()}",
            "correlation_id": f"cor_deal_{int(time.time())}",
            "deal": {
                "name": f"LoadTest Deal - {random.choice(['Enterprise', 'Standard', 'Premium'])}",
                "amount": random.choice([10000, 25000, 50000, 100000]),
                "currency": "USD",
                "stage": random.choice(["qualification", "proposal", "negotiation"]),
                "close_date": (datetime.utcnow() + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%d"),
                "custom_fields": {
                    "deal_source": "load_test",
                    "product_interest": random.choice(["enterprise", "standard"])
                }
            }
        }
        
        self.client.post(
            "/api/v1/crm/deals",
            json=deal_data,
            headers=APIHeaders.get_headers(include_idempotency=True),
            name="CRM: Create Deal"
        )


class HelpdeskTasks(TaskSet):
    """Helpdesk operations tasks"""
    
    ticket_ids = []
    
    @tag("helpdesk", "create")
    @task(8)
    def create_ticket(self):
        """Create a support ticket"""
        priorities = ["low", "normal", "high", "urgent"]
        subjects = [
            "Login issue",
            "Performance problem",
            "Feature request",
            "Bug report",
            "Integration question"
        ]
        
        ticket_data = {
            "idempotency_key": f"idm_ticket_{uuid.uuid4()}",
            "correlation_id": f"cor_ticket_{int(time.time())}",
            "ticket": {
                "subject": f"{random.choice(subjects)} - Load Test",
                "description": f"Load test ticket created at {datetime.utcnow().isoformat()}",
                "requester": {
                    "email": f"loadtest.{uuid.uuid4().hex[:8]}@example.com",
                    "name": f"TestUser{random.randint(1, 1000)}"
                },
                "priority": random.choice(priorities),
                "tags": ["load-test", random.choice(["api", "ui", "performance"])],
                "custom_fields": {
                    "environment": random.choice(["production", "staging"]),
                    "browser": random.choice(["Chrome", "Firefox", "Safari"])
                }
            },
            "options": {
                "send_notification": False,
                "auto_assign": True
            }
        }
        
        with self.client.post(
            "/api/v1/helpdesk/tickets",
            json=ticket_data,
            headers=APIHeaders.get_headers(include_idempotency=True),
            catch_response=True,
            name="Helpdesk: Create Ticket"
        ) as response:
            if response.status_code in [200, 201]:
                result = response.json()
                if "result" in result and "id" in result["result"]:
                    self.ticket_ids.append(result["result"]["id"])
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @tag("helpdesk", "read")
    @task(12)
    def search_tickets(self):
        """Search for tickets"""
        params = {
            "status": random.choice(["open", "pending", "solved"]),
            "priority": random.choice(["high", "urgent", "normal"]),
            "limit": 20
        }
        
        self.client.get(
            "/api/v1/helpdesk/tickets/search",
            params=params,
            headers=APIHeaders.get_headers(),
            name="Helpdesk: Search Tickets"
        )
    
    @tag("helpdesk", "update")
    @task(5)
    def add_ticket_comment(self):
        """Add comment to a ticket"""
        if not self.ticket_ids:
            raise RescheduleTask()
        
        ticket_id = random.choice(self.ticket_ids)
        comment_data = {
            "idempotency_key": f"idm_comment_{uuid.uuid4()}",
            "correlation_id": f"cor_comment_{int(time.time())}",
            "comment": {
                "body": f"Load test comment at {datetime.utcnow().isoformat()}",
                "is_public": False,
                "author": {
                    "type": "agent",
                    "id": "agent_loadtest_001"
                }
            }
        }
        
        self.client.post(
            f"/api/v1/helpdesk/tickets/{ticket_id}/comments",
            json=comment_data,
            headers=APIHeaders.get_headers(include_idempotency=True),
            name="Helpdesk: Add Comment"
        )
    
    @tag("helpdesk", "update")
    @task(3)
    def update_ticket_status(self):
        """Update ticket status"""
        if not self.ticket_ids:
            raise RescheduleTask()
        
        ticket_id = random.choice(self.ticket_ids)
        update_data = {
            "idempotency_key": f"idm_update_{uuid.uuid4()}",
            "correlation_id": f"cor_update_{int(time.time())}",
            "updates": {
                "status": random.choice(["pending", "solved"]),
                "tags": ["updated", "load-test"]
            }
        }
        
        self.client.patch(
            f"/api/v1/helpdesk/tickets/{ticket_id}",
            json=update_data,
            headers=APIHeaders.get_headers(include_idempotency=True),
            name="Helpdesk: Update Status"
        )


class WorkflowTasks(TaskSet):
    """Workflow execution tasks"""
    
    @tag("workflow", "execute")
    @task(5)
    def execute_workflow(self):
        """Execute a workflow"""
        workflow_data = {
            "idempotency_key": f"idm_workflow_{uuid.uuid4()}",
            "correlation_id": f"cor_workflow_{int(time.time())}",
            "workflow_id": random.choice([
                "lead_qualification",
                "support_triage",
                "ops_monitoring"
            ]),
            "input": {
                "email": f"loadtest.{uuid.uuid4().hex[:8]}@example.com",
                "company": f"TestCompany{random.randint(1, 100)}",
                "priority": random.choice(["normal", "high"])
            },
            "options": {
                "timeout": 30,
                "retry_on_failure": True
            }
        }
        
        self.client.post(
            "/api/v1/workflows/execute",
            json=workflow_data,
            headers=APIHeaders.get_headers(include_idempotency=True),
            name="Workflow: Execute"
        )
    
    @tag("workflow", "read")
    @task(8)
    def list_workflows(self):
        """List available workflows"""
        self.client.get(
            "/api/v1/workflows",
            headers=APIHeaders.get_headers(),
            name="Workflow: List"
        )


class KnowledgeTasks(TaskSet):
    """Knowledge base operations tasks"""
    
    @tag("knowledge", "search")
    @task(10)
    def search_knowledge(self):
        """Search knowledge base"""
        queries = [
            "How do I reset my password?",
            "API authentication",
            "Rate limiting",
            "Integration guide",
            "Troubleshooting errors"
        ]
        
        search_data = {
            "correlation_id": f"cor_kb_{int(time.time())}",
            "query": {
                "text": random.choice(queries),
                "filters": {
                    "published_only": True
                },
                "options": {
                    "max_results": 5,
                    "min_score": 0.7,
                    "include_snippets": True
                }
            }
        }
        
        self.client.post(
            "/api/v1/knowledge/search",
            json=search_data,
            headers=APIHeaders.get_headers(),
            name="Knowledge: Search"
        )


class AdminTasks(TaskSet):
    """Admin operations tasks"""
    
    @tag("admin", "logs")
    @task(3)
    def query_logs(self):
        """Query audit logs"""
        params = {
            "limit": 50,
            "operation": random.choice(["crm.contact.create", "helpdesk.ticket.create"]),
            "status": "success"
        }
        
        self.client.get(
            "/api/v1/logs/audit",
            params=params,
            headers=APIHeaders.get_headers(),
            name="Admin: Query Logs"
        )


class AdapterUser(HttpUser):
    """
    Simulated user for the Transform Army AI Adapter Service
    
    This user simulates realistic behavior patterns including:
    - Think time between requests (1-5 seconds)
    - Mixed workload across different endpoints
    - Realistic error handling
    """
    
    wait_time = between(1, 5)  # Think time between tasks
    
    # Task weight distribution (realistic usage patterns)
    tasks = {
        HealthCheckTasks: 1,      # 5% - Monitoring
        CRMTasks: 8,              # 40% - CRM operations
        HelpdeskTasks: 6,         # 30% - Support tickets
        WorkflowTasks: 3,         # 15% - Workflow automation
        KnowledgeTasks: 1,        # 5% - Knowledge search
        AdminTasks: 1             # 5% - Admin operations
    }
    
    def on_start(self):
        """Initialize user session"""
        self.tenant_id = f"tenant_{random.randint(1, 10):03d}"
        self.correlation_prefix = f"cor_user_{uuid.uuid4().hex[:8]}"


class ProviderLoadUser(HttpUser):
    """
    Focused load testing for provider integration endpoints
    
    This user specifically tests provider API calls under load to identify
    bottlenecks in external service integrations.
    """
    
    wait_time = between(2, 8)  # Longer wait time for provider calls
    
    @tag("provider", "crm")
    @task(5)
    def crm_provider_operations(self):
        """Test CRM provider under load"""
        # Create contact via provider
        contact_data = {
            "idempotency_key": f"idm_provider_{uuid.uuid4()}",
            "contact": {
                "email": f"provider.{uuid.uuid4().hex[:8]}@example.com",
                "first_name": "Provider",
                "last_name": "Test"
            }
        }
        
        self.client.post(
            "/api/v1/crm/contacts",
            json=contact_data,
            headers=APIHeaders.get_headers(include_idempotency=True),
            name="Provider: CRM Create"
        )
    
    @tag("provider", "helpdesk")
    @task(3)
    def helpdesk_provider_operations(self):
        """Test helpdesk provider under load"""
        ticket_data = {
            "idempotency_key": f"idm_provider_{uuid.uuid4()}",
            "ticket": {
                "subject": "Provider load test",
                "description": "Testing provider integration",
                "requester": {
                    "email": f"provider.{uuid.uuid4().hex[:8]}@example.com",
                    "name": "Provider Test"
                },
                "priority": "normal"
            }
        }
        
        self.client.post(
            "/api/v1/helpdesk/tickets",
            json=ticket_data,
            headers=APIHeaders.get_headers(include_idempotency=True),
            name="Provider: Helpdesk Create"
        )


# Event hooks for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print(f"Starting load test at {datetime.utcnow().isoformat()}")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print(f"Load test completed at {datetime.utcnow().isoformat()}")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")