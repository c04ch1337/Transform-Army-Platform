/**
 * Transform Army AI Schema Package - TypeScript/Zod Exports
 * 
 * This module exports all Zod schemas and TypeScript types for the
 * Transform Army AI platform.
 */

// Base exports
export * from './base';
export type {
  ActionEnvelope,
  ActionMetadata,
  ActionStatus,
  ErrorCode,
  ErrorDetails,
  ErrorResponse,
  HealthCheckResponse,
  PaginationParams,
  PaginationResponse,
  Priority,
  ProviderCredentials,
  TicketStatus,
  ToolInput,
  ToolResult,
} from './base';

// CRM exports
export * from './crm';
export type {
  Company,
  Contact,
  ContactData,
  ContactOptions,
  ContactSearchMatch,
  CreateContactRequest,
  CreateDealRequest,
  Deal,
  DealData,
  Note,
  NoteData,
  AddNoteRequest,
  SearchContactsRequest,
  SearchContactsResponse,
  UpdateContactRequest,
  UpdateDealRequest,
} from './crm';

// Helpdesk exports
export * from './helpdesk';
export type {
  AddCommentRequest,
  CommentAuthor,
  CommentData,
  CreateTicketRequest,
  SearchTicketsRequest,
  SearchTicketsResponse,
  Ticket,
  TicketComment,
  TicketData,
  TicketMetrics,
  TicketOptions,
  TicketRequester,
  TicketSearchMatch,
  UpdateTicketRequest,
} from './helpdesk';

// Calendar exports
export * from './calendar';
export type {
  Attendee,
  AvailabilityQuery,
  AvailableSlot,
  CalendarEvent,
  CheckAvailabilityRequest,
  CheckAvailabilityResponse,
  CreateEventRequest,
  DateRange,
  EventData,
  EventLocation,
  EventOptions,
  EventReminder,
  ListEventsRequest,
  ListEventsResponse,
  TimeSlot,
  UpdateEventRequest,
  WorkingHours,
} from './calendar';

// Email exports
export * from './email';
export type {
  Attachment,
  Email,
  EmailAddress,
  EmailBody,
  EmailData,
  EmailOptions,
  EmailSearchMatch,
  EmailThread,
  SearchEmailsRequest,
  SearchEmailsResponse,
  SendEmailRequest,
  SendEmailResponse,
} from './email';

// Knowledge exports
export * from './knowledge';
export type {
  ArticleData,
  Document,
  DocumentAnalytics,
  DocumentMetadata,
  IndexDocumentRequest,
  IndexOptions,
  ListDocumentsRequest,
  ListDocumentsResponse,
  SearchFilters,
  SearchOptions,
  SearchQuery,
  SearchRequest,
  SearchResponse,
  SearchResult,
} from './knowledge';

// Agent exports
export * from './agent';
export type {
  AgentCapability,
  AgentConfig,
  AgentMessage,
  AgentPerformanceMetrics,
  AgentRole,
  AgentState,
  AgentStatus,
  MessageRole,
  Workflow,
  WorkflowStatus,
  WorkflowStep,
  WorkflowStepConfig,
} from './agent';