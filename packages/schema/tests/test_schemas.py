"""
Comprehensive unit tests for Transform Army AI Pydantic schemas.

Tests validation, serialization, and edge cases for all schema models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

# Import all schemas
from packages.schema.src.python import (
    # Base
    ActionEnvelope,
    ActionStatus,
    ErrorCode,
    ErrorResponse,
    PaginationParams,
    Priority,
    TicketStatus,
    # CRM
    Contact,
    Company,
    Deal,
    Note,
    CreateContactRequest,
    SearchContactsRequest,
    # Helpdesk
    Ticket,
    TicketComment,
    CreateTicketRequest,
    TicketRequester,
    # Calendar
    CalendarEvent,
    Attendee,
    CreateEventRequest,
    # Email
    Email,
    EmailAddress,
    SendEmailRequest,
    # Knowledge
    Document,
    SearchRequest,
    IndexDocumentRequest,
    # Agent
    AgentConfig,
    AgentState,
    Workflow,
    WorkflowStep,
)


class TestBaseSchemas:
    """Tests for base schema models."""
    
    def test_action_envelope_valid(self):
        """Test valid ActionEnvelope creation."""
        envelope = ActionEnvelope(
            action_id="act_123",
            tenant_id="tenant_001",
            timestamp=datetime.utcnow(),
            operation="crm.contact.create",
            status=ActionStatus.SUCCESS,
        )
        assert envelope.action_id == "act_123"
        assert envelope.status == ActionStatus.SUCCESS
    
    def test_action_envelope_with_result(self):
        """Test ActionEnvelope with result data."""
        envelope = ActionEnvelope(
            action_id="act_123",
            tenant_id="tenant_001",
            timestamp=datetime.utcnow(),
            operation="crm.contact.create",
            status=ActionStatus.SUCCESS,
            result={"id": "cont_456", "email": "test@example.com"},
        )
        assert envelope.result["id"] == "cont_456"
    
    def test_pagination_params_defaults(self):
        """Test PaginationParams default values."""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 50
        assert params.cursor is None
    
    def test_pagination_params_validation(self):
        """Test PaginationParams validation rules."""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)  # page must be >= 1
        
        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)  # page_size max is 100
    
    def test_error_response_creation(self):
        """Test ErrorResponse creation."""
        error = ErrorResponse(
            code=ErrorCode.VALIDATION_ERROR,
            message="Invalid email format",
            timestamp=datetime.utcnow(),
        )
        assert error.code == ErrorCode.VALIDATION_ERROR
        assert "Invalid email" in error.message


class TestCRMSchemas:
    """Tests for CRM schema models."""
    
    def test_contact_creation(self):
        """Test Contact model creation."""
        contact = Contact(
            id="cont_123",
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            created_at=datetime.utcnow(),
        )
        assert contact.email == "john.doe@example.com"
        assert contact.first_name == "John"
    
    def test_contact_email_validation(self):
        """Test Contact email validation."""
        with pytest.raises(ValidationError):
            Contact(
                id="cont_123",
                email="invalid-email",  # Invalid email format
                created_at=datetime.utcnow(),
            )
    
    def test_deal_currency_validation(self):
        """Test Deal currency code validation."""
        deal = Deal(
            id="deal_123",
            name="Test Deal",
            currency="USD",
            stage="qualification",
        )
        assert deal.currency == "USD"
        
        with pytest.raises(ValidationError):
            Deal(
                id="deal_123",
                name="Test Deal",
                currency="us",  # Must be 3 uppercase letters
                stage="qualification",
            )
    
    def test_create_contact_request(self):
        """Test CreateContactRequest schema."""
        request = CreateContactRequest(
            contact=CreateContactRequest.ContactData(
                email="test@example.com",
                first_name="Test",
                last_name="User",
            ),
            idempotency_key="idm_test123",
        )
        assert request.contact.email == "test@example.com"
        assert request.idempotency_key == "idm_test123"


class TestHelpdeskSchemas:
    """Tests for helpdesk schema models."""
    
    def test_ticket_creation(self):
        """Test Ticket model creation."""
        ticket = Ticket(
            id="tick_123",
            subject="Test Issue",
            description="Description here",
            status=TicketStatus.OPEN,
            priority=Priority.HIGH,
            requester=TicketRequester(
                email="user@example.com",
                name="Test User",
            ),
            created_at=datetime.utcnow(),
        )
        assert ticket.subject == "Test Issue"
        assert ticket.status == TicketStatus.OPEN
        assert ticket.priority == Priority.HIGH
    
    def test_ticket_requester_email_validation(self):
        """Test TicketRequester email validation."""
        with pytest.raises(ValidationError):
            TicketRequester(
                email="not-an-email",
                name="Test User",
            )
    
    def test_create_ticket_request(self):
        """Test CreateTicketRequest schema."""
        request = CreateTicketRequest(
            ticket=CreateTicketRequest.TicketData(
                subject="Help needed",
                description="Need assistance",
                requester=TicketRequester(
                    email="help@example.com",
                ),
            ),
        )
        assert request.ticket.subject == "Help needed"


class TestCalendarSchemas:
    """Tests for calendar schema models."""
    
    def test_calendar_event_creation(self):
        """Test CalendarEvent creation."""
        start_time = datetime.utcnow()
        end_time = datetime.utcnow()
        
        event = CalendarEvent(
            id="evt_123",
            title="Meeting",
            start_time=start_time,
            end_time=end_time,
        )
        assert event.title == "Meeting"
        assert event.timezone == "UTC"
    
    def test_attendee_email_validation(self):
        """Test Attendee email validation."""
        attendee = Attendee(
            email="attendee@example.com",
            name="Attendee Name",
        )
        assert attendee.email == "attendee@example.com"
        
        with pytest.raises(ValidationError):
            Attendee(email="invalid-email")
    
    def test_working_hours_time_format(self):
        """Test WorkingHours time format validation."""
        from packages.schema.src.python.calendar import WorkingHours
        
        hours = WorkingHours(
            start="09:00",
            end="17:00",
            timezone="America/New_York",
        )
        assert hours.start == "09:00"
        
        with pytest.raises(ValidationError):
            WorkingHours(
                start="9:00",  # Invalid format, needs leading zero
                end="17:00",
                timezone="UTC",
            )


class TestEmailSchemas:
    """Tests for email schema models."""
    
    def test_email_address_creation(self):
        """Test EmailAddress model."""
        addr = EmailAddress(
            email="test@example.com",
            name="Test User",
        )
        assert addr.email == "test@example.com"
        assert addr.name == "Test User"
    
    def test_email_creation(self):
        """Test Email model creation."""
        from packages.schema.src.python.email import EmailBody
        
        email = Email(
            id="msg_123",
            from_=EmailAddress(email="sender@example.com"),
            to=[EmailAddress(email="recipient@example.com")],
            subject="Test Subject",
            body=EmailBody(text="Test content"),
            date=datetime.utcnow(),
        )
        assert email.subject == "Test Subject"
        assert len(email.to) == 1
    
    def test_attachment_content_type_validation(self):
        """Test Attachment content_type validation."""
        from packages.schema.src.python.email import Attachment
        
        attachment = Attachment(
            filename="test.pdf",
            content_type="application/pdf",
        )
        assert attachment.content_type == "application/pdf"
        
        with pytest.raises(ValidationError):
            Attachment(
                filename="test.pdf",
                content_type="pdf",  # Invalid, must have '/'
            )


class TestKnowledgeSchemas:
    """Tests for knowledge schema models."""
    
    def test_document_creation(self):
        """Test Document model creation."""
        doc = Document(
            id="kb_123",
            title="Test Document",
            content="Document content here",
            created_at=datetime.utcnow(),
        )
        assert doc.title == "Test Document"
        assert doc.published is False  # Default value
    
    def test_search_request_validation(self):
        """Test SearchRequest validation."""
        request = SearchRequest(
            query=SearchRequest.SearchQuery(
                text="password reset",
            ),
        )
        assert request.query.text == "password reset"
    
    def test_list_documents_sort_order(self):
        """Test ListDocumentsRequest sort_order validation."""
        from packages.schema.src.python.knowledge import ListDocumentsRequest
        
        request = ListDocumentsRequest(sort_order="desc")
        assert request.sort_order == "desc"
        
        with pytest.raises(ValidationError):
            ListDocumentsRequest(sort_order="invalid")


class TestAgentSchemas:
    """Tests for agent schema models."""
    
    def test_agent_config_creation(self):
        """Test AgentConfig creation."""
        from packages.schema.src.python.agent import AgentRole, AgentCapability
        
        config = AgentConfig(
            agent_id="agent_001",
            name="Test Agent",
            role=AgentRole.SPECIALIST,
            system_prompt="You are a helpful assistant",
            capabilities=[
                AgentCapability(
                    name="test_capability",
                    description="Test capability",
                )
            ],
        )
        assert config.agent_id == "agent_001"
        assert config.role == AgentRole.SPECIALIST
        assert config.temperature == 0.7  # Default value
    
    def test_agent_state_creation(self):
        """Test AgentState creation."""
        from packages.schema.src.python.agent import AgentStatus
        
        state = AgentState(
            agent_id="agent_001",
            status=AgentStatus.ACTIVE,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert state.status == AgentStatus.ACTIVE
        assert len(state.message_history) == 0
        assert len(state.tools_used) == 0
    
    def test_workflow_step_validation(self):
        """Test WorkflowStep validation."""
        from packages.schema.src.python.agent import WorkflowStatus
        
        step = WorkflowStep(
            step_id="step_001",
            agent_id="agent_001",
            name="Test Step",
        )
        assert step.status == WorkflowStatus.PENDING
        assert step.retry_count == 0
    
    def test_workflow_requires_steps(self):
        """Test Workflow requires at least one step."""
        from packages.schema.src.python.agent import WorkflowStatus
        
        with pytest.raises(ValidationError):
            Workflow(
                workflow_id="wf_001",
                name="Test Workflow",
                steps=[],  # Must have at least one step
            )


class TestSerialization:
    """Tests for JSON serialization/deserialization."""
    
    def test_contact_json_serialization(self):
        """Test Contact JSON serialization."""
        contact = Contact(
            id="cont_123",
            email="test@example.com",
            first_name="Test",
            created_at=datetime.utcnow(),
        )
        
        # Serialize to dict
        data = contact.model_dump()
        assert data["email"] == "test@example.com"
        
        # Deserialize from dict
        contact2 = Contact(**data)
        assert contact2.email == contact.email
    
    def test_action_envelope_json_round_trip(self):
        """Test ActionEnvelope JSON round-trip."""
        envelope = ActionEnvelope(
            action_id="act_123",
            tenant_id="tenant_001",
            timestamp=datetime.utcnow(),
            operation="test.operation",
            status=ActionStatus.SUCCESS,
        )
        
        # To JSON
        json_str = envelope.model_dump_json()
        assert "act_123" in json_str
        
        # From JSON
        envelope2 = ActionEnvelope.model_validate_json(json_str)
        assert envelope2.action_id == envelope.action_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])