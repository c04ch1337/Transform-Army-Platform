# SDK Examples

> Comprehensive SDK usage examples for Transform Army AI Adapter Service

## Table of Contents

- [Python SDK](#python-sdk)
- [TypeScript SDK](#typescript-sdk)
- [Common Use Cases](#common-use-cases)
- [Best Practices](#best-practices)
- [Error Handling](#error-handling)
- [Retry Logic](#retry-logic)
- [Advanced Patterns](#advanced-patterns)

---

## Python SDK

### Installation

```bash
pip install transform-army-sdk

# Or with optional dependencies
pip install transform-army-sdk[async]
```

### Basic Setup

```python
from transform_army import TransformArmyClient

# Initialize client
client = TransformArmyClient(
    api_key="your_api_key_here",
    base_url="https://api.transform-army.ai"  # Optional, defaults to production
)

# Or with additional configuration
client = TransformArmyClient(
    api_key="your_api_key_here",
    base_url="https://api.transform-army.ai",
    timeout=30,  # Request timeout in seconds
    max_retries=3,  # Maximum retry attempts
    retry_backoff_factor=2.0  # Exponential backoff multiplier
)
```

### Async Client

```python
from transform_army import AsyncTransformArmyClient
import asyncio

async def main():
    async with AsyncTransformArmyClient(
        api_key="your_api_key_here"
    ) as client:
        # Use async methods
        contact = await client.crm.create_contact(
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe"
        )
        print(f"Created contact: {contact.id}")

# Run async code
asyncio.run(main())
```

### CRM Operations

```python
# Create a contact
contact = client.crm.create_contact(
    email="john.doe@example.com",
    first_name="John",
    last_name="Doe",
    company="Acme Corp",
    phone="+1-555-0123",
    metadata={
        "source": "website",
        "campaign": "spring-2025"
    }
)
print(f"Contact created: {contact.id}")
print(f"Provider: {contact.provider}")
print(f"URL: {contact.url}")

# Update a contact
updated_contact = client.crm.update_contact(
    contact_id=contact.id,
    updates={
        "title": "VP of Sales",
        "phone": "+1-555-0199"
    },
    metadata={
        "updated_by": "automation"
    }
)

# Search contacts
results = client.crm.search_contacts(
    query="john doe",
    filters={
        "company": "Acme Corp",
        "created_after": "2025-01-01"
    },
    limit=10
)

for match in results.matches:
    print(f"{match.first_name} {match.last_name} - {match.company}")
    print(f"  Score: {match.score}")
    print(f"  URL: {match.url}")

# Pagination
page = 1
while results.pagination.has_next:
    results = client.crm.search_contacts(
        query="john",
        limit=10,
        offset=page * 10
    )
    page += 1
    for match in results.matches:
        print(f"Contact: {match.email}")

# Add note to contact
note = client.crm.add_note(
    contact_id=contact.id,
    note_text="Initial qualification call completed. Customer interested in enterprise plan.",
    note_type="call_note",
    metadata={
        "call_duration": 1800,
        "outcome": "qualified"
    }
)
print(f"Note added: {note.id}")
```

### Helpdesk Operations

```python
# Create a support ticket
ticket = client.helpdesk.create_ticket(
    subject="Integration help needed",
    description="Having issues with API rate limiting. Need guidance on best practices.",
    priority="high",
    requester_email="customer@example.com",
    tags=["api", "rate-limiting", "urgent"]
)
print(f"Ticket created: {ticket.id}")
print(f"Status: {ticket.status}")
print(f"URL: {ticket.url}")

# Search tickets
tickets = client.helpdesk.search_tickets(
    status="open",
    priority="high",
    limit=20
)

for ticket in tickets.results:
    print(f"{ticket.id}: {ticket.subject}")
    print(f"  Priority: {ticket.priority}")
    print(f"  Created: {ticket.created_at}")

# Add comment to ticket
comment = client.helpdesk.add_comment(
    ticket_id=ticket.id,
    comment_text="Thanks for reaching out. I'll review your integration and get back to you within 2 hours.",
    is_public=True
)

# Update ticket status
client.helpdesk.update_ticket(
    ticket_id=ticket.id,
    updates={
        "status": "pending",
        "priority": "normal"
    }
)
```

### Calendar Operations

```python
from datetime import datetime, timedelta

# Check availability
start_time = datetime.now() + timedelta(days=1)
end_time = start_time + timedelta(hours=8)

availability = client.calendar.check_availability(
    calendar_id="primary",
    start_time=start_time,
    end_time=end_time,
    duration_minutes=30
)

print("Available slots:")
for slot in availability.available_slots:
    print(f"  {slot.start_time} - {slot.end_time}")

# Create calendar event
event = client.calendar.create_event(
    calendar_id="primary",
    summary="Product Demo with Acme Corp",
    description="Demonstrate key features for enterprise account",
    start_time=start_time,
    end_time=start_time + timedelta(hours=1),
    attendees=["john.doe@acme.com", "jane.smith@acme.com"],
    location="Zoom Meeting",
    timezone="America/New_York"
)
print(f"Event created: {event.id}")
print(f"URL: {event.url}")

# Get event
event = client.calendar.get_event(
    calendar_id="primary",
    event_id=event.id
)

# Update event
client.calendar.update_event(
    calendar_id="primary",
    event_id=event.id,
    updates={
        "summary": "Modified: Product Demo",
        "location": "Microsoft Teams"
    }
)

# Delete event
client.calendar.delete_event(
    calendar_id="primary",
    event_id=event.id
)
```

### Email Operations

```python
# Send email
email = client.email.send(
    to="customer@example.com",
    subject="Welcome to Transform Army AI",
    body="""
    Thank you for signing up!
    
    Here's how to get started:
    1. Set up your API key
    2. Configure your first integration
    3. Start automating your workflows
    
    Best regards,
    Transform Army Team
    """,
    cc=["manager@example.com"],
    attachments=[]
)
print(f"Email sent: {email.id}")

# Send with HTML
email = client.email.send(
    to="customer@example.com",
    subject="Welcome Email",
    body_html="""
    <html>
      <body>
        <h1>Welcome!</h1>
        <p>Thank you for signing up.</p>
      </body>
    </html>
    """,
    body_text="Welcome! Thank you for signing up."  # Fallback
)

# Search emails
results = client.email.search(
    query="subject:meeting from:john@example.com",
    limit=10
)

for email in results.results:
    print(f"{email.from_address}: {email.subject}")
    print(f"  Received: {email.received_at}")
    print(f"  Snippet: {email.snippet}")

# Get email by ID
email = client.email.get(email_id="email_abc123")
print(f"Subject: {email.subject}")
print(f"Body: {email.body}")
```

### Knowledge Base Operations

```python
# Search knowledge base
results = client.knowledge.search(
    query="how to integrate webhooks",
    limit=5,
    filters={
        "category": "api-integration"
    }
)

for result in results.results:
    print(f"{result.title} (score: {result.score})")
    print(f"  URL: {result.url}")
    print(f"  Content: {result.content[:100]}...")

# Index document
doc = client.knowledge.index_document(
    title="Webhook Integration Guide",
    content="Webhooks allow you to receive real-time notifications...",
    metadata={
        "category": "api-integration",
        "author": "docs-team",
        "version": "1.0"
    }
)
print(f"Document indexed: {doc.id}")

# Update document
client.knowledge.update_document(
    document_id=doc.id,
    updates={
        "content": "Updated content...",
        "version": "1.1"
    }
)

# Delete document
client.knowledge.delete_document(doc.id)
```

### Workflow Operations

```python
# Create workflow
workflow = client.workflows.create(
    name="Lead Qualification Workflow",
    description="Automated lead qualification and routing",
    definition={
        "steps": [
            {
                "name": "enrich_lead",
                "agent_id": "research-agent",
                "agent_type": "research",
                "timeout": 60
            },
            {
                "name": "qualify_lead",
                "agent_id": "bdr-agent",
                "agent_type": "bdr",
                "timeout": 120
            }
        ]
    },
    is_active=True
)
print(f"Workflow created: {workflow.id}")

# Execute workflow
execution = client.workflows.execute(
    workflow_id=workflow.id,
    input_data={
        "lead_email": "prospect@example.com",
        "lead_company": "Acme Corp"
    }
)
print(f"Execution started: {execution.execution_id}")
print(f"Status: {execution.status}")

# Poll for completion
import time
while execution.status == "running":
    time.sleep(5)
    execution = client.workflows.get_execution(execution.execution_id)
    print(f"Status: {execution.status}")

if execution.status == "completed":
    print("Workflow completed successfully!")
    print(f"Results: {execution.results}")
else:
    print(f"Workflow failed: {execution.error}")

# List workflows
workflows = client.workflows.list(is_active=True)
for workflow in workflows.results:
    print(f"{workflow.name}: {workflow.description}")
```

---

## TypeScript SDK

### Installation

```bash
npm install @transform-army/sdk
# or
yarn add @transform-army/sdk
# or
pnpm add @transform-army/sdk
```

### Basic Setup

```typescript
import { TransformArmyClient } from '@transform-army/sdk';

// Initialize client
const client = new TransformArmyClient({
  apiKey: 'your_api_key_here',
  baseUrl: 'https://api.transform-army.ai', // Optional
});

// With additional configuration
const client = new TransformArmyClient({
  apiKey: 'your_api_key_here',
  baseUrl: 'https://api.transform-army.ai',
  timeout: 30000, // Request timeout in milliseconds
  maxRetries: 3,
  retryBackoffFactor: 2.0,
});
```

### CRM Operations

```typescript
// Create a contact
const contact = await client.crm.createContact({
  email: 'john.doe@example.com',
  firstName: 'John',
  lastName: 'Doe',
  company: 'Acme Corp',
  phone: '+1-555-0123',
  metadata: {
    source: 'website',
    campaign: 'spring-2025',
  },
});

console.log(`Contact created: ${contact.id}`);
console.log(`Provider: ${contact.provider}`);

// Update contact
const updatedContact = await client.crm.updateContact({
  contactId: contact.id,
  updates: {
    title: 'VP of Sales',
    phone: '+1-555-0199',
  },
});

// Search contacts
const results = await client.crm.searchContacts({
  query: 'john doe',
  filters: {
    company: 'Acme Corp',
    created_after: '2025-01-01',
  },
  limit: 10,
});

for (const match of results.matches) {
  console.log(`${match.firstName} ${match.lastName} - ${match.company}`);
  console.log(`  Score: ${match.score}`);
}

// Pagination with async iteration
for await (const contact of client.crm.iterateContacts({ query: 'john' })) {
  console.log(`Contact: ${contact.email}`);
}

// Add note
const note = await client.crm.addNote({
  contactId: contact.id,
  noteText: 'Initial qualification call completed.',
  noteType: 'call_note',
  metadata: {
    callDuration: 1800,
    outcome: 'qualified',
  },
});
```

### Helpdesk Operations

```typescript
// Create ticket
const ticket = await client.helpdesk.createTicket({
  subject: 'Integration help needed',
  description: 'Having issues with API rate limiting.',
  priority: 'high',
  requesterEmail: 'customer@example.com',
  tags: ['api', 'rate-limiting', 'urgent'],
});

console.log(`Ticket created: ${ticket.id}`);

// Search tickets
const tickets = await client.helpdesk.searchTickets({
  status: 'open',
  priority: 'high',
  limit: 20,
});

// Add comment
const comment = await client.helpdesk.addComment({
  ticketId: ticket.id,
  commentText: "I'll review your integration and get back to you.",
  isPublic: true,
});

// Update ticket
await client.helpdesk.updateTicket({
  ticketId: ticket.id,
  updates: {
    status: 'pending',
    priority: 'normal',
  },
});
```

### Calendar Operations

```typescript
// Check availability
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
tomorrow.setHours(9, 0, 0, 0);

const endTime = new Date(tomorrow);
endTime.setHours(17, 0, 0, 0);

const availability = await client.calendar.checkAvailability({
  calendarId: 'primary',
  startTime: tomorrow,
  endTime: endTime,
  durationMinutes: 30,
});

console.log('Available slots:');
for (const slot of availability.availableSlots) {
  console.log(`  ${slot.startTime} - ${slot.endTime}`);
}

// Create event
const event = await client.calendar.createEvent({
  calendarId: 'primary',
  summary: 'Product Demo with Acme Corp',
  description: 'Demonstrate key features',
  startTime: tomorrow,
  endTime: new Date(tomorrow.getTime() + 3600000), // +1 hour
  attendees: ['john.doe@acme.com', 'jane.smith@acme.com'],
  location: 'Zoom Meeting',
  timezone: 'America/New_York',
});

console.log(`Event created: ${event.id}`);
```

### Email Operations

```typescript
// Send email
const email = await client.email.send({
  to: 'customer@example.com',
  subject: 'Welcome to Transform Army AI',
  body: `
    Thank you for signing up!
    
    Here's how to get started:
    1. Set up your API key
    2. Configure your first integration
    3. Start automating your workflows
  `,
  cc: ['manager@example.com'],
});

// Send with template
const email = await client.email.send({
  to: 'customer@example.com',
  templateId: 'welcome-email',
  templateData: {
    firstName: 'John',
    companyName: 'Acme Corp',
  },
});

// Search emails
const results = await client.email.search({
  query: 'subject:meeting from:john@example.com',
  limit: 10,
});
```

### Knowledge Base Operations

```typescript
// Search knowledge base
const results = await client.knowledge.search({
  query: 'how to integrate webhooks',
  limit: 5,
  filters: {
    category: 'api-integration',
  },
});

for (const result of results.results) {
  console.log(`${result.title} (score: ${result.score})`);
  console.log(`  URL: ${result.url}`);
}

// Index document
const doc = await client.knowledge.indexDocument({
  title: 'Webhook Integration Guide',
  content: 'Webhooks allow you to receive real-time notifications...',
  metadata: {
    category: 'api-integration',
    author: 'docs-team',
  },
});
```

### Workflow Operations

```typescript
// Create workflow
const workflow = await client.workflows.create({
  name: 'Lead Qualification Workflow',
  description: 'Automated lead qualification',
  definition: {
    steps: [
      {
        name: 'enrich_lead',
        agentId: 'research-agent',
        agentType: 'research',
        timeout: 60,
      },
      {
        name: 'qualify_lead',
        agentId: 'bdr-agent',
        agentType: 'bdr',
        timeout: 120,
      },
    ],
  },
  isActive: true,
});

// Execute workflow
const execution = await client.workflows.execute({
  workflowId: workflow.id,
  inputData: {
    leadEmail: 'prospect@example.com',
    leadCompany: 'Acme Corp',
  },
});

// Poll for completion
while (execution.status === 'running') {
  await new Promise((resolve) => setTimeout(resolve, 5000));
  execution = await client.workflows.getExecution(execution.executionId);
  console.log(`Status: ${execution.status}`);
}

if (execution.status === 'completed') {
  console.log('Workflow completed!');
  console.log(`Results: ${JSON.stringify(execution.results)}`);
}
```

---

## Common Use Cases

### 1. Lead Enrichment Pipeline

```python
def enrich_and_qualify_lead(email: str, company: str):
    """Complete lead enrichment and qualification pipeline."""
    
    # Step 1: Create contact in CRM
    contact = client.crm.create_contact(
        email=email,
        company=company,
        metadata={"source": "website", "status": "new_lead"}
    )
    
    # Step 2: Search for additional information
    knowledge_results = client.knowledge.search(
        query=f"{company} company information",
        limit=3
    )
    
    # Step 3: Enrich contact with research data
    enrichment_data = {
        "industry": knowledge_results.results[0].metadata.get("industry"),
        "company_size": knowledge_results.results[0].metadata.get("size"),
        "research_date": datetime.now().isoformat()
    }
    
    client.crm.update_contact(
        contact_id=contact.id,
        updates=enrichment_data
    )
    
    # Step 4: Create qualification task
    ticket = client.helpdesk.create_ticket(
        subject=f"Qualify lead: {contact.first_name} {contact.last_name}",
        description=f"New lead from {company}. Enriched data available.",
        priority="normal",
        tags=["lead-qualification", "new-lead"]
    )
    
    # Step 5: Schedule follow-up
    follow_up_time = datetime.now() + timedelta(days=2)
    event = client.calendar.create_event(
        calendar_id="primary",
        summary=f"Follow-up: {contact.first_name} {contact.last_name}",
        start_time=follow_up_time,
        end_time=follow_up_time + timedelta(minutes=30),
        description=f"Follow up on lead from {company}"
    )
    
    return {
        "contact_id": contact.id,
        "ticket_id": ticket.id,
        "event_id": event.id,
        "status": "qualified"
    }

# Usage
result = enrich_and_qualify_lead(
    email="john.doe@acme.com",
    company="Acme Corp"
)
```

### 2. Customer Support Automation

```typescript
async function automateCustomerSupport(
  requesterEmail: string,
  subject: string,
  description: string
) {
  // Create ticket
  const ticket = await client.helpdesk.createTicket({
    subject,
    description,
    requesterEmail,
    priority: 'normal',
  });

  // Search knowledge base for relevant articles
  const kbResults = await client.knowledge.search({
    query: subject,
    limit: 3,
  });

  // Add helpful articles as internal note
  if (kbResults.results.length > 0) {
    const articles = kbResults.results
      .map((r) => `- ${r.title}: ${r.url}`)
      .join('\n');

    await client.helpdesk.addComment({
      ticketId: ticket.id,
      commentText: `Relevant KB articles:\n${articles}`,
      isPublic: false,
    });
  }

  // Send acknowledgment email
  await client.email.send({
    to: requesterEmail,
    subject: `Re: ${subject}`,
    body: `
      Thank you for contacting support. 
      Your ticket #${ticket.id} has been created.
      
      We'll get back to you within 24 hours.
    `,
  });

  // Find contact in CRM
  const contacts = await client.crm.searchContacts({
    query: requesterEmail,
    limit: 1,
  });

  // Add note to contact if exists  if (contacts.matches.length > 0) {
    await client.crm.addNote({
      contactId: contacts.matches[0].id,
      noteText: `Support ticket created: ${subject}`,
      noteType: 'support_ticket',
      metadata: {
        ticketId: ticket.id,
        priority: 'normal',
      },
    });
  }

  return ticket;
}
```

### 3. Meeting Scheduler with CRM Integration

```python
def schedule_meeting_with_lead(
    contact_email: str,
    meeting_type: str,
    preferred_date: datetime
):
    """Schedule meeting and update CRM."""
    
    # Find contact
    contacts = client.crm.search_contacts(
        query=contact_email,
        limit=1
    )
    
    if not contacts.matches:
        raise ValueError(f"Contact not found: {contact_email}")
    
    contact = contacts.matches[0]
    
    # Check availability
    start_of_day = preferred_date.replace(hour=9, minute=0)
    end_of_day = preferred_date.replace(hour=17, minute=0)
    
    availability = client.calendar.check_availability(
        calendar_id="primary",
        start_time=start_of_day,
        end_time=end_of_day,
        duration_minutes=60
    )
    
    if not availability.available_slots:
        raise ValueError("No available slots on preferred date")
    
    # Book first available slot
    slot = availability.available_slots[0]
    event = client.calendar.create_event(
        calendar_id="primary",
        summary=f"{meeting_type} with {contact.first_name} {contact.last_name}",
        start_time=slot.start_time,
        end_time=slot.end_time,
        attendees=[contact_email],
        description=f"Meeting with {contact.company}"
    )
    
    # Update CRM
    client.crm.add_note(
        contact_id=contact.id,
        note_text=f"Scheduled {meeting_type} for {slot.start_time}",
        note_type="meeting",
        metadata={
            "calendar_event_id": event.id,
            "calendar_url": event.url
        }
    )
    
    # Send confirmation email
    client.email.send(
        to=contact_email,
        subject=f"{meeting_type} Scheduled",
        body=f"""
        Hi {contact.first_name},
        
        Your {meeting_type} has been scheduled for:
        {slot.start_time.strftime('%B %d, %Y at %I:%M %p')}
        
        Calendar invite: {event.url}
        
        Looking forward to speaking with you!
        """
    )
    
    return event
```

---

## Best Practices

### 1. Use Environment Variables

```python
import os

api_key = os.environ.get('TRANSFORM_ARMY_API_KEY')
if not api_key:
    raise ValueError("TRANSFORM_ARMY_API_KEY environment variable not set")

client = TransformArmyClient(api_key=api_key)
```

### 2. Implement Proper Error Handling

```python
from transform_army.exceptions import (
    TransformArmyError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    ProviderError
)

try:
    contact = client.crm.create_contact(
        email="john@example.com",
        first_name="John"
    )
except AuthenticationError as e:
    print("Authentication failed: Check your API key")
    print(f"Correlation ID: {e.correlation_id}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
    time.sleep(e.retry_after)
    # Retry request
except ValidationError as e:
    print(f"Validation error: {e.message}")
    print(f"Field: {e.field}")
    print(f"Details: {e.details}")
except ProviderError as e:
    print(f"Provider error: {e.provider}")
    print(f"Message: {e.message}")
except TransformArmyError as e:
    print(f"API error: {e.message}")
    print(f"Correlation ID: {e.correlation_id}")
```

### 3. Use Context Managers

```python
# Automatic connection cleanup
with TransformArmyClient(api_key="your_key") as client:
    contact = client.crm.create_contact(
        email="john@example.com"
    )
    # Client automatically closed after block

# Async context manager
async with AsyncTransformArmyClient(api_key="your_key") as client:
    contact = await client.crm.create_contact(
        email="john@example.com"
    )
```

### 4. Implement Logging

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SDK supports logging
client = TransformArmyClient(
    api_key="your_key",
    logger=logger  # Pass custom logger
)

# Log operations
logger.info("Creating contact")
contact = client.crm.create_contact(email="john@example.com")
logger.info(f"Contact created: {contact.id}")
```

### 5. Use Batch Operations

```python
# Instead of multiple single requests
contacts = []
for email in email_list:
    contact = client.crm.create_contact(email=email)
    contacts.append(contact)

# Use batch operations
contacts = client.crm.create_contacts_batch(
    [{"email": email} for email in email_list]
)
```

---

## Error Handling

### Comprehensive Error Handling Pattern

```python
from transform_army import TransformArmyClient
from transform_army.exceptions import *
import time
import logging

logger = logging.getLogger(__name__)

def create_contact_with_retry(email: str, max_retries: int = 3):
    """Create contact with comprehensive error handling."""
    
    client = TransformArmyClient(api_key=os.environ['TRANSFORM_ARMY_API_KEY'])
    
    for attempt in range(max_retries):
        try:
            contact = client.crm.create_contact(
                email=email,
                metadata={"attempt": attempt + 1}
            )
            
            logger.info(f"Contact created successfully: {contact.id}")
            return contact
            
        except AuthenticationError as e:
            # Don't retry on auth errors
            logger.error(f"Authentication failed: {e.message}")
            logger.error(f"Correlation ID: {e.correlation_id}")
            raise
            
        except ValidationError as e:
            # Don't retry on validation errors
            logger.error(f"Validation error: {e.message}")
            logger.error(f"Field: {e.field}, Issue: {e.details}")
            raise
            
        except RateLimitError as e:
            # Wait and retry on rate limits
            wait_time = e.retry_after or (2 ** attempt)
            logger.warning(f"Rate limited. Waiting {wait_time}s before retry")
            time.sleep(wait_time)
            continue
            
        except ProviderError as e:
            # Retry on provider errors
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(
                    f"Provider error ({e.provider}). "
                    f"Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Provider error after {max_retries} attempts: {e.message}")
                raise
                
        except NetworkError as e:
            # Retry on network errors
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Network error. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Network error after {max_retries} attempts")
                raise
                
        except TransformArmyError as e:
            # Generic error handling
            logger.error(f"API error: {e.message}")
            logger.error(f"Correlation ID: {e.correlation_id}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                raise
    
    raise Exception(f"Failed to create contact after {max_retries} attempts")
```

### TypeScript Error Handling

```typescript
import {
  TransformArmyClient,
  TransformArmyError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  ProviderError,
} from '@transform-army/sdk';

async function createContactWithRetry(
  email: string,
  maxRetries: number = 3
): Promise<Contact> {
  const client = new TransformArmyClient({
    apiKey: process.env.TRANSFORM_ARMY_API_KEY!,
  });

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const contact = await client.crm.createContact({
        email,
        metadata: { attempt: attempt + 1 },
      });

      console.log(`Contact created successfully: ${contact.id}`);
      return contact;
    } catch (error) {
      if (error instanceof AuthenticationError) {
        // Don't retry on auth errors
        console.error(`Authentication failed: ${error.message}`);
        console.error(`Correlation ID: ${error.correlationId}`);
        throw error;
      } else if (error instanceof ValidationError) {
        // Don't retry on validation errors
        console.error(`Validation error: ${error.message}`);
        console.error(`Field: ${error.field}, Details: ${error.details}`);
        throw error;
      } else if (error instanceof RateLimitError) {
        // Wait and retry on rate limits
        const waitTime = error.retryAfter || 2 ** attempt;
        console.warn(`Rate limited. Waiting ${waitTime}s before retry`);
        await new Promise((resolve) => setTimeout(resolve, waitTime * 1000));
        continue;
      } else if (error instanceof ProviderError) {
        // Retry on provider errors
        if (attempt < maxRetries - 1) {
          const waitTime = 2 ** attempt;
          console.warn(
            `Provider error (${error.provider}). Retrying in ${waitTime}s...`
          );
          await new Promise((resolve) => setTimeout(resolve, waitTime * 1000));
          continue;
        } else {
          console.error(
            `Provider error after ${maxRetries} attempts: ${error.message}`
          );
          throw error;
        }
      } else if (error instanceof TransformArmyError) {
        // Generic error handling
        console.error(`API error: ${error.message}`);
        console.error(`Correlation ID: ${error.correlationId}`);

        if (attempt < maxRetries - 1) {
          const waitTime = 2 ** attempt;
          console.log(`Retrying in ${waitTime}s...`);
          await new Promise((resolve) => setTimeout(resolve, waitTime * 1000));
          continue;
        } else {
          throw error;
        }
      } else {
        throw error;
      }
    }
  }

  throw new Error(`Failed to create contact after ${maxRetries} attempts`);
}
```

---

## Retry Logic

### Exponential Backoff with Jitter

```python
import random
import time
from typing import Callable, TypeVar, Any

T = TypeVar('T')

def exponential_backoff_retry(
    func: Callable[[], T],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> T:
    """
    Execute function with exponential backoff retry logic.
    
    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        jitter: Add random jitter to prevent thundering herd
    
    Returns:
        Result from successful function execution
    """
    for attempt in range(max_retries):
        try:
            return func()
        except (RateLimitError, ProviderError, NetworkError) as e:
            if attempt == max_retries - 1:
                raise
            
            # Calculate exponential backoff
            delay = min(base_delay * (2 ** attempt), max_delay)
            
            # Add jitter
            if jitter:
                delay = delay * (0.5 + random.random())
            
            logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s")
            time.sleep(delay)
    
    raise Exception(f"Max retries ({max_retries}) exceeded")

# Usage
contact = exponential_backoff_retry(
    lambda: client.crm.create_contact(email="john@example.com"),
    max_retries=5
)
```

### Circuit Breaker Pattern

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker closed after successful call")
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

# Usage
breaker = CircuitBreaker(failure_threshold=5, timeout=60)

try:
    contact = breaker.call(
        client.crm.create_contact,
        email="john@example.com"
    )
except Exception as e:
    logger.error(f"Request failed: {e}")
```

---

## Advanced Patterns

### Request Batching

```python
from collections import defaultdict
from typing import List, Dict
import asyncio

class BatchProcessor:
    def __init__(self, client: TransformArmyClient, batch_size: int = 50):
        self.client = client
        self.batch_size = batch_size
        self.pending_requests = []
    
    def add_request(self, operation: str, **kwargs):
        """Add request to batch."""
        self.pending_requests.append({
            "operation": operation,
            "params": kwargs
        })
        
        if len(self.pending_requests) >= self.batch_size:
            return self.flush()
    
    def flush(self):
        """Execute all pending requests."""
        if not self.pending_requests:
            return []
        
        # Group by operation type
        grouped = defaultdict(list)
        for req in self.pending_requests:
            grouped[req["operation"]].append(req["params"])
        
        results = []
        for operation, params_list in grouped.items():
            if operation == "create_contact":
                batch_results = self.client.crm.create_contacts_batch(params_list)
                results.extend(batch_results)
        
        self.pending_requests = []
        return results

# Usage
processor = BatchProcessor(client)

for email in email_list:
    processor.add_request("create_contact", email=email, company="Acme Corp")

# Flush remaining
results = processor.flush()
```

### Caching Layer

```python
from functools import lru_cache
from datetime import datetime, timedelta
import hashlib
import json

class CachedClient:
    def __init__(self, client: TransformArmyClient, cache_ttl: int = 300):
        self.client = client
        self.cache_ttl = cache_ttl
        self.cache = {}
    
    def _cache_key(self, method: str, **kwargs) -> str:
        """Generate cache key from method and parameters."""
        params_str = json.dumps(kwargs, sort_keys=True)
        return hashlib.md5(f"{method}:{params_str}".encode()).hexdigest()
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cache entry is still valid."""
        return datetime.now() - timestamp < timedelta(seconds=self.cache_ttl)
    
    def search_contacts(self, **kwargs):
        """Search contacts with caching."""
        cache_key = self._cache_key("search_contacts", **kwargs)
        
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp):
                logger.debug(f"Cache hit for {cache_key}")
                return result
        
        # Cache miss - fetch from API
        logger.debug(f"Cache miss for {cache_key}")
        result = self.client.crm.search_contacts(**kwargs)
        self.cache[cache_key] = (result, datetime.now())
        
        return result
    
    def invalidate_cache(self):
        """Clear all cache entries."""
        self.cache = {}

# Usage
cached_client = CachedClient(client, cache_ttl=300)

# First call - cache miss
results1 = cached_client.search_contacts(query="john", limit=10)

# Second call - cache hit
results2 = cached_client.search_contacts(query="john", limit=10)
```

---

*Last Updated: 2025-10-31* | *SDK Version: 1.0.0*