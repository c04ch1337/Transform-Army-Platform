/**
 * Helpdesk schema definitions for Transform Army AI Adapter Service.
 * 
 * This module defines Zod schemas for helpdesk operations including tickets,
 * comments, and related functionality across different helpdesk providers.
 */

import { z } from 'zod';
import { ToolInputSchema, PaginationParamsSchema, PaginationResponseSchema, PrioritySchema, TicketStatusSchema } from './base';

/**
 * Information about the person requesting support.
 */
export const TicketRequesterSchema = z.object({
  email: z.string().email().describe('Requester email address'),
  name: z.string().optional().describe('Requester name'),
  phone: z.string().optional().describe('Requester phone number'),
  user_id: z.string().optional().describe('User ID in the system'),
});
export type TicketRequester = z.infer<typeof TicketRequesterSchema>;

/**
 * Helpdesk ticket model.
 */
export const TicketSchema = z.object({
  id: z.string().describe('Unique ticket identifier'),
  ticket_number: z.string().optional().describe('Human-readable ticket number'),
  subject: z.string().describe('Ticket subject/title'),
  description: z.string().describe('Ticket description/body'),
  status: TicketStatusSchema.describe('Ticket status'),
  priority: PrioritySchema.optional().describe('Ticket priority'),
  requester: TicketRequesterSchema.describe('Person requesting support'),
  assignee_id: z.string().optional().describe('ID of assigned agent'),
  assignee_name: z.string().optional().describe('Name of assigned agent'),
  tags: z.array(z.string()).optional().describe('Tags associated with the ticket'),
  url: z.string().url().optional().describe('URL to view ticket in provider system'),
  created_at: z.string().datetime().or(z.date()).describe('Ticket creation timestamp'),
  updated_at: z.string().datetime().or(z.date()).optional().describe('Last update timestamp'),
  resolved_at: z.string().datetime().or(z.date()).optional().describe('Resolution timestamp'),
  custom_fields: z.record(z.any()).optional().describe('Provider-specific custom fields'),
  due_date: z.string().datetime().or(z.date()).optional().describe('Ticket due date'),
  group_id: z.string().optional().describe('Support group/team ID'),
});
export type Ticket = z.infer<typeof TicketSchema>;

/**
 * Author of a ticket comment.
 */
export const CommentAuthorSchema = z.object({
  type: z.string().describe("Author type (e.g., 'agent', 'customer', 'system')"),
  id: z.string().describe('Author identifier'),
  name: z.string().optional().describe('Author name'),
  email: z.string().email().optional().describe('Author email'),
});
export type CommentAuthor = z.infer<typeof CommentAuthorSchema>;

/**
 * Comment/reply on a helpdesk ticket.
 */
export const TicketCommentSchema = z.object({
  id: z.string().describe('Unique comment identifier'),
  ticket_id: z.string().describe('Associated ticket ID'),
  body: z.string().describe('Comment body/content'),
  is_public: z.boolean().default(true).describe('Whether comment is visible to requester'),
  author: CommentAuthorSchema.describe('Comment author'),
  created_at: z.string().datetime().or(z.date()).describe('Comment creation timestamp'),
  attachments: z.array(z.string()).optional().describe('URLs of attached files'),
});
export type TicketComment = z.infer<typeof TicketCommentSchema>;

/**
 * Ticket data for creation.
 */
export const TicketDataSchema = z.object({
  subject: z.string().describe('Ticket subject'),
  description: z.string().describe('Ticket description'),
  requester: TicketRequesterSchema.describe('Person requesting support'),
  priority: PrioritySchema.optional().describe('Ticket priority'),
  status: TicketStatusSchema.default('new').describe('Initial ticket status'),
  tags: z.array(z.string()).optional().describe('Tags to apply'),
  assignee_id: z.string().optional().describe('Assign to specific agent'),
  group_id: z.string().optional().describe('Assign to specific group'),
  custom_fields: z.record(z.any()).optional().describe('Custom fields'),
  due_date: z.string().datetime().or(z.date()).optional().describe('Ticket due date'),
});
export type TicketData = z.infer<typeof TicketDataSchema>;

/**
 * Options for ticket creation.
 */
export const TicketOptionsSchema = z.object({
  send_notification: z.boolean().default(true).describe('Send notification to requester'),
  auto_assign: z.boolean().default(false).describe('Automatically assign to available agent'),
});
export type TicketOptions = z.infer<typeof TicketOptionsSchema>;

/**
 * Request to create a new helpdesk ticket.
 */
export const CreateTicketRequestSchema = ToolInputSchema.extend({
  ticket: TicketDataSchema.describe('Ticket data to create'),
  options: TicketOptionsSchema.optional().describe('Creation options'),
});
export type CreateTicketRequest = z.infer<typeof CreateTicketRequestSchema>;

/**
 * Request to update an existing helpdesk ticket.
 */
export const UpdateTicketRequestSchema = ToolInputSchema.extend({
  updates: z.record(z.any()).describe('Fields to update (partial update)'),
  resolution: z.string().optional().describe('Resolution notes when closing ticket'),
});
export type UpdateTicketRequest = z.infer<typeof UpdateTicketRequestSchema>;

/**
 * Comment data for creation.
 */
export const CommentDataSchema = z.object({
  body: z.string().describe('Comment body/content'),
  is_public: z.boolean().default(true).describe('Whether comment is visible to requester'),
  author: CommentAuthorSchema.describe('Comment author'),
  attachments: z.array(z.string()).optional().describe('URLs or base64-encoded file content'),
});
export type CommentData = z.infer<typeof CommentDataSchema>;

/**
 * Request to add a comment to a ticket.
 */
export const AddCommentRequestSchema = ToolInputSchema.extend({
  comment: CommentDataSchema.describe('Comment data to add'),
});
export type AddCommentRequest = z.infer<typeof AddCommentRequestSchema>;

/**
 * Request to search for helpdesk tickets.
 */
export const SearchTicketsRequestSchema = z.object({
  status: z.array(TicketStatusSchema).optional().describe('Filter by ticket status'),
  priority: z.array(PrioritySchema).optional().describe('Filter by priority'),
  assignee: z.string().optional().describe('Filter by assignee ID'),
  requester_email: z.string().email().optional().describe('Filter by requester email'),
  tags: z.array(z.string()).optional().describe('Filter by tags (any match)'),
  created_after: z.string().datetime().or(z.date()).optional().describe('Filter tickets created after this timestamp'),
  created_before: z.string().datetime().or(z.date()).optional().describe('Filter tickets created before this timestamp'),
  query: z.string().optional().describe('Full-text search query'),
  group_id: z.string().optional().describe('Filter by support group'),
  pagination: PaginationParamsSchema.optional().describe('Pagination parameters'),
});
export type SearchTicketsRequest = z.infer<typeof SearchTicketsRequestSchema>;

/**
 * A single ticket search result.
 */
export const TicketSearchMatchSchema = z.object({
  id: z.string().describe('Ticket ID'),
  ticket_number: z.string().optional().describe('Ticket number'),
  subject: z.string().describe('Ticket subject'),
  status: TicketStatusSchema.describe('Ticket status'),
  priority: PrioritySchema.optional().describe('Ticket priority'),
  requester_email: z.string().email().describe('Requester email'),
  requester_name: z.string().optional().describe('Requester name'),
  assignee_id: z.string().optional().describe('Assignee ID'),
  assignee_name: z.string().optional().describe('Assignee name'),
  tags: z.array(z.string()).optional().describe('Ticket tags'),
  created_at: z.string().datetime().or(z.date()).describe('Creation timestamp'),
  updated_at: z.string().datetime().or(z.date()).optional().describe('Last update timestamp'),
  url: z.string().url().optional().describe('URL to view in provider system'),
});
export type TicketSearchMatch = z.infer<typeof TicketSearchMatchSchema>;

/**
 * Response from ticket search operation.
 */
export const SearchTicketsResponseSchema = z.object({
  matches: z.array(TicketSearchMatchSchema).describe('Search results'),
  pagination: PaginationResponseSchema.optional().describe('Pagination metadata'),
});
export type SearchTicketsResponse = z.infer<typeof SearchTicketsResponseSchema>;

/**
 * Metrics and statistics for tickets.
 */
export const TicketMetricsSchema = z.object({
  total_tickets: z.number().int().describe('Total number of tickets'),
  open_tickets: z.number().int().describe('Number of open tickets'),
  pending_tickets: z.number().int().describe('Number of pending tickets'),
  solved_tickets: z.number().int().describe('Number of solved tickets'),
  average_resolution_time_hours: z.number().optional().describe('Average time to resolve tickets (hours)'),
  first_response_time_hours: z.number().optional().describe('Average time to first response (hours)'),
});
export type TicketMetrics = z.infer<typeof TicketMetricsSchema>;