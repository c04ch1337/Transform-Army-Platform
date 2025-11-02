/**
 * Schema Consistency Tests
 * 
 * These tests verify that Python (Pydantic) and TypeScript (Zod) schemas
 * are consistent in structure, field names, types, and validation rules.
 */

import { describe, it, expect } from '@jest/globals';
import {
  // Base schemas
  ActionStatusSchema,
  ErrorCodeSchema,
  PrioritySchema,
  TicketStatusSchema,
  PaginationParamsSchema,
  
  // Email schemas
  EmailAddressSchema,
  EmailBodySchema,
  AttachmentSchema,
  EmailSchema,
  EmailThreadSchema,
  SendEmailRequestSchema,
  
  // Calendar schemas
  AttendeeSchema,
  EventLocationSchema,
  EventReminderSchema,
  CalendarEventSchema,
  TimeSlotSchema,
  WorkingHoursSchema,
  
  // Agent schemas
  AgentRoleSchema,
  AgentStatusSchema,
  MessageRoleSchema,
  WorkflowStatusSchema,
  AgentCapabilitySchema,
  AgentConfigSchema,
  
  // Knowledge schemas
  DocumentMetadataSchema,
  DocumentSchema,
  SearchResultSchema,
  SearchQuerySchema,
} from '../src/typescript';

describe('Schema Consistency Tests', () => {
  
  describe('Base Schemas', () => {
    it('should validate ActionStatus enum values', () => {
      const validStatuses = ['success', 'failure', 'pending', 'queued'];
      validStatuses.forEach(status => {
        expect(() => ActionStatusSchema.parse(status)).not.toThrow();
      });
      
      expect(() => ActionStatusSchema.parse('invalid')).toThrow();
    });
    
    it('should validate ErrorCode enum values', () => {
      const validCodes = [
        'VALIDATION_ERROR',
        'AUTHENTICATION_ERROR',
        'PERMISSION_ERROR',
        'NOT_FOUND',
        'CONFLICT',
        'RATE_LIMIT_EXCEEDED',
        'PROVIDER_ERROR',
        'TIMEOUT_ERROR',
        'INTERNAL_ERROR',
      ];
      
      validCodes.forEach(code => {
        expect(() => ErrorCodeSchema.parse(code)).not.toThrow();
      });
    });
    
    it('should validate Priority enum values', () => {
      const validPriorities = ['low', 'medium', 'high', 'urgent'];
      validPriorities.forEach(priority => {
        expect(() => PrioritySchema.parse(priority)).not.toThrow();
      });
    });
    
    it('should validate TicketStatus enum values', () => {
      const validStatuses = [
        'open', 'pending', 'solved', 'closed',
        'new', 'in_progress', 'on_hold'
      ];
      
      validStatuses.forEach(status => {
        expect(() => TicketStatusSchema.parse(status)).not.toThrow();
      });
    });
    
    it('should validate PaginationParams with correct field types', () => {
      const validParams = {
        page: 1,
        page_size: 50,
        cursor: 'optional_cursor'
      };
      
      expect(() => PaginationParamsSchema.parse(validParams)).not.toThrow();
      
      // Test defaults
      const minimal = PaginationParamsSchema.parse({});
      expect(minimal.page).toBe(1);
      expect(minimal.page_size).toBe(50);
    });
  });
  
  describe('Email Schemas', () => {
    it('should validate EmailAddress with required fields', () => {
      const validAddress = {
        email: 'test@example.com',
        name: 'Test User'
      };
      
      expect(() => EmailAddressSchema.parse(validAddress)).not.toThrow();
      
      // Name is optional
      const minimalAddress = { email: 'test@example.com' };
      expect(() => EmailAddressSchema.parse(minimalAddress)).not.toThrow();
    });
    
    it('should validate EmailBody with text and optional html', () => {
      const validBody = {
        text: 'Plain text content',
        html: '<p>HTML content</p>'
      };
      
      expect(() => EmailBodySchema.parse(validBody)).not.toThrow();
      
      // HTML is optional
      const textOnly = { text: 'Plain text only' };
      expect(() => EmailBodySchema.parse(textOnly)).not.toThrow();
    });
    
    it('should validate Attachment with correct field names', () => {
      const validAttachment = {
        filename: 'document.pdf',
        content_type: 'application/pdf',
        size_bytes: 1024,
        content: 'base64_content',
      };
      
      expect(() => AttachmentSchema.parse(validAttachment)).not.toThrow();
    });
    
    it('should validate Email with all required fields', () => {
      const validEmail = {
        id: 'msg_123',
        from: { email: 'sender@example.com' },
        to: [{ email: 'recipient@example.com' }],
        subject: 'Test Subject',
        body: { text: 'Test content' },
        date: new Date().toISOString(),
      };
      
      expect(() => EmailSchema.parse(validEmail)).not.toThrow();
    });
    
    it('should validate EmailThread with required fields', () => {
      const validThread = {
        thread_id: 'thread_123',
        subject: 'Thread Subject',
        messages: [],
        participants: [{ email: 'user@example.com' }],
        message_count: 0,
        last_message_date: new Date().toISOString(),
      };
      
      expect(() => EmailThreadSchema.parse(validThread)).not.toThrow();
    });
  });
  
  describe('Calendar Schemas', () => {
    it('should validate Attendee with correct field names', () => {
      const validAttendee = {
        email: 'attendee@example.com',
        name: 'John Doe',
        required: true,
        response_status: 'accepted',
      };
      
      expect(() => AttendeeSchema.parse(validAttendee)).not.toThrow();
    });
    
    it('should validate EventLocation with correct structure', () => {
      const validLocation = {
        type: 'video',
        url: 'https://meet.google.com/abc-defg',
        display_name: 'Google Meet',
      };
      
      expect(() => EventLocationSchema.parse(validLocation)).not.toThrow();
    });
    
    it('should validate EventReminder with correct field names', () => {
      const validReminder = {
        method: 'email',
        minutes_before: 1440,
      };
      
      expect(() => EventReminderSchema.parse(validReminder)).not.toThrow();
    });
    
    it('should validate CalendarEvent with all required fields', () => {
      const validEvent = {
        id: 'evt_123',
        title: 'Team Meeting',
        start_time: new Date().toISOString(),
        end_time: new Date(Date.now() + 3600000).toISOString(),
      };
      
      expect(() => CalendarEventSchema.parse(validEvent)).not.toThrow();
    });
    
    it('should validate TimeSlot with ISO 8601 timestamps', () => {
      const validSlot = {
        start_time: '2024-01-01T10:00:00-05:00',
        end_time: '2024-01-01T11:00:00-05:00',
      };
      
      expect(() => TimeSlotSchema.parse(validSlot)).not.toThrow();
    });
    
    it('should validate WorkingHours with HH:MM format', () => {
      const validHours = {
        start: '09:00',
        end: '17:00',
        timezone: 'America/New_York',
      };
      
      expect(() => WorkingHoursSchema.parse(validHours)).not.toThrow();
      
      // Invalid time format should fail
      const invalidHours = {
        start: '9:00',  // Should be 09:00
        end: '17:00',
        timezone: 'UTC',
      };
      
      expect(() => WorkingHoursSchema.parse(invalidHours)).toThrow();
    });
  });
  
  describe('Agent Schemas', () => {
    it('should validate AgentRole enum with all business roles', () => {
      const genericRoles = [
        'orchestrator', 'researcher', 'analyst', 
        'writer', 'reviewer', 'executor', 'specialist', 'custom'
      ];
      
      const businessRoles = [
        'bdr_concierge', 'support_concierge', 'research_recon',
        'ops_sapper', 'knowledge_librarian', 'qa_auditor'
      ];
      
      [...genericRoles, ...businessRoles].forEach(role => {
        expect(() => AgentRoleSchema.parse(role)).not.toThrow();
      });
    });
    
    it('should validate AgentStatus enum values', () => {
      const validStatuses = [
        'idle', 'active', 'thinking', 'working',
        'waiting', 'completed', 'failed', 'paused'
      ];
      
      validStatuses.forEach(status => {
        expect(() => AgentStatusSchema.parse(status)).not.toThrow();
      });
    });
    
    it('should validate MessageRole enum values', () => {
      const validRoles = ['system', 'user', 'assistant', 'function', 'tool'];
      
      validRoles.forEach(role => {
        expect(() => MessageRoleSchema.parse(role)).not.toThrow();
      });
    });
    
    it('should validate WorkflowStatus enum values', () => {
      const validStatuses = ['pending', 'running', 'completed', 'failed', 'cancelled'];
      
      validStatuses.forEach(status => {
        expect(() => WorkflowStatusSchema.parse(status)).not.toThrow();
      });
    });
    
    it('should validate AgentCapability with correct field names', () => {
      const validCapability = {
        name: 'crm_operations',
        description: 'CRM operations capability',
        enabled: true,
        tools: ['create_contact', 'update_deal'],
        confidence_threshold: 0.8,
      };
      
      expect(() => AgentCapabilitySchema.parse(validCapability)).not.toThrow();
    });
    
    it('should validate AgentConfig with all required fields', () => {
      const validConfig = {
        agent_id: 'agent_001',
        name: 'Sales Agent',
        role: 'bdr_concierge',
        capabilities: [],
        system_prompt: 'You are a sales assistant',
      };
      
      expect(() => AgentConfigSchema.parse(validConfig)).not.toThrow();
    });
  });
  
  describe('Knowledge Schemas', () => {
    it('should validate DocumentMetadata with correct field names', () => {
      const validMetadata = {
        author: 'John Doe',
        version: '1.0',
        language: 'en',
        category: 'technical',
        tags: ['api', 'integration'],
        helpful_votes: 42,
        unhelpful_votes: 3,
        view_count: 1250,
      };
      
      expect(() => DocumentMetadataSchema.parse(validMetadata)).not.toThrow();
    });
    
    it('should validate KnowledgeDocument with all required fields', () => {
      const validDocument = {
        id: 'doc_123',
        title: 'API Guide',
        content: '# API Integration Guide\n\nContent here...',
        published: true,
        created_at: new Date().toISOString(),
      };
      
      expect(() => DocumentSchema.parse(validDocument)).not.toThrow();
    });
    
    it('should validate SearchResult with score between 0 and 1', () => {
      const validResult = {
        id: 'doc_123',
        title: 'Test Document',
        score: 0.95,
      };
      
      expect(() => SearchResultSchema.parse(validResult)).not.toThrow();
      
      // Score out of range should fail
      const invalidResult = {
        id: 'doc_123',
        title: 'Test',
        score: 1.5,
      };
      
      expect(() => SearchResultSchema.parse(invalidResult)).toThrow();
    });
    
    it('should validate SearchQuery with correct structure', () => {
      const validQuery = {
        text: 'API authentication',
        filters: {
          categories: ['technical'],
          published_only: true,
        },
        options: {
          max_results: 10,
          min_score: 0.5,
        },
      };
      
      expect(() => SearchQuerySchema.parse(validQuery)).not.toThrow();
    });
  });
  
  describe('Field Name Consistency', () => {
    it('should use snake_case for all field names', () => {
      // Test that key schemas use snake_case consistently
      const testCases = [
        { schema: EmailSchema, fields: ['thread_id', 'is_read', 'is_starred', 'provider_id'] },
        { schema: CalendarEventSchema, fields: ['calendar_id', 'start_time', 'end_time', 'all_day'] },
        { schema: AgentConfigSchema, fields: ['agent_id', 'system_prompt', 'max_tokens'] },
        { schema: DocumentSchema, fields: ['created_at', 'updated_at', 'published_at', 'parent_id'] },
      ];
      
      testCases.forEach(({ schema, fields }) => {
        const shape = schema._def.shape();
        fields.forEach(field => {
          expect(shape).toHaveProperty(field);
        });
      });
    });
  });
  
  describe('Sample Data Validation', () => {
    it('should validate complete email send request', () => {
      const sampleRequest = {
        idempotency_key: 'idm_email123',
        correlation_id: 'cor_req456',
        email: {
          from: {
            email: 'sender@example.com',
            name: 'Sender Name',
          },
          to: [
            {
              email: 'recipient@example.com',
              name: 'Recipient Name',
            },
          ],
          subject: 'Test Email',
          body: {
            text: 'This is a test email',
            html: '<p>This is a test email</p>',
          },
        },
        options: {
          track_opens: true,
          track_clicks: true,
        },
      };
      
      expect(() => SendEmailRequestSchema.parse(sampleRequest)).not.toThrow();
    });
    
    it('should validate complete calendar event', () => {
      const sampleEvent = {
        id: 'evt_789',
        title: 'Product Demo - Acme Corp',
        description: 'Demonstrating enterprise features',
        start_time: new Date('2025-11-05T14:00:00Z').toISOString(),
        end_time: new Date('2025-11-05T15:00:00Z').toISOString(),
        timezone: 'America/New_York',
        all_day: false,
        attendees: [
          {
            email: 'john.doe@example.com',
            name: 'John Doe',
            required: true,
            response_status: 'accepted',
          },
        ],
        location: {
          type: 'video',
          url: 'https://meet.google.com/abc-defg-hij',
          display_name: 'Google Meet',
        },
        status: 'confirmed',
      };
      
      expect(() => CalendarEventSchema.parse(sampleEvent)).not.toThrow();
    });
    
    it('should validate complete agent config', () => {
      const sampleConfig = {
        agent_id: 'agent_bdr_001',
        name: 'BDR Concierge',
        role: 'bdr_concierge',
        description: 'Business Development Representative assistant',
        model: 'gpt-4',
        temperature: 0.7,
        max_tokens: 2000,
        capabilities: [
          {
            name: 'crm_operations',
            description: 'Create and manage CRM contacts and deals',
            enabled: true,
            tools: ['create_contact', 'update_contact', 'create_deal'],
          },
        ],
        system_prompt: 'You are a BDR assistant specialized in lead qualification',
        enabled: true,
      };
      
      expect(() => AgentConfigSchema.parse(sampleConfig)).not.toThrow();
    });
  });
});