/**
 * Email schema definitions for Transform Army AI Adapter Service.
 * 
 * This module defines Zod schemas for email operations including sending emails,
 * managing attachments, and searching email threads.
 */

import { z } from 'zod';
import { ToolInputSchema, PaginationParamsSchema, PaginationResponseSchema } from './base';

/**
 * Email address with optional name.
 */
export const EmailAddressSchema = z.object({
  email: z.string().email().describe('Email address'),
  name: z.string().optional().describe('Display name'),
});
export type EmailAddress = z.infer<typeof EmailAddressSchema>;

/**
 * Email body content in text and HTML formats.
 */
export const EmailBodySchema = z.object({
  text: z.string().describe('Plain text version of email body'),
  html: z.string().optional().describe('HTML version of email body'),
});
export type EmailBody = z.infer<typeof EmailBodySchema>;

/**
 * Email attachment model.
 */
export const AttachmentSchema = z.object({
  filename: z.string().describe('Attachment filename'),
  content_type: z.string().describe("MIME type (e.g., 'application/pdf', 'image/png')"),
  size_bytes: z.number().int().min(0).optional().describe('Attachment size in bytes'),
  content: z.string().optional().describe('Base64-encoded content or URL to content'),
  url: z.string().url().optional().describe('URL to download attachment'),
  attachment_id: z.string().optional().describe('Provider-specific attachment ID'),
});
export type Attachment = z.infer<typeof AttachmentSchema>;

/**
 * Email message model.
 */
export const EmailSchema = z.object({
  id: z.string().describe('Unique message identifier'),
  thread_id: z.string().optional().describe('Thread identifier'),
  from: EmailAddressSchema.describe('Sender email address'),
  to: z.array(EmailAddressSchema).describe('Recipient email addresses'),
  cc: z.array(EmailAddressSchema).optional().describe('CC recipients'),
  bcc: z.array(EmailAddressSchema).optional().describe('BCC recipients'),
  reply_to: EmailAddressSchema.optional().describe('Reply-to address'),
  subject: z.string().describe('Email subject'),
  body: EmailBodySchema.describe('Email body content'),
  date: z.string().datetime().or(z.date()).describe('Email date/time'),
  snippet: z.string().optional().describe('Short preview of email content'),
  attachments: z.array(AttachmentSchema).optional().describe('Email attachments'),
  labels: z.array(z.string()).optional().describe("Labels/folders (e.g., 'INBOX', 'SENT', 'IMPORTANT')"),
  is_read: z.boolean().default(false).describe('Whether email has been read'),
  is_starred: z.boolean().default(false).describe('Whether email is starred/flagged'),
  headers: z.record(z.string()).optional().describe('Custom email headers'),
  provider_id: z.string().optional().describe('Provider-specific message ID'),
});
export type Email = z.infer<typeof EmailSchema>;

/**
 * Email data for sending.
 */
export const EmailDataSchema = z.object({
  from: EmailAddressSchema.describe('Sender email address'),
  to: z.array(EmailAddressSchema).min(1).describe('Recipient email addresses'),
  cc: z.array(EmailAddressSchema).optional().describe('CC recipients'),
  bcc: z.array(EmailAddressSchema).optional().describe('BCC recipients'),
  reply_to: EmailAddressSchema.optional().describe('Reply-to address'),
  subject: z.string().describe('Email subject'),
  body: EmailBodySchema.describe('Email body'),
  attachments: z.array(AttachmentSchema).optional().describe('Email attachments'),
  headers: z.record(z.string()).optional().describe('Custom email headers'),
});
export type EmailData = z.infer<typeof EmailDataSchema>;

/**
 * Options for sending email.
 */
export const EmailOptionsSchema = z.object({
  track_opens: z.boolean().default(false).describe('Track when email is opened'),
  track_clicks: z.boolean().default(false).describe('Track link clicks in email'),
  send_at: z.string().datetime().or(z.date()).optional().describe('Schedule email for future delivery'),
  priority: z.string().optional().describe("Email priority (e.g., 'high', 'normal', 'low')"),
});
export type EmailOptions = z.infer<typeof EmailOptionsSchema>;

/**
 * Request to send an email.
 */
export const SendEmailRequestSchema = ToolInputSchema.extend({
  email: EmailDataSchema.describe('Email data to send'),
  options: EmailOptionsSchema.optional().describe('Sending options'),
});
export type SendEmailRequest = z.infer<typeof SendEmailRequestSchema>;

/**
 * Email thread model.
 */
export const EmailThreadSchema = z.object({
  thread_id: z.string().describe('Thread identifier'),
  subject: z.string().describe('Thread subject'),
  messages: z.array(EmailSchema).describe('Messages in thread'),
  participants: z.array(EmailAddressSchema).describe('All participants in thread'),
  message_count: z.number().int().min(0).describe('Number of messages in thread'),
  is_read: z.boolean().default(false).describe('Whether all messages are read'),
  labels: z.array(z.string()).optional().describe('Thread labels'),
  last_message_date: z.string().datetime().or(z.date()).describe('Date of most recent message'),
});
export type EmailThread = z.infer<typeof EmailThreadSchema>;

/**
 * Request to search for emails.
 */
export const SearchEmailsRequestSchema = z.object({
  query: z.string().optional().describe('Full-text search query'),
  from_email: z.string().email().optional().describe('Filter by sender email'),
  to_email: z.string().email().optional().describe('Filter by recipient email'),
  subject: z.string().optional().describe('Filter by subject (partial match)'),
  has_attachments: z.boolean().optional().describe('Filter messages with/without attachments'),
  labels: z.array(z.string()).optional().describe("Filter by labels (e.g., ['INBOX', 'IMPORTANT'])"),
  is_read: z.boolean().optional().describe('Filter by read status'),
  is_starred: z.boolean().optional().describe('Filter by starred status'),
  date_after: z.string().datetime().or(z.date()).optional().describe('Filter messages after this date'),
  date_before: z.string().datetime().or(z.date()).optional().describe('Filter messages before this date'),
  thread_id: z.string().optional().describe('Filter by thread ID'),
  pagination: PaginationParamsSchema.optional().describe('Pagination parameters'),
});
export type SearchEmailsRequest = z.infer<typeof SearchEmailsRequestSchema>;

/**
 * A single email search result.
 */
export const EmailSearchMatchSchema = z.object({
  id: z.string().describe('Message ID'),
  thread_id: z.string().optional().describe('Thread ID'),
  from: EmailAddressSchema.describe('Sender'),
  to: z.array(EmailAddressSchema).describe('Recipients'),
  subject: z.string().describe('Email subject'),
  snippet: z.string().describe('Email preview snippet'),
  date: z.string().datetime().or(z.date()).describe('Email date'),
  labels: z.array(z.string()).optional().describe('Email labels'),
  is_read: z.boolean().describe('Read status'),
  is_starred: z.boolean().default(false).describe('Starred status'),
  has_attachments: z.boolean().default(false).describe('Whether email has attachments'),
});
export type EmailSearchMatch = z.infer<typeof EmailSearchMatchSchema>;

/**
 * Response from email search operation.
 */
export const SearchEmailsResponseSchema = z.object({
  matches: z.array(EmailSearchMatchSchema).describe('Search results'),
  pagination: PaginationResponseSchema.optional().describe('Pagination metadata'),
});
export type SearchEmailsResponse = z.infer<typeof SearchEmailsResponseSchema>;

/**
 * Response from send email operation.
 */
export const SendEmailResponseSchema = z.object({
  message_id: z.string().describe('Internal message ID'),
  thread_id: z.string().optional().describe('Thread ID if part of thread'),
  provider: z.string().describe('Email provider used'),
  provider_message_id: z.string().describe("Provider's message ID"),
  scheduled_for: z.string().datetime().or(z.date()).optional().describe('Scheduled delivery time'),
  estimated_delivery: z.string().datetime().or(z.date()).optional().describe('Estimated delivery time'),
  status: z.string().describe("Email status (e.g., 'queued', 'sent', 'delivered')"),
});
export type SendEmailResponse = z.infer<typeof SendEmailResponseSchema>;