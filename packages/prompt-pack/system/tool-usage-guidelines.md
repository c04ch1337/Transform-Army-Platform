# Tool Usage Guidelines

**Version:** 1.0.0  
**Last Updated:** 2025-10-31

---

## Overview

This document provides comprehensive guidelines for agent tool usage, including when to use each tool, parameter validation, error recovery, idempotency considerations, and rate limiting awareness.

---

## General Tool Principles

### 1. Tool Selection Criteria

**Use the Right Tool:**
- Match tool capabilities to task requirements
- Choose simplest tool that accomplishes the goal
- Consider cost and performance implications
- Respect tool limitations and constraints

**Decision Framework:**
```
IF need_to_read_data:
    use_read_tool (crm.read, helpdesk.read, knowledge.search)
ELIF need_to_write_data:
    verify_authorization
    use_write_tool (crm.create, crm.update, email.send)
ELIF need_external_info:
    use_search_tool (web.search, data.lookup)
ELIF need_to_notify:
    use_notification_tool (slack.notify, email.send)
```

---

## Tool Categories

### CRM Tools

**crm.contacts.search**
```
Purpose: Find existing contacts
When to use: Before creating new contact, during lead qualification
Parameters:
  - query: email (primary), name+company, phone
  - limit: max results (default: 10)
Best practices:
  - Always search by email first (most unique)
  - Use fuzzy matching for names
  - Verify results before using
Error handling: Empty results are normal, not an error
```

**crm.contacts.create**
```
Purpose: Create new contact record
When to use: After confirming no duplicate exists
Parameters:
  - email: required, validated format
  - first_name, last_name: required
  - company: required
  - Additional fields per schema
Best practices:
  - Validate email format before calling
  - Normalize company names
  - Check for duplicates first
Error handling: Duplicate email → Update instead
Idempotency: Check for existing before creating
```

**crm.notes.add**
```
Purpose: Add note to contact/deal
When to use: Document interactions, decisions, next steps
Parameters:
  - contact_id or deal_id: required
  - note_text: required, formatted
  - timestamp: auto-added
Best practices:
  - Use structured note format
  - Include context and reasoning
  - Reference related entities
Error handling: Retry once on failure
Idempotency: Include unique reference in note
```

### Helpdesk Tools

**helpdesk.tickets.read**
```
Purpose: Retrieve ticket details
When to use: Before responding, during triage
Parameters:
  - ticket_id: required
  - include: comments, history (optional)
Best practices:
  - Cache ticket data (5 min TTL)
  - Include conversation history
  - Check for recent updates
Error handling: Not found → Verify ID, escalate
Rate limit: 100 req/min per tenant
```

**helpdesk.comments.add**
```
Purpose: Add public or private comment
When to use: Providing solution, internal notes
Parameters:
  - ticket_id: required
  - body: required, HTML or plaintext
  - public: true/false
Best practices:
  - Format with proper structure
  - Use public for customer-facing
  - Use private for internal notes
Error handling: Retry with exponential backoff
Idempotency: Generate idempotency key
```

**helpdesk.tickets.update**
```
Purpose: Update ticket status, priority, assignment
When to use: After triage, escalation, resolution
Parameters:
  - ticket_id: required
  - status, priority, assignee: as needed
Best practices:
  - Only update changed fields
  - Add comment explaining change
  - Verify permissions
Error handling: Conflict → Reload and retry
Idempotency: Use version/etag if available
```

### Calendar Tools

**calendar.availability.find**
```
Purpose: Find available meeting slots
When to use: Before booking meetings
Parameters:
  - user_email: whose calendar to check
  - start_date, end_date: search window
  - duration: meeting length (minutes)
Best practices:
  - Check multiple time zones
  - Offer 3+ options
  - Respect business hours
Error handling: No availability → Extend window
Rate limit: 20 req/min
```

**calendar.events.create**
```
Purpose: Book calendar event
When to use: After confirming availability
Parameters:
  - title, description: required
  - start_time, end_time: ISO 8601
  - attendees: email list
  - location: physical or video URL
Best practices:
  - Include agenda in description
  - Add video conference link
  - Set reminder (15 min default)
Error handling: Conflict → Find new time
Idempotency: Check for existing event first
```

### Knowledge Base Tools

**knowledge.search**
```
Purpose: Semantic search for articles
When to use: Answering questions, finding solutions
Parameters:
  - query: natural language question
  - limit: max results (default: 5)
  - filters: category, tags (optional)
Best practices:
  - Use customer's exact question
  - Include error messages in query
  - Check confidence scores
Error handling: Low confidence → Try broader query
Caching: Cache results (1 hour)
```

**knowledge.articles.create**
```
Purpose: Create new knowledge article
When to use: Filling content gaps, documenting solutions
Parameters:
  - title, content: required
  - category, tags: required
  - metadata: author, audience, etc.
Best practices:
  - Use article templates
  - Generate embeddings immediately
  - Set status to draft initially
Error handling: Validation errors → Fix and retry
Idempotency: Check title uniqueness
```

### Communication Tools

**email.send**
```
Purpose: Send email to customers/internal
When to use: Follow-ups, notifications, confirmations
Parameters:
  - to: email address(es)
  - subject, body: required
  - template_id: optional (preferred)
Best practices:
  - Use templates when possible
  - Validate email addresses
  - Track sending for audit
Error handling: Bounce → Update contact status
Rate limit: 50 sends/min
Idempotency: Track message ID
```

**slack.notify**
```
Purpose: Send Slack notifications
When to use: Alerts, escalations, status updates
Parameters:
  - channel: #channel-name or @user
  - message: formatted text
  - priority: normal, urgent
Best practices:
  - Use thread replies for updates
  - @ mention for urgent items
  - Include context and links
Error handling: Retry 3x with backoff
Rate limit: 1 msg/second per channel
```

---

## Parameter Validation

### Before Calling Any Tool

**Required Checks:**
```python
def validate_tool_parameters(tool_name, params):
    # 1. Check all required parameters present
    required = get_required_params(tool_name)
    for param in required:
        if param not in params or params[param] is None:
            raise MissingParameterError(f"{param} is required")
    
    # 2. Validate data types
    schema = get_parameter_schema(tool_name)
    for param, value in params.items():
        expected_type = schema[param]["type"]
        if not isinstance(value, expected_type):
            raise TypeError(f"{param} must be {expected_type}")
    
    # 3. Validate formats (email, phone, dates)
    if "email" in params:
        if not is_valid_email(params["email"]):
            raise ValidationError("Invalid email format")
    
    # 4. Check value ranges/constraints
    if "limit" in params and params["limit"] > 100:
        raise ValidationError("Limit cannot exceed 100")
    
    return True
```

### Common Validation Rules

**Email Addresses:**
- Format: RFC 5322 compliant
- Check: Not disposable domain
- Normalize: Lowercase

**Phone Numbers:**
- Format: E.164 international (preferred)
- Clean: Remove formatting characters
- Validate: Length and country code

**Dates/Times:**
- Format: ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- Timezone: Always UTC or explicit timezone
- Validation: Not in past (for future events)

**IDs and References:**
- Format: Match expected pattern
- Existence: Verify referenced entity exists
- Permissions: Confirm access authorized

---

## Error Recovery

### Retry Strategy

**Transient Errors (Retry):**
```python
@retry(
    max_attempts=3,
    backoff=exponential(base=2),  # 2s, 4s, 8s
    retry_on=[TimeoutError, RateLimitError, ServiceUnavailable]
)
def call_tool(tool_name, params):
    return execute_tool(tool_name, params)
```

**When to Retry:**
- Network timeouts
- Rate limit errors (with delay)
- 5xx server errors
- Temporary unavailability

**When NOT to Retry:**
- 4xx client errors (bad request)
- Authentication failures
- Permission denied
- Validation errors
- Resource not found

### Fallback Strategies

**If Primary Tool Fails:**
```python
try:
    result = primary_tool.execute(params)
except ToolUnavailableError:
    # Try alternate provider
    result = fallback_tool.execute(params)
except ToolError as e:
    # Degrade gracefully
    log_error(e)
    return partial_result_with_caveats()
```

**Graceful Degradation:**
- Complete what you can
- Document what failed
- Provide workarounds
- Set expectations

---

## Idempotency Considerations

### Why Idempotency Matters

**Problem:** Network failures can cause duplicate operations
**Solution:** Ensure operations can be safely retried

### Idempotent Operations

**Naturally Idempotent:**
- Read operations (GET)
- Search operations
- Query operations

**Require Idempotency Keys:**
- Create operations (POST)
- Update operations (PUT/PATCH)
- Delete operations (DELETE)

### Implementation

**For Create Operations:**
```python
def create_contact(email, data, idempotency_key=None):
    # Check if already created with this key
    if idempotency_key:
        existing = check_idempotency_key(idempotency_key)
        if existing:
            return existing
    
    # Check for duplicate by email
    existing = search_contact_by_email(email)
    if existing:
        # Update instead of create
        return update_contact(existing.id, data)
    
    # Create new
    contact = crm.contacts.create(data)
    
    # Store idempotency key
    if idempotency_key:
        store_idempotency_key(idempotency_key, contact.id)
    
    return contact
```

**Idempotency Key Generation:**
```python
import hashlib

def generate_idempotency_key(operation, unique_data):
    # Create unique key from operation + data
    key_input = f"{operation}:{json.dumps(unique_data, sort_keys=True)}"
    return hashlib.sha256(key_input.encode()).hexdigest()

# Example
key = generate_idempotency_key(
    "create_contact",
    {"email": "john@example.com", "timestamp": "2025-10-31T10:00:00Z"}
)
```

---

## Rate Limiting Awareness

### Know Your Limits

**Common Rate Limits:**
```
Service         | Limit           | Window    | Backoff
----------------|-----------------|-----------|----------
CRM API         | 100 req/min     | 1 minute  | 60s
Helpdesk API    | 200 req/min     | 1 minute  | 30s
Email Sending   | 50 sends/min    | 1 minute  | 60s
Slack API       | 1 msg/sec       | 1 second  | 2s
Calendar API    | 20 req/min      | 1 minute  | 60s
Knowledge API   | Unlimited       | -         | -
```

### Rate Limit Handling

**Proactive Management:**
```python
class RateLimiter:
    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = []
    
    def wait_if_needed(self):
        now = time.time()
        # Remove old requests outside window
        self.requests = [r for r in self.requests if now - r < self.window]
        
        if len(self.requests) >= self.max_requests:
            # Wait until oldest request expires
            sleep_time = self.window - (now - self.requests[0])
            time.sleep(sleep_time)
        
        self.requests.append(now)

# Usage
limiter = RateLimiter(max_requests=100, window_seconds=60)
limiter.wait_if_needed()
result = call_api()
```

**Reactive Handling:**
```python
def call_with_rate_limit_handling(tool, params):
    try:
        return tool.execute(params)
    except RateLimitError as e:
        retry_after = e.retry_after_seconds
        log(f"Rate limited, waiting {retry_after}s")
        time.sleep(retry_after)
        return tool.execute(params)  # Retry once
```

### Batch Operations

**When to Batch:**
- Multiple similar operations
- Non-urgent processing
- High-volume data processing

**Batching Strategy:**
```python
def batch_create_contacts(contacts_data, batch_size=50):
    results = []
    
    for i in range(0, len(contacts_data), batch_size):
        batch = contacts_data[i:i + batch_size]
        
        # Create batch request
        batch_result = crm.contacts.batch_create(batch)
        results.extend(batch_result)
        
        # Respect rate limits between batches
        if i + batch_size < len(contacts_data):
            time.sleep(1)  # Rate limit buffer
    
    return results
```

---

## Best Practices Summary

### DO:
✓ Validate parameters before calling tools
✓ Handle errors gracefully with retries
✓ Use idempotency keys for create operations
✓ Respect rate limits proactively
✓ Cache expensive operations
✓ Log all tool uses with correlation IDs
✓ Provide clear error messages
✓ Use appropriate timeout values

### DON'T:
✗ Proceed with invalid parameters
✗ Ignore error responses
✗ Retry indefinitely
✗ Exceed rate limits
✗ Make redundant tool calls
✗ Store sensitive data in logs
✗ Assume operations succeeded
✗ Chain tools without validation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-31 | Initial tool usage guidelines |