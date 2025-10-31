/**
 * Comprehensive unit tests for Transform Army AI Zod schemas.
 * 
 * Tests validation, parsing, and edge cases for all schema models.
 */

import { describe, it, expect } from 'vitest';
import { z } from 'zod';

// Import all schemas
import {
  // Base
  ActionEnvelopeSchema,
  ActionStatusSchema,
  ErrorCodeSchema,
  ErrorResponseSchema,
  PaginationParamsSchema,
  PrioritySchema,
  TicketStatusSchema,
  // CRM
  ContactSchema,
  CompanySchema,
  DealSchema,
  CreateContactRequestSchema,
  SearchContactsRequestSchema,
  // Helpdesk
  TicketSchema,
  TicketCommentSchema,
  CreateTicketRequestSchema,
  TicketRequesterSchema,
  // Calendar
  CalendarEventSchema,
  AttendeeSchema,
  CreateEventRequestSchema,
  WorkingHoursSchema,
  // Email
  EmailSchema,
  EmailAddressSchema,
  SendEmailRequestSchema,
  AttachmentSchema,
  // Knowledge
  DocumentSchema,
  SearchRequestSchema,
  IndexDocumentRequestSchema,
  // Agent
  AgentConfigSchema,
  AgentStateSchema,
  WorkflowSchema,
  WorkflowStepSchema,
} from '../src/typescript';

describe('Base Schemas', () => {
  describe('ActionEnvelopeSchema', () => {
    it('should validate a valid action envelope', () => {
      const data = {
        action_id: 'act_123',
        tenant_id: 'tenant_001',
        timestamp: new Date().toISOString(),
        operation: 'crm.contact.create',
        status: 'success',
      };
      
      const result = ActionEnvelopeSchema.safeParse(data);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.action_id).toBe('act_123');
        expect(result.data.status).toBe('success');
      }
    });

    it('should validate envelope with result', () => {
      const data = {
        action_id: 'act_123',
        tenant_id: 'tenant_001',
        timestamp: new Date().toISOString(),
        operation: 'crm.contact.create',
        status: 'success',
        result: { id: 'cont_456', email: 'test@example.com' },
      };
      
      const result = ActionEnvelopeSchema.parse(data);
      expect(result.result).toEqual({ id: 'cont_456', email: 'test@example.com' });
    });
  });

  describe('PaginationParamsSchema', () => {
    it('should use default values', () => {
      const result = PaginationParamsSchema.parse({});
      expect(result.page).toBe(1);
      expect(result.page_size).toBe(50);
    });

    it('should reject invalid page number', () => {
      const result = PaginationParamsSchema.safeParse({ page: 0 });
      expect(result.success).toBe(false);
    });

    it('should reject page_size over 100', () => {
      const result = PaginationParamsSchema.safeParse({ page_size: 101 });
      expect(result.success).toBe(false);
    });
  });

  describe('ErrorResponseSchema', () => {
    it('should validate error response', () => {
      const error = {
        code: 'VALIDATION_ERROR',
        message: 'Invalid email format',
        timestamp: new Date().toISOString(),
      };
      
      const result = ErrorResponseSchema.parse(error);
      expect(result.code).toBe('VALIDATION_ERROR');
      expect(result.message).toContain('Invalid email');
    });
  });
});

describe('CRM Schemas', () => {
  describe('ContactSchema', () => {
    it('should validate a valid contact', () => {
      const contact = {
        id: 'cont_123',
        email: 'john.doe@example.com',
        first_name: 'John',
        last_name: 'Doe',
        created_at: new Date().toISOString(),
      };
      
      const result = ContactSchema.parse(contact);
      expect(result.email).toBe('john.doe@example.com');
      expect(result.first_name).toBe('John');
    });

    it('should reject invalid email', () => {
      const contact = {
        id: 'cont_123',
        email: 'invalid-email',
        created_at: new Date().toISOString(),
      };
      
      const result = ContactSchema.safeParse(contact);
      expect(result.success).toBe(false);
    });
  });

  describe('DealSchema', () => {
    it('should validate deal with currency', () => {
      const deal = {
        id: 'deal_123',
        name: 'Test Deal',
        currency: 'USD',
        stage: 'qualification',
      };
      
      const result = DealSchema.parse(deal);
      expect(result.currency).toBe('USD');
    });

    it('should reject invalid currency code', () => {
      const deal = {
        id: 'deal_123',
        name: 'Test Deal',
        currency: 'US',
        stage: 'qualification',
      };
      
      const result = DealSchema.safeParse(deal);
      expect(result.success).toBe(false);
    });
  });

  describe('CreateContactRequestSchema', () => {
    it('should validate contact creation request', () => {
      const request = {
        contact: {
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
        },
        idempotency_key: 'idm_test123',
      };
      
      const result = CreateContactRequestSchema.parse(request);
      expect(result.contact.email).toBe('test@example.com');
      expect(result.idempotency_key).toBe('idm_test123');
    });
  });
});

describe('Helpdesk Schemas', () => {
  describe('TicketSchema', () => {
    it('should validate a valid ticket', () => {
      const ticket = {
        id: 'tick_123',
        subject: 'Test Issue',
        description: 'Description here',
        status: 'open',
        priority: 'high',
        requester: {
          email: 'user@example.com',
          name: 'Test User',
        },
        created_at: new Date().toISOString(),
      };
      
      const result = TicketSchema.parse(ticket);
      expect(result.subject).toBe('Test Issue');
      expect(result.status).toBe('open');
      expect(result.priority).toBe('high');
    });
  });

  describe('TicketRequesterSchema', () => {
    it('should reject invalid email', () => {
      const requester = {
        email: 'not-an-email',
        name: 'Test User',
      };
      
      const result = TicketRequesterSchema.safeParse(requester);
      expect(result.success).toBe(false);
    });
  });

  describe('CreateTicketRequestSchema', () => {
    it('should validate ticket creation request', () => {
      const request = {
        ticket: {
          subject: 'Help needed',
          description: 'Need assistance',
          requester: {
            email: 'help@example.com',
          },
        },
      };
      
      const result = CreateTicketRequestSchema.parse(request);
      expect(result.ticket.subject).toBe('Help needed');
    });
  });
});

describe('Calendar Schemas', () => {
  describe('CalendarEventSchema', () => {
    it('should validate calendar event', () => {
      const event = {
        id: 'evt_123',
        title: 'Meeting',
        start_time: new Date().toISOString(),
        end_time: new Date(Date.now() + 3600000).toISOString(),
      };
      
      const result = CalendarEventSchema.parse(event);
      expect(result.title).toBe('Meeting');
      expect(result.timezone).toBe('UTC');
    });
  });

  describe('AttendeeSchema', () => {
    it('should validate attendee', () => {
      const attendee = {
        email: 'attendee@example.com',
        name: 'Attendee Name',
      };
      
      const result = AttendeeSchema.parse(attendee);
      expect(result.email).toBe('attendee@example.com');
      expect(result.required).toBe(true);
    });

    it('should reject invalid email', () => {
      const attendee = {
        email: 'invalid-email',
      };
      
      const result = AttendeeSchema.safeParse(attendee);
      expect(result.success).toBe(false);
    });
  });

  describe('WorkingHoursSchema', () => {
    it('should validate working hours', () => {
      const hours = {
        start: '09:00',
        end: '17:00',
        timezone: 'America/New_York',
      };
      
      const result = WorkingHoursSchema.parse(hours);
      expect(result.start).toBe('09:00');
    });

    it('should reject invalid time format', () => {
      const hours = {
        start: '9:00',
        end: '17:00',
        timezone: 'UTC',
      };
      
      const result = WorkingHoursSchema.safeParse(hours);
      expect(result.success).toBe(false);
    });
  });
});

describe('Email Schemas', () => {
  describe('EmailAddressSchema', () => {
    it('should validate email address', () => {
      const addr = {
        email: 'test@example.com',
        name: 'Test User',
      };
      
      const result = EmailAddressSchema.parse(addr);
      expect(result.email).toBe('test@example.com');
      expect(result.name).toBe('Test User');
    });
  });

  describe('EmailSchema', () => {
    it('should validate email', () => {
      const email = {
        id: 'msg_123',
        from: { email: 'sender@example.com' },
        to: [{ email: 'recipient@example.com' }],
        subject: 'Test Subject',
        body: { text: 'Test content' },
        date: new Date().toISOString(),
      };
      
      const result = EmailSchema.parse(email);
      expect(result.subject).toBe('Test Subject');
      expect(result.to.length).toBe(1);
    });
  });

  describe('AttachmentSchema', () => {
    it('should validate attachment', () => {
      const attachment = {
        filename: 'test.pdf',
        content_type: 'application/pdf',
      };
      
      const result = AttachmentSchema.parse(attachment);
      expect(result.content_type).toBe('application/pdf');
    });

    it('should reject invalid content type', () => {
      const attachment = {
        filename: 'test.pdf',
        content_type: 'pdf',
      };
      
      const result = AttachmentSchema.safeParse(attachment);
      expect(result.success).toBe(false);
    });
  });
});

describe('Knowledge Schemas', () => {
  describe('DocumentSchema', () => {
    it('should validate document', () => {
      const doc = {
        id: 'kb_123',
        title: 'Test Document',
        content: 'Document content here',
        created_at: new Date().toISOString(),
      };
      
      const result = DocumentSchema.parse(doc);
      expect(result.title).toBe('Test Document');
      expect(result.published).toBe(false);
    });
  });

  describe('SearchRequestSchema', () => {
    it('should validate search request', () => {
      const request = {
        query: {
          text: 'password reset',
        },
      };
      
      const result = SearchRequestSchema.parse(request);
      expect(result.query.text).toBe('password reset');
    });
  });

  describe('IndexDocumentRequestSchema', () => {
    it('should validate index document request', () => {
      const request = {
        article: {
          title: 'Test Article',
          content: 'Article content',
        },
      };
      
      const result = IndexDocumentRequestSchema.parse(request);
      expect(result.article.title).toBe('Test Article');
    });
  });
});

describe('Agent Schemas', () => {
  describe('AgentConfigSchema', () => {
    it('should validate agent config', () => {
      const config = {
        agent_id: 'agent_001',
        name: 'Test Agent',
        role: 'specialist',
        system_prompt: 'You are a helpful assistant',
        capabilities: [
          {
            name: 'test_capability',
            description: 'Test capability',
          },
        ],
      };
      
      const result = AgentConfigSchema.parse(config);
      expect(result.agent_id).toBe('agent_001');
      expect(result.role).toBe('specialist');
      expect(result.temperature).toBe(0.7);
    });
  });

  describe('AgentStateSchema', () => {
    it('should validate agent state', () => {
      const state = {
        agent_id: 'agent_001',
        status: 'active',
        context: {},
        message_history: [],
        tools_used: [],
        started_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      
      const result = AgentStateSchema.parse(state);
      expect(result.status).toBe('active');
      expect(result.message_history.length).toBe(0);
    });
  });

  describe('WorkflowStepSchema', () => {
    it('should validate workflow step', () => {
      const step = {
        step_id: 'step_001',
        agent_id: 'agent_001',
        name: 'Test Step',
      };
      
      const result = WorkflowStepSchema.parse(step);
      expect(result.status).toBe('pending');
      expect(result.retry_count).toBe(0);
    });
  });

  describe('WorkflowSchema', () => {
    it('should validate workflow', () => {
      const workflow = {
        workflow_id: 'wf_001',
        name: 'Test Workflow',
        steps: [
          {
            step_id: 'step_001',
            agent_id: 'agent_001',
            name: 'Step 1',
          },
        ],
        context: {},
        created_at: new Date().toISOString(),
      };
      
      const result = WorkflowSchema.parse(workflow);
      expect(result.workflow_id).toBe('wf_001');
      expect(result.steps.length).toBe(1);
    });

    it('should reject workflow with no steps', () => {
      const workflow = {
        workflow_id: 'wf_001',
        name: 'Test Workflow',
        steps: [],
        context: {},
        created_at: new Date().toISOString(),
      };
      
      const result = WorkflowSchema.safeParse(workflow);
      expect(result.success).toBe(false);
    });
  });
});

describe('Serialization', () => {
  describe('Contact JSON round-trip', () => {
    it('should serialize and deserialize contact', () => {
      const contact = {
        id: 'cont_123',
        email: 'test@example.com',
        first_name: 'Test',
        created_at: new Date().toISOString(),
      };
      
      const parsed = ContactSchema.parse(contact);
      const json = JSON.stringify(parsed);
      const reparsed = ContactSchema.parse(JSON.parse(json));
      
      expect(reparsed.email).toBe(contact.email);
    });
  });

  describe('ActionEnvelope JSON round-trip', () => {
    it('should serialize and deserialize envelope', () => {
      const envelope = {
        action_id: 'act_123',
        tenant_id: 'tenant_001',
        timestamp: new Date().toISOString(),
        operation: 'test.operation',
        status: 'success',
      };
      
      const parsed = ActionEnvelopeSchema.parse(envelope);
      const json = JSON.stringify(parsed);
      const reparsed = ActionEnvelopeSchema.parse(JSON.parse(json));
      
      expect(reparsed.action_id).toBe(envelope.action_id);
    });
  });
});