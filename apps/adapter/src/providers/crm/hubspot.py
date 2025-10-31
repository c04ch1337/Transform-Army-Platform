"""
HubSpot CRM provider implementation.

This is a stub implementation that simulates HubSpot API interactions
for testing and development purposes.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from ..base import (
    ProviderPlugin,
    ProviderCapability,
    AuthenticationError,
    ValidationError,
    NotFoundError
)
from ...core.logging import get_logger


logger = get_logger(__name__)


class HubSpotProvider(ProviderPlugin):
    """
    HubSpot CRM provider stub implementation.
    
    Simulates HubSpot API for contact, company, deal, and note operations.
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize HubSpot provider.
        
        Args:
            credentials: HubSpot credentials including api_key
        """
        super().__init__(credentials)
        self._contacts = {}
        self._companies = {}
        self._deals = {}
        self._notes = {}
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "hubspot"
    
    @property
    def supported_capabilities(self) -> List[ProviderCapability]:
        """Return supported capabilities."""
        return [
            ProviderCapability.CRM_CONTACTS,
            ProviderCapability.CRM_COMPANIES,
            ProviderCapability.CRM_DEALS,
            ProviderCapability.CRM_NOTES
        ]
    
    async def validate_credentials(self) -> bool:
        """
        Validate HubSpot credentials.
        
        Returns:
            True if credentials are valid
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        api_key = self.credentials.get("api_key")
        
        if not api_key:
            raise AuthenticationError(
                "Missing HubSpot API key",
                provider=self.provider_name
            )
        
        if len(api_key) < 20:
            raise AuthenticationError(
                "Invalid HubSpot API key format",
                provider=self.provider_name
            )
        
        logger.info(f"HubSpot credentials validated for key: {api_key[:10]}...")
        return True
    
    async def execute_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute HubSpot action.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            idempotency_key: Optional idempotency key
            
        Returns:
            Action result
            
        Raises:
            ValidationError: If parameters are invalid
            NotFoundError: If resource not found
        """
        action_map = {
            "create_contact": self._create_contact,
            "update_contact": self._update_contact,
            "get_contact": self._get_contact,
            "search_contacts": self._search_contacts,
            "create_company": self._create_company,
            "create_deal": self._create_deal,
            "add_note": self._add_note
        }
        
        handler = action_map.get(action)
        if not handler:
            raise ValueError(f"Unsupported action: {action}")
        
        return await handler(parameters, idempotency_key)
    
    def normalize_response(
        self,
        provider_response: Any,
        action: str
    ) -> Dict[str, Any]:
        """
        Normalize HubSpot response.
        
        Args:
            provider_response: Raw HubSpot response
            action: Action that was executed
            
        Returns:
            Normalized response
        """
        # Stub implementation - responses are already normalized
        return provider_response
    
    async def health_check(self) -> bool:
        """Check HubSpot provider health."""
        try:
            await self.validate_credentials()
            return True
        except Exception:
            return False
    
    async def _create_contact(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Create contact in HubSpot."""
        contact_data = parameters.get("contact", {})
        
        # Validate required fields
        if not contact_data.get("email"):
            raise ValidationError(
                "Email is required for contact creation",
                provider=self.provider_name,
                action="create_contact"
            )
        
        # Generate contact ID
        contact_id = f"hs_cont_{uuid.uuid4().hex[:12]}"
        
        # Store contact
        self._contacts[contact_id] = {
            "id": contact_id,
            "email": contact_data.get("email"),
            "first_name": contact_data.get("first_name"),
            "last_name": contact_data.get("last_name"),
            "company": contact_data.get("company"),
            "phone": contact_data.get("phone"),
            "title": contact_data.get("title"),
            "custom_fields": contact_data.get("custom_fields", {}),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return {
            "id": f"cont_{contact_id}",
            "provider": self.provider_name,
            "provider_id": contact_id,
            "data": {
                **self._contacts[contact_id],
                "url": f"https://app.hubspot.com/contacts/{contact_id}"
            }
        }
    
    async def _update_contact(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Update contact in HubSpot."""
        contact_id = parameters.get("contact_id")
        updates = parameters.get("updates", {})
        
        if contact_id not in self._contacts:
            raise NotFoundError(
                f"Contact not found: {contact_id}",
                provider=self.provider_name,
                action="update_contact"
            )
        
        # Update contact
        self._contacts[contact_id].update(updates)
        self._contacts[contact_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        return {
            "id": f"cont_{contact_id}",
            "provider": self.provider_name,
            "provider_id": contact_id,
            "data": self._contacts[contact_id]
        }
    
    async def _get_contact(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Get contact from HubSpot."""
        contact_id = parameters.get("contact_id")
        
        if contact_id not in self._contacts:
            raise NotFoundError(
                f"Contact not found: {contact_id}",
                provider=self.provider_name,
                action="get_contact"
            )
        
        return {
            "id": f"cont_{contact_id}",
            "provider": self.provider_name,
            "provider_id": contact_id,
            "data": self._contacts[contact_id]
        }
    
    async def _search_contacts(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Search contacts in HubSpot."""
        query = parameters.get("query", "")
        
        # Simple search - match against email, first_name, last_name
        matches = []
        for contact_id, contact in self._contacts.items():
            if (query.lower() in str(contact.get("email", "")).lower() or
                query.lower() in str(contact.get("first_name", "")).lower() or
                query.lower() in str(contact.get("last_name", "")).lower()):
                matches.append({
                    "id": f"cont_{contact_id}",
                    "email": contact["email"],
                    "first_name": contact.get("first_name"),
                    "last_name": contact.get("last_name"),
                    "company": contact.get("company"),
                    "score": 0.95
                })
        
        return {
            "matches": matches,
            "pagination": {
                "total_items": len(matches),
                "has_next": False
            }
        }
    
    async def _create_company(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Create company in HubSpot."""
        company_data = parameters.get("company", {})
        
        # Validate required fields
        if not company_data.get("name"):
            raise ValidationError(
                "Name is required for company creation",
                provider=self.provider_name,
                action="create_company"
            )
        
        # Generate company ID
        company_id = f"hs_comp_{uuid.uuid4().hex[:12]}"
        
        # Store company
        self._companies[company_id] = {
            "id": company_id,
            "name": company_data.get("name"),
            "domain": company_data.get("domain"),
            "industry": company_data.get("industry"),
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return {
            "id": f"comp_{company_id}",
            "provider": self.provider_name,
            "provider_id": company_id,
            "data": self._companies[company_id]
        }
    
    async def _create_deal(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Create deal in HubSpot."""
        deal_data = parameters.get("deal", {})
        
        # Validate required fields
        if not deal_data.get("name"):
            raise ValidationError(
                "Name is required for deal creation",
                provider=self.provider_name,
                action="create_deal"
            )
        
        # Generate deal ID
        deal_id = f"hs_deal_{uuid.uuid4().hex[:12]}"
        
        # Store deal
        self._deals[deal_id] = {
            "id": deal_id,
            "name": deal_data.get("name"),
            "amount": deal_data.get("amount"),
            "stage": deal_data.get("stage"),
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return {
            "id": f"deal_{deal_id}",
            "provider": self.provider_name,
            "provider_id": deal_id,
            "data": self._deals[deal_id]
        }
    
    async def _add_note(
        self,
        parameters: Dict[str, Any],
        idempotency_key: Optional[str]
    ) -> Dict[str, Any]:
        """Add note to contact/company/deal in HubSpot."""
        note_data = parameters.get("note", {})
        contact_id = parameters.get("contact_id")
        
        # Generate note ID
        note_id = f"hs_note_{uuid.uuid4().hex[:12]}"
        
        # Store note
        self._notes[note_id] = {
            "id": note_id,
            "content": note_data.get("content"),
            "contact_id": contact_id,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return {
            "id": f"note_{note_id}",
            "provider": self.provider_name,
            "provider_id": note_id,
            "data": self._notes[note_id]
        }