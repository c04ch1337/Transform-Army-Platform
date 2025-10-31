# Transform Army AI - Schema

Shared data models and schemas for type-safe communication across the platform.

## Overview

This package provides unified data models for both Python (Pydantic) and TypeScript (Zod), ensuring type safety and validation consistency across the entire platform.

## Philosophy

**Contract-First Design**: Define schemas once, use everywhere.

- API contracts are defined before implementation
- Validation happens at system boundaries
- Types are inferred from schemas
- Breaking changes are caught at compile time

## Directory Structure

```
schema/
├── python/              # Pydantic models
│   ├── requests/       # Request models
│   ├── responses/      # Response models
│   ├── entities/       # Domain entities
│   └── events/         # Event schemas
├── typescript/         # Zod schemas
│   ├── requests/       # Request schemas
│   ├── responses/      # Response schemas
│   ├── entities/       # Domain entities
│   └── events/         # Event schemas
├── package.json        # TypeScript package config
└── requirements.txt    # Python dependencies
```

## Python Schemas (Pydantic)

### Installation

```bash
pip install -r requirements.txt
```

### Usage

```python
from schema.python.requests import CreateContactRequest
from schema.python.responses import ContactResponse

# Validate request
request = CreateContactRequest(
    email="user@example.com",
    first_name="John",
    last_name="Doe"
)

# Type-safe response
response = ContactResponse(
    id="cont_123",
    email=request.email,
    created_at=datetime.now()
)
```

### Example Models

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class CreateContactRequest(BaseModel):
    """Request to create CRM contact."""
    email: EmailStr = Field(..., description="Contact email address")
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@acme.com",
                "first_name": "John",
                "last_name": "Doe",
                "company": "Acme Corp"
            }
        }

class ContactResponse(BaseModel):
    """CRM contact response."""
    id: str = Field(..., description="Unique contact ID")
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }
```

## TypeScript Schemas (Zod)

### Installation

```bash
pnpm install
```

### Usage

```typescript
import { createContactRequestSchema, type CreateContactRequest } from '@/schema/requests';
import { contactResponseSchema, type ContactResponse } from '@/schema/responses';

// Validate request
const request = createContactRequestSchema.parse({
  email: 'user@example.com',
  firstName: 'John',
  lastName: 'Doe'
});

// Type inference
type Request = z.infer<typeof createContactRequestSchema>;
```

### Example Schemas

```typescript
import { z } from 'zod';

export const createContactRequestSchema = z.object({
  email: z.string().email('Invalid email address'),
  firstName: z.string().max(50).optional(),
  lastName: z.string().max(50).optional(),
  company: z.string().max(100).optional(),
});

export type CreateContactRequest = z.infer<typeof createContactRequestSchema>;

export const contactResponseSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  firstName: z.string().optional(),
  lastName: z.string().optional(),
  company: z.string().optional(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export type ContactResponse = z.infer<typeof contactResponseSchema>;
```

## Schema Categories

### Request Models

Validate incoming API requests:
- Parameter validation
- Required field checking
- Format validation
- Business rule enforcement

### Response Models

Type-safe API responses:
- Consistent response structure
- Optional field handling
- Serialization rules
- Documentation generation

### Entity Models

Domain entities and business objects:
- Core business concepts
- Relationship modeling
- State management
- Validation rules

### Event Models

System events and messages:
- Event payload structure
- Event metadata
- Event versioning
- Event routing

## Common Patterns

### Pagination

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
```

### Error Responses

```python
from pydantic import BaseModel
from typing import Optional, List

class ErrorDetail(BaseModel):
    """Error detail information."""
    field: Optional[str] = None
    message: str
    code: str

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    correlation_id: str
```

### Timestamps

```python
from pydantic import BaseModel
from datetime import datetime

class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime
    updated_at: datetime
```

## Schema Validation

### Python Validation

```python
from pydantic import ValidationError

try:
    contact = CreateContactRequest(email="invalid")
except ValidationError as e:
    print(e.json())
    # [{
    #   "type": "value_error.email",
    #   "loc": ["email"],
    #   "msg": "value is not a valid email address"
    # }]
```

### TypeScript Validation

```typescript
import { ZodError } from 'zod';

try {
  const contact = createContactRequestSchema.parse({ email: 'invalid' });
} catch (error) {
  if (error instanceof ZodError) {
    console.log(error.errors);
    // [{
    //   "code": "invalid_string",
    //   "path": ["email"],
    //   "message": "Invalid email address"
    // }]
  }
}
```

## Schema Versioning

Schemas are versioned to support API evolution:

```
schema/
├── python/
│   ├── v1/
│   │   └── requests.py
│   └── v2/
│       └── requests.py
```

Version in URLs:
- `/api/v1/contacts` - Uses v1 schemas
- `/api/v2/contacts` - Uses v2 schemas

## Code Generation

Generate TypeScript from Python:

```bash
# Generate TypeScript types from Pydantic models
pydantic2ts --module schema.python --output schema/typescript/generated
```

Generate OpenAPI specs:

```bash
# Generate OpenAPI from FastAPI
python scripts/generate_openapi.py > openapi.json
```

## Testing

### Python Tests

```python
def test_create_contact_request_validation():
    """Test contact request validation."""
    # Valid request
    request = CreateContactRequest(
        email="test@example.com",
        first_name="Test"
    )
    assert request.email == "test@example.com"
    
    # Invalid email
    with pytest.raises(ValidationError):
        CreateContactRequest(email="invalid")
```

### TypeScript Tests

```typescript
describe('createContactRequestSchema', () => {
  it('validates valid request', () => {
    const result = createContactRequestSchema.safeParse({
      email: 'test@example.com',
      firstName: 'Test'
    });
    expect(result.success).toBe(true);
  });
  
  it('rejects invalid email', () => {
    const result = createContactRequestSchema.safeParse({
      email: 'invalid'
    });
    expect(result.success).toBe(false);
  });
});
```

## Best Practices

1. **Single Source of Truth**: Define schemas once
2. **Fail Fast**: Validate at boundaries
3. **Clear Errors**: Provide helpful validation messages
4. **Versioning**: Plan for schema evolution
5. **Documentation**: Include examples and descriptions
6. **Type Safety**: Leverage type inference

## Contributing

When adding new schemas:
1. Define Python model with Pydantic
2. Define TypeScript schema with Zod
3. Add validation tests for both
4. Update documentation
5. Add examples

## License

MIT License - see [LICENSE](../../LICENSE) for details.