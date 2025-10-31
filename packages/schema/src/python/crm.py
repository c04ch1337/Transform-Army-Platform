"""
CRM schema models for Transform Army AI Adapter Service.

This module defines Pydantic models for CRM operations including contacts,
companies, deals, and notes across different CRM providers (HubSpot, Salesforce, etc.).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, EmailStr, HttpUrl, ConfigDict, field_validator

from .base import ToolInput, PaginationParams, PaginationResponse


class Contact(BaseModel):
    """
    CRM contact model representing a person in the CRM system.
    
    This model abstracts contact data across different CRM providers.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "cont_12345",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "company": "Acme Corp",
                "phone": "+1-555-0123",
                "title": "VP of Sales",
                "url": "https://app.hubspot.com/contacts/12345",
                "created_at": "2025-10-31T01:17:00Z",
                "updated_at": "2025-10-31T01:17:00Z",
                "custom_fields": {
                    "lead_source": "website",
                    "lead_score": 85
                }
            }
        }
    )
    
    id: str = Field(description="Unique contact identifier")
    email: EmailStr = Field(description="Contact email address")
    first_name: Optional[str] = Field(
        default=None,
        description="Contact first name"
    )
    last_name: Optional[str] = Field(
        default=None,
        description="Contact last name"
    )
    company: Optional[str] = Field(
        default=None,
        description="Company name"
    )
    phone: Optional[str] = Field(
        default=None,
        description="Phone number"
    )
    title: Optional[str] = Field(
        default=None,
        description="Job title"
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to view contact in provider system"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Contact creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Provider-specific custom fields"
    )
    owner_id: Optional[str] = Field(
        default=None,
        description="ID of the contact owner/assignee"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags associated with the contact"
    )


class Company(BaseModel):
    """
    CRM company/account model.
    
    Represents an organization in the CRM system.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "comp_456",
                "name": "Acme Corp",
                "domain": "acme.com",
                "industry": "Technology",
                "employees": 500,
                "annual_revenue": 10000000,
                "url": "https://app.hubspot.com/companies/456"
            }
        }
    )
    
    id: str = Field(description="Unique company identifier")
    name: str = Field(description="Company name")
    domain: Optional[str] = Field(
        default=None,
        description="Company website domain"
    )
    industry: Optional[str] = Field(
        default=None,
        description="Industry/sector"
    )
    employees: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of employees"
    )
    annual_revenue: Optional[float] = Field(
        default=None,
        ge=0,
        description="Annual revenue"
    )
    phone: Optional[str] = Field(
        default=None,
        description="Company phone number"
    )
    address: Optional[str] = Field(
        default=None,
        description="Company address"
    )
    city: Optional[str] = Field(
        default=None,
        description="City"
    )
    state: Optional[str] = Field(
        default=None,
        description="State/province"
    )
    country: Optional[str] = Field(
        default=None,
        description="Country"
    )
    postal_code: Optional[str] = Field(
        default=None,
        description="Postal/ZIP code"
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to view company in provider system"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Company creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Provider-specific custom fields"
    )


class Deal(BaseModel):
    """
    CRM deal/opportunity model.
    
    Represents a sales opportunity or deal in the CRM pipeline.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "deal_789",
                "name": "Acme Corp - Enterprise Plan",
                "amount": 50000,
                "currency": "USD",
                "stage": "qualification",
                "probability": 0.25,
                "close_date": "2025-12-31",
                "contact_ids": ["cont_12345"],
                "company_id": "comp_456"
            }
        }
    )
    
    id: str = Field(description="Unique deal identifier")
    name: str = Field(description="Deal name")
    amount: Optional[float] = Field(
        default=None,
        ge=0,
        description="Deal amount/value"
    )
    currency: str = Field(
        default="USD",
        description="Currency code (ISO 4217)"
    )
    stage: str = Field(
        description="Current deal stage/status"
    )
    probability: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Win probability (0-1)"
    )
    close_date: Optional[str] = Field(
        default=None,
        description="Expected close date (YYYY-MM-DD)"
    )
    contact_ids: Optional[List[str]] = Field(
        default=None,
        description="Associated contact IDs"
    )
    company_id: Optional[str] = Field(
        default=None,
        description="Associated company ID"
    )
    owner_id: Optional[str] = Field(
        default=None,
        description="Deal owner/assignee ID"
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to view deal in provider system"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Deal creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Provider-specific custom fields"
    )
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code format (3 uppercase letters)."""
        if len(v) != 3 or not v.isupper():
            raise ValueError("Currency must be a 3-letter ISO 4217 code (e.g., USD, EUR)")
        return v


class Note(BaseModel):
    """
    CRM note/activity model.
    
    Represents a note or activity associated with a contact, company, or deal.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "note_678",
                "content": "Initial qualification call completed.",
                "type": "call_note",
                "contact_id": "cont_12345",
                "created_at": "2025-10-31T01:15:00Z"
            }
        }
    )
    
    id: str = Field(description="Unique note identifier")
    content: str = Field(description="Note content/body")
    type: Optional[str] = Field(
        default=None,
        description="Note type (e.g., 'call_note', 'email', 'meeting')"
    )
    contact_id: Optional[str] = Field(
        default=None,
        description="Associated contact ID"
    )
    company_id: Optional[str] = Field(
        default=None,
        description="Associated company ID"
    )
    deal_id: Optional[str] = Field(
        default=None,
        description="Associated deal ID"
    )
    author_id: Optional[str] = Field(
        default=None,
        description="Note author/creator ID"
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Note timestamp (when the activity occurred)"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Note creation timestamp in system"
    )


class CreateContactRequest(ToolInput):
    """
    Request to create a new CRM contact.
    
    Includes deduplication options to handle existing contacts.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_unique123",
                "correlation_id": "cor_req123",
                "contact": {
                    "email": "john.doe@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "company": "Acme Corp",
                    "phone": "+1-555-0123",
                    "title": "VP of Sales"
                },
                "options": {
                    "dedupe_by": ["email"],
                    "update_if_exists": True
                }
            }
        }
    )
    
    class ContactData(BaseModel):
        """Contact data for creation."""
        email: EmailStr = Field(description="Contact email (required)")
        first_name: Optional[str] = Field(default=None, description="First name")
        last_name: Optional[str] = Field(default=None, description="Last name")
        company: Optional[str] = Field(default=None, description="Company name")
        phone: Optional[str] = Field(default=None, description="Phone number")
        title: Optional[str] = Field(default=None, description="Job title")
        owner_id: Optional[str] = Field(default=None, description="Owner ID")
        tags: Optional[List[str]] = Field(default=None, description="Tags")
        custom_fields: Optional[Dict[str, Any]] = Field(
            default=None,
            description="Custom fields"
        )
    
    class ContactOptions(BaseModel):
        """Options for contact creation."""
        dedupe_by: Optional[List[str]] = Field(
            default=None,
            description="Fields to check for duplicates (e.g., ['email'])"
        )
        update_if_exists: bool = Field(
            default=False,
            description="Update contact if duplicate found"
        )
    
    contact: ContactData = Field(description="Contact data to create")
    options: Optional[ContactOptions] = Field(
        default=None,
        description="Creation options"
    )


class UpdateContactRequest(ToolInput):
    """Request to update an existing CRM contact."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_update456",
                "correlation_id": "cor_req124",
                "updates": {
                    "title": "Senior VP of Sales",
                    "phone": "+1-555-0199"
                }
            }
        }
    )
    
    updates: Dict[str, Any] = Field(
        description="Fields to update (partial update)"
    )


class CreateDealRequest(ToolInput):
    """Request to create a new CRM deal/opportunity."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_deal789",
                "correlation_id": "cor_req126",
                "deal": {
                    "name": "Acme Corp - Enterprise Plan",
                    "amount": 50000,
                    "currency": "USD",
                    "stage": "qualification",
                    "close_date": "2025-12-31",
                    "contact_ids": ["cont_12345"],
                    "company_id": "comp_456"
                }
            }
        }
    )
    
    class DealData(BaseModel):
        """Deal data for creation."""
        name: str = Field(description="Deal name")
        amount: Optional[float] = Field(default=None, ge=0, description="Deal amount")
        currency: str = Field(default="USD", description="Currency code")
        stage: str = Field(description="Deal stage")
        probability: Optional[float] = Field(
            default=None,
            ge=0,
            le=1,
            description="Win probability"
        )
        close_date: Optional[str] = Field(
            default=None,
            description="Expected close date (YYYY-MM-DD)"
        )
        contact_ids: Optional[List[str]] = Field(
            default=None,
            description="Associated contact IDs"
        )
        company_id: Optional[str] = Field(
            default=None,
            description="Associated company ID"
        )
        owner_id: Optional[str] = Field(default=None, description="Deal owner ID")
        custom_fields: Optional[Dict[str, Any]] = Field(
            default=None,
            description="Custom fields"
        )
    
    deal: DealData = Field(description="Deal data to create")


class UpdateDealRequest(ToolInput):
    """Request to update an existing CRM deal."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_deal_update890",
                "correlation_id": "cor_req127",
                "updates": {
                    "stage": "negotiation",
                    "probability": 0.75,
                    "amount": 55000
                }
            }
        }
    )
    
    updates: Dict[str, Any] = Field(
        description="Fields to update (partial update)"
    )


class AddNoteRequest(ToolInput):
    """Request to add a note to a CRM entity."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "idempotency_key": "idm_note456",
                "correlation_id": "cor_req124",
                "note": {
                    "content": "Initial qualification call completed.",
                    "type": "call_note",
                    "timestamp": "2025-10-31T01:15:00Z"
                }
            }
        }
    )
    
    class NoteData(BaseModel):
        """Note data for creation."""
        content: str = Field(description="Note content")
        type: Optional[str] = Field(default=None, description="Note type")
        timestamp: Optional[datetime] = Field(
            default=None,
            description="When the activity occurred"
        )
    
    note: NoteData = Field(description="Note data to create")


class SearchContactsRequest(BaseModel):
    """Request to search for CRM contacts."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "john.doe@example.com",
                "fields": ["email", "first_name", "last_name", "company"],
                "filters": {
                    "company": "Acme Corp",
                    "tags": ["lead", "qualified"]
                },
                "pagination": {
                    "page": 1,
                    "page_size": 10
                }
            }
        }
    )
    
    query: Optional[str] = Field(
        default=None,
        description="Search query string"
    )
    fields: Optional[List[str]] = Field(
        default=None,
        description="Fields to return in results"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional filters to apply"
    )
    pagination: Optional[PaginationParams] = Field(
        default=None,
        description="Pagination parameters"
    )


class ContactSearchMatch(BaseModel):
    """A single contact search result with relevance score."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "cont_12345",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "company": "Acme Corp",
                "score": 0.98
            }
        }
    )
    
    id: str = Field(description="Contact ID")
    email: EmailStr = Field(description="Contact email")
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    company: Optional[str] = Field(default=None, description="Company")
    title: Optional[str] = Field(default=None, description="Job title")
    phone: Optional[str] = Field(default=None, description="Phone")
    score: float = Field(
        ge=0,
        le=1,
        description="Relevance score (0-1)"
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="URL to view in provider system"
    )


class SearchContactsResponse(BaseModel):
    """Response from contact search operation."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "matches": [
                    {
                        "id": "cont_12345",
                        "email": "john.doe@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "company": "Acme Corp",
                        "score": 0.98
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total_pages": 1,
                    "total_items": 1,
                    "has_next": False,
                    "has_previous": False
                }
            }
        }
    )
    
    matches: List[ContactSearchMatch] = Field(description="Search results")
    pagination: Optional[PaginationResponse] = Field(
        default=None,
        description="Pagination metadata"
    )