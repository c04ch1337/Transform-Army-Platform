/**
 * Base schema definitions for Transform Army AI Adapter Service.
 * 
 * This module defines Zod schemas for foundational data structures used across
 * all adapter operations, including action envelopes, error responses, and
 * common data structures.
 */

import { z } from 'zod';

/**
 * Status of an action execution.
 */
export const ActionStatusSchema = z.enum([
  'success',
  'failure',
  'pending',
  'queued',
]);
export type ActionStatus = z.infer<typeof ActionStatusSchema>;

/**
 * Standard error codes for adapter operations.
 */
export const ErrorCodeSchema = z.enum([
  'VALIDATION_ERROR',
  'AUTHENTICATION_ERROR',
  'PERMISSION_ERROR',
  'NOT_FOUND',
  'CONFLICT',
  'RATE_LIMIT_EXCEEDED',
  'PROVIDER_ERROR',
  'TIMEOUT_ERROR',
  'INTERNAL_ERROR',
]);
export type ErrorCode = z.infer<typeof ErrorCodeSchema>;

/**
 * Priority levels for tasks, tickets, etc.
 */
export const PrioritySchema = z.enum(['low', 'medium', 'high', 'urgent']);
export type Priority = z.infer<typeof PrioritySchema>;

/**
 * Status values for helpdesk tickets.
 */
export const TicketStatusSchema = z.enum([
  'open',
  'pending',
  'solved',
  'closed',
  'new',
  'in_progress',
  'on_hold',
]);
export type TicketStatus = z.infer<typeof TicketStatusSchema>;

/**
 * Parameters for paginating list results.
 */
export const PaginationParamsSchema = z.object({
  page: z.number().int().min(1).default(1).describe('Page number (1-indexed)'),
  page_size: z
    .number()
    .int()
    .min(1)
    .max(100)
    .default(50)
    .describe('Number of items per page (max 100)'),
  cursor: z
    .string()
    .optional()
    .describe('Opaque cursor for cursor-based pagination'),
});
export type PaginationParams = z.infer<typeof PaginationParamsSchema>;

/**
 * Pagination metadata in response.
 */
export const PaginationResponseSchema = z.object({
  page: z.number().int().describe('Current page number'),
  page_size: z.number().int().describe('Items per page'),
  total_pages: z.number().int().describe('Total number of pages'),
  total_items: z.number().int().describe('Total number of items'),
  has_next: z.boolean().describe('Whether there is a next page'),
  has_previous: z.boolean().describe('Whether there is a previous page'),
  next_cursor: z.string().optional().describe('Cursor for next page'),
});
export type PaginationResponse = z.infer<typeof PaginationResponseSchema>;

/**
 * Additional details about an error.
 */
export const ErrorDetailsSchema = z
  .object({
    field: z.string().optional().describe('Field that caused the error'),
    issue: z.string().optional().describe('Description of the issue'),
    value: z.any().optional().describe('Invalid value that caused the error'),
    provider: z.string().optional().describe('Provider that reported the error'),
    provider_error: z
      .string()
      .optional()
      .describe('Original error message from provider'),
  })
  .passthrough();
export type ErrorDetails = z.infer<typeof ErrorDetailsSchema>;

/**
 * Standardized error response format.
 */
export const ErrorResponseSchema = z.object({
  code: ErrorCodeSchema.describe('Error code'),
  message: z.string().describe('Human-readable error message'),
  details: ErrorDetailsSchema.optional().describe('Additional error details'),
  correlation_id: z
    .string()
    .optional()
    .describe('Correlation ID for request tracing'),
  timestamp: z
    .string()
    .datetime()
    .or(z.date())
    .describe('Error timestamp'),
  retry_after: z
    .number()
    .int()
    .optional()
    .describe('Seconds to wait before retrying (for rate limits)'),
  documentation_url: z
    .string()
    .url()
    .optional()
    .describe('URL to error documentation'),
});
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;

/**
 * Metadata about action execution.
 */
export const ActionMetadataSchema = z
  .object({
    idempotency_key: z
      .string()
      .optional()
      .describe('Idempotency key for safe retries'),
    retry_count: z.number().int().default(0).describe('Number of retries attempted'),
    provider_request_id: z
      .string()
      .optional()
      .describe('Request ID from provider API'),
  })
  .passthrough();
export type ActionMetadata = z.infer<typeof ActionMetadataSchema>;

/**
 * Generic structure for tool/action results.
 */
export const ToolResultSchema = z
  .object({
    id: z.string().describe('Resource ID'),
    provider: z.string().describe("Provider name (e.g., 'hubspot', 'zendesk')"),
    provider_id: z.string().describe("ID in provider's system"),
    data: z.any().describe('Result data specific to the operation'),
  })
  .passthrough();
export type ToolResult = z.infer<typeof ToolResultSchema>;

/**
 * Standardized envelope for all adapter operations.
 * 
 * This wraps every request/response to provide consistent structure,
 * tracing, and metadata across all operations.
 */
export const ActionEnvelopeSchema = z.object({
  action_id: z.string().describe('Unique identifier for this action'),
  correlation_id: z
    .string()
    .optional()
    .describe('Correlation ID for distributed tracing'),
  tenant_id: z.string().describe('Tenant identifier'),
  timestamp: z
    .string()
    .datetime()
    .or(z.date())
    .describe('Action execution timestamp'),
  operation: z.string().describe("Operation name (e.g., 'crm.contact.create')"),
  status: ActionStatusSchema.describe('Action execution status'),
  duration_ms: z
    .number()
    .int()
    .min(0)
    .optional()
    .describe('Execution duration in milliseconds'),
  result: z.any().optional().describe('Operation result data'),
  error: ErrorResponseSchema.optional().describe("Error details if status is 'failure'"),
  metadata: ActionMetadataSchema.optional().describe('Additional metadata about the action'),
});
export type ActionEnvelope = z.infer<typeof ActionEnvelopeSchema>;

/**
 * Generic structure for tool/action input.
 */
export const ToolInputSchema = z
  .object({
    idempotency_key: z
      .string()
      .max(255)
      .optional()
      .describe('Idempotency key for safe retries (valid for 24 hours)'),
    correlation_id: z
      .string()
      .optional()
      .describe('Correlation ID for request tracing'),
  })
  .passthrough();
export type ToolInput = z.infer<typeof ToolInputSchema>;

/**
 * Provider-specific credentials.
 */
export const ProviderCredentialsSchema = z
  .object({
    provider_name: z
      .string()
      .describe("Name of the provider (e.g., 'hubspot', 'zendesk')"),
    api_key: z.string().optional().describe('API key for authentication'),
    api_secret: z.string().optional().describe('API secret for authentication'),
    access_token: z.string().optional().describe('OAuth access token'),
    refresh_token: z.string().optional().describe('OAuth refresh token'),
    expires_at: z
      .string()
      .datetime()
      .or(z.date())
      .optional()
      .describe('Token expiration timestamp'),
  })
  .passthrough();
export type ProviderCredentials = z.infer<typeof ProviderCredentialsSchema>;

/**
 * Health check response format.
 */
export const HealthCheckResponseSchema = z.object({
  status: z.string().describe('Overall health status'),
  timestamp: z
    .string()
    .datetime()
    .or(z.date())
    .describe('Health check timestamp'),
  version: z.string().describe('API version'),
  providers: z
    .record(z.string())
    .optional()
    .describe('Health status of individual providers'),
});
export type HealthCheckResponse = z.infer<typeof HealthCheckResponseSchema>;