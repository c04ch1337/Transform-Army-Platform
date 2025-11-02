# Schema Consistency Guide

This document provides comprehensive guidance on maintaining consistency between Python (Pydantic) and TypeScript (Zod) schemas in the Transform Army AI platform.

## Table of Contents

1. [Overview](#overview)
2. [Schema Architecture](#schema-architecture)
3. [Python/TypeScript Mapping](#pythontypescript-mapping)
4. [Field Naming Conventions](#field-naming-conventions)
5. [Type Mappings](#type-mappings)
6. [Keeping Schemas in Sync](#keeping-schemas-in-sync)
7. [Validation Procedures](#validation-procedures)
8. [Adding New Schemas](#adding-new-schemas)
9. [Common Patterns](#common-patterns)
10. [Troubleshooting](#troubleshooting)

## Overview

Transform Army AI uses a dual-schema approach to ensure type safety across the full stack:

- **Python (Pydantic)**: Backend API, data validation, and database models
- **TypeScript (Zod)**: Frontend applications, API clients, and type checking

Both implementations **must remain exactly synchronized** to prevent runtime errors and ensure seamless communication between frontend and backend.

## Schema Architecture

### Directory Structure

```
packages/schema/
├── src/
│   ├── python/           # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── base.py       # Base models and enums
│   │   ├── agent.py      # Agent schemas
│   │   ├── calendar.py   # Calendar schemas
│   │   ├── crm.py        # CRM schemas
│   │   ├── email.py      # Email schemas
│   │   ├── helpdesk.py   # Helpdesk schemas
│   │   └── knowledge.py  # Knowledge base schemas
│   └── typescript/       # Zod schemas
│       ├── base.ts       # Base schemas and enums
│       ├── agent.ts      # Agent schemas
│       ├── calendar.ts   # Calendar schemas
│       ├── crm.ts        # CRM schemas
│       ├── email.ts      # Email schemas
│       ├── helpdesk.ts   # Helpdesk schemas
│       ├── knowledge.ts  # Knowledge base schemas
│       └── index.ts      # Barrel exports
├── tests/
│   ├── test_schemas.py              # Python tests
│   └── schema_consistency.test.ts   # TypeScript tests
└── SCHEMA_CONSISTENCY.md            # This document
```

### Schema Categories

1. **Base Schemas** (`base.py` / `base.ts`)
   - Common enums (ActionStatus, ErrorCode, Priority, TicketStatus)
   - Base models (ToolInput, PaginationParams, ErrorResponse)
   - Generic structures (ActionEnvelope, ToolResult)

2. **Domain Schemas**
   - **Agent**: Agent configuration, roles, workflows, and state management
   - **Calendar**: Events, attendees, availability, and scheduling
   - **CRM**: Contacts, companies, deals, and notes
   - **Email**: Messages, threads, attachments, and search
   - **Helpdesk**: Tickets, comments, and support operations
   - **Knowledge**: Documents, search, and knowledge base management

## Python/TypeScript Mapping

### Schema Files Correspondence

| Python File | TypeScript File | Purpose |
|------------|----------------|---------|
| `base.py` | `base.ts` | Base models, enums, and common structures |
| `agent.py` | `agent.ts` | Agent configuration and workflow schemas |
| `calendar.py` | `calendar.ts` | Calendar event and scheduling schemas |
| `crm.py` | `crm.ts` | CRM contact and deal management schemas |
| `email.py` | `email.ts` | Email message and thread schemas |
| `helpdesk.py` | `helpdesk.ts` | Support ticket schemas |
| `knowledge.py` | `knowledge.ts` | Knowledge base document schemas |

### Model Naming Conventions

Both Python and TypeScript use identical model names:

```python
# Python (Pydantic)
class EmailAddress(BaseModel):
    email: EmailStr
    name: Optional[str] = None
```

```typescript
// TypeScript (Zod)
export const EmailAddressSchema = z.object({
  email: z.string().email(),
  name: z.string().optional(),
});
export type EmailAddress = z.infer<typeof EmailAddressSchema>;
```

**Naming Pattern:**
- Python: `ClassName(BaseModel)`
- TypeScript: `ClassNameSchema = z.object(...)`
- TypeScript type: `type ClassName = z.infer<typeof ClassNameSchema>`

## Field Naming Conventions

### Snake Case Standard

**All field names MUST use snake_case** in both Python and TypeScript:

✅ **Correct:**
```python
# Python
thread_id: str
is_read: bool
created_at: datetime
```

```typescript
// TypeScript
thread_id: z.string()
is_read: z.boolean()
created_at: z.string().datetime()
```

❌ **Incorrect:**
```typescript
// DO NOT use camelCase in schemas
threadId: z.string()     // Wrong!
isRead: z.boolean()      // Wrong!
createdAt: z.string()    // Wrong!
```

### Reserved Keywords

Python's `from` is a reserved keyword, so we use aliases:

```python
# Python
from_: EmailAddress = Field(alias="from")
```

```typescript
// TypeScript
from: EmailAddressSchema
```

Both serialize to `"from"` in JSON.

## Type Mappings

### Primitive Types

| Python (Pydantic) | TypeScript (Zod) | Notes |
|-------------------|------------------|-------|
| `str` | `z.string()` | Basic string |
| `int` | `z.number().int()` | Integer |
| `float` | `z.number()` | Floating point |
| `bool` | `z.boolean()` | Boolean |
| `datetime` | `z.string().datetime()` or `z.date()` | ISO 8601 format |
| `date` | `z.string()` | YYYY-MM-DD format |
| `EmailStr` | `z.string().email()` | Email validation |
| `HttpUrl` | `z.string().url()` | URL validation |

### Complex Types

| Python (Pydantic) | TypeScript (Zod) | Notes |
|-------------------|------------------|-------|
| `List[T]` | `z.array(T)` | Array of type T |
| `Optional[T]` | `T.optional()` | Nullable field |
| `Dict[str, T]` | `z.record(T)` | Object with string keys |
| `Union[A, B]` | `A.or(B)` | Union type |
| `Literal["a", "b"]` | `z.enum(["a", "b"])` | Enum values |

### Enums

Python and TypeScript enums must have identical values:

```python
# Python
class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    BDR_CONCIERGE = "bdr_concierge"
```

```typescript
// TypeScript
export const AgentRoleSchema = z.enum([
  'orchestrator',
  'bdr_concierge',
]);
```

### Validation Constraints

Common validation rules and their equivalents:

| Python (Pydantic) | TypeScript (Zod) |
|-------------------|------------------|
| `Field(ge=0)` | `z.number().min(0)` |
| `Field(le=100)` | `z.number().max(100)` |
| `Field(min_length=1)` | `z.string().min(1)` |
| `Field(max_length=255)` | `z.string().max(255)` |
| `Field(regex=r"^\d{2}:\d{2}$")` | `z.string().regex(/^\d{2}:\d{2}$/)` |

## Keeping Schemas in Sync

### Development Workflow

1. **Define Requirements**
   - Identify the data structure needed
   - Document all fields and validations

2. **Create/Update Python Schema**
   - Add model to appropriate file in `src/python/`
   - Include docstrings and examples
   - Add field descriptions and validations

3. **Create/Update TypeScript Schema**
   - Mirror the Python schema in `src/typescript/`
   - Use exact same field names
   - Apply equivalent validations

4. **Update Exports**
   - Add to Python `__init__.py` if needed
   - Add to TypeScript `index.ts`

5. **Write Tests**
   - Add validation tests to `test_schemas.py`
   - Add consistency tests to `schema_consistency.test.ts`

6. **Run Validation**
   - Execute Python tests: `pytest packages/schema/tests/`
   - Execute TypeScript tests: `npm test` in `packages/schema/`

### Checklist for Schema Changes

When modifying schemas, verify:

- [ ] Field names are identical (snake_case)
- [ ] Types are correctly mapped
- [ ] Required/optional fields match
- [ ] Default values are identical
- [ ] Validation rules are equivalent
- [ ] Enum values are identical
- [ ] Documentation is updated
- [ ] Tests pass in both languages
- [ ] Exports are updated

## Validation Procedures

### Running Tests

**Python Tests:**
```bash
cd packages/schema
pytest tests/test_schemas.py -v
```

**TypeScript Tests:**
```bash
cd packages/schema
npm test
```

### Manual Validation

1. **Field Name Check**
   - Compare field lists between Python and TypeScript
   - Ensure all fields use snake_case
   - Verify no camelCase fields exist

2. **Type Validation**
   - Test with sample data
   - Verify parsing succeeds with valid data
   - Verify parsing fails with invalid data

3. **Serialization Check**
   - Create object in Python, serialize to JSON
   - Parse JSON in TypeScript
   - Verify all fields are present and correct

### Automated Consistency Checks

The test suite includes automated checks for:

- Enum value consistency
- Field name consistency (snake_case)
- Required vs optional field alignment
- Sample data validation

## Adding New Schemas

### Step-by-Step Guide

1. **Plan the Schema**
   ```markdown
   Schema Name: ArticleComment
   Purpose: Represent comments on knowledge base articles
   
   Fields:
   - id: string (required)
   - article_id: string (required)
   - author_email: email (required)
   - content: string (required)
   - created_at: datetime (required)
   - helpful_votes: int (optional, min 0)
   ```

2. **Create Python Schema**
   ```python
   # In packages/schema/src/python/knowledge.py
   
   class ArticleComment(BaseModel):
       """Comment on a knowledge base article."""
       
       model_config = ConfigDict(
           json_schema_extra={
               "example": {
                   "id": "cmt_123",
                   "article_id": "art_456",
                   "author_email": "user@example.com",
                   "content": "Great article!",
                   "created_at": "2025-10-31T01:17:00Z",
                   "helpful_votes": 5
               }
           }
       )
       
       id: str = Field(description="Unique comment identifier")
       article_id: str = Field(description="Article identifier")
       author_email: EmailStr = Field(description="Comment author email")
       content: str = Field(description="Comment content")
       created_at: datetime = Field(description="Creation timestamp")
       helpful_votes: Optional[int] = Field(
           default=None,
           ge=0,
           description="Number of helpful votes"
       )
   ```

3. **Create TypeScript Schema**
   ```typescript
   // In packages/schema/src/typescript/knowledge.ts
   
   /**
    * Comment on a knowledge base article.
    */
   export const ArticleCommentSchema = z.object({
     id: z.string().describe('Unique comment identifier'),
     article_id: z.string().describe('Article identifier'),
     author_email: z.string().email().describe('Comment author email'),
     content: z.string().describe('Comment content'),
     created_at: z.string().datetime().or(z.date()).describe('Creation timestamp'),
     helpful_votes: z.number().int().min(0).optional().describe('Number of helpful votes'),
   });
   export type ArticleComment = z.infer<typeof ArticleCommentSchema>;
   ```

4. **Update Exports**
   ```python
   # In packages/schema/src/python/__init__.py
   from .knowledge import ArticleComment
   ```
   
   ```typescript
   // In packages/schema/src/typescript/index.ts
   export type { ArticleComment } from './knowledge';
   ```

5. **Add Tests**
   ```python
   # In packages/schema/tests/test_schemas.py
   def test_article_comment():
       comment = ArticleComment(
           id="cmt_123",
           article_id="art_456",
           author_email="user@example.com",
           content="Great article!",
           created_at=datetime.utcnow()
       )
       assert comment.id == "cmt_123"
   ```
   
   ```typescript
   // In packages/schema/tests/schema_consistency.test.ts
   it('should validate ArticleComment', () => {
     const validComment = {
       id: 'cmt_123',
       article_id: 'art_456',
       author_email: 'user@example.com',
       content: 'Great article!',
       created_at: new Date().toISOString(),
     };
     
     expect(() => ArticleCommentSchema.parse(validComment)).not.toThrow();
   });
   ```

## Common Patterns

### Nested Models

```python
# Python
class Address(BaseModel):
    street: str
    city: str

class Contact(BaseModel):
    name: str
    address: Address
```

```typescript
// TypeScript
export const AddressSchema = z.object({
  street: z.string(),
  city: z.string(),
});

export const ContactSchema = z.object({
  name: z.string(),
  address: AddressSchema,
});
```

### Arrays of Objects

```python
# Python
class Email(BaseModel):
    to: List[EmailAddress]
```

```typescript
// TypeScript
export const EmailSchema = z.object({
  to: z.array(EmailAddressSchema),
});
```

### Optional Fields with Defaults

```python
# Python
published: bool = Field(default=False)
```

```typescript
// TypeScript
published: z.boolean().default(false)
```

### Union Types

```python
# Python
value: Union[str, int]
```

```typescript
// TypeScript
value: z.string().or(z.number())
```

### Generic Models

```python
# Python (using TypeVar)
TResult = TypeVar('TResult')

class ToolResult(BaseModel, Generic[TResult]):
    data: TResult
```

```typescript
// TypeScript (using z.any())
export const ToolResultSchema = z.object({
  data: z.any(),
});
```

## Troubleshooting

### Common Issues

**Issue: Field name mismatch**
```
Error: Unknown field 'threadId' in TypeScript
```
**Solution:** Ensure field uses snake_case: `thread_id`

---

**Issue: Type validation fails**
```
Error: Expected number, received string
```
**Solution:** Check type mappings. Ensure Python `int` maps to TypeScript `z.number().int()`

---

**Issue: Enum values don't match**
```
Error: Invalid enum value 'bdr-concierge'
```
**Solution:** Enum values must be identical. Use `bdr_concierge` (underscore, not hyphen)

---

**Issue: Required field missing**
```
Error: Required field 'email' is missing
```
**Solution:** Verify field is not marked optional in one language but required in other

---

**Issue: Date/datetime parsing fails**
```
Error: Invalid datetime format
```
**Solution:** Use ISO 8601 format. Python: `datetime.isoformat()`, TypeScript: `.toISOString()`

### Debugging Tips

1. **Compare Field Lists**
   ```python
   # Python
   print(Model.__fields__.keys())
   ```
   ```typescript
   // TypeScript
   console.log(Object.keys(ModelSchema.shape));
   ```

2. **Test Serialization**
   ```python
   # Python
   obj = Model(...)
   json_str = obj.model_dump_json()
   ```
   ```typescript
   // TypeScript
   const parsed = ModelSchema.parse(JSON.parse(json_str));
   ```

3. **Use Validation Errors**
   Both Pydantic and Zod provide detailed error messages:
   ```python
   # Python
   try:
       Model(**data)
   except ValidationError as e:
       print(e.errors())
   ```
   ```typescript
   // TypeScript
   try {
       ModelSchema.parse(data);
   } catch (e) {
       console.log(e.errors);
   }
   ```

## Schema Governance

### Review Process

All schema changes require:

1. **Peer Review**
   - Another developer must review Python and TypeScript changes
   - Verify field names, types, and validations match

2. **Test Coverage**
   - New schemas must have tests in both languages
   - Tests must validate required fields, optional fields, and constraints

3. **Documentation**
   - Update this document if new patterns are introduced
   - Add examples for complex schemas

### Version Control

- Schema changes should be atomic (Python + TypeScript in same commit)
- Use descriptive commit messages: `feat(schema): add ArticleComment model`
- Tag breaking schema changes appropriately

### Breaking Changes

Schema changes that break compatibility:

- Removing required fields
- Changing field types
- Renaming fields
- Changing enum values

These require:
- Version bump
- Migration guide
- Deprecation period (if applicable)

## Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Zod Documentation](https://zod.dev/)
- [JSON Schema Specification](https://json-schema.org/)
- [Python Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## Appendix: Agent Role Reference

Current agent roles defined in both Python and TypeScript:

### Generic Roles
- `orchestrator` - Coordinates multi-agent workflows
- `researcher` - Gathers and analyzes information
- `analyst` - Performs data analysis
- `writer` - Creates content and documentation
- `reviewer` - Reviews and validates work
- `executor` - Executes specific tasks
- `specialist` - Domain-specific expertise
- `custom` - Custom role definition

### Business-Specific Roles
- `bdr_concierge` - Business Development Representative assistant
- `support_concierge` - Customer support assistant
- `research_recon` - Market research and reconnaissance
- `ops_sapper` - Operations automation specialist
- `knowledge_librarian` - Knowledge base management
- `qa_auditor` - Quality assurance and testing

---

**Last Updated:** 2025-11-01

**Maintained By:** Transform Army AI Engineering Team