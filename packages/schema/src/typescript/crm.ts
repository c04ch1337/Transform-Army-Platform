/**
 * CRM schema definitions for Transform Army AI Adapter Service.
 * 
 * This module defines Zod schemas for CRM operations including contacts,
 * companies, deals, and notes across different CRM providers.
 */

import { z } from 'zod';
import { ToolInputSchema, PaginationParamsSchema, PaginationResponseSchema } from './base';

/**
 * CRM contact model representing a person in the CRM system.
 */
export const ContactSchema = z.object({
  id: z.string().describe('Unique contact identifier'),
  email: z.string().email().describe('Contact email address'),
  first_name: z.string().optional().describe('Contact first name'),
  last_name: z.string().optional().describe('Contact last name'),
  company: z.string().optional().describe('Company name'),
  phone: z.string().optional().describe('Phone number'),
  title: z.string().optional().describe('Job title'),
  url: z.string().url().optional().describe('URL to view contact in provider system'),
  created_at: z.string().datetime().or(z.date()).optional().describe('Contact creation timestamp'),
  updated_at: z.string().datetime().or(z.date()).optional().describe('Last update timestamp'),
  custom_fields: z.record(z.any()).optional().describe('Provider-specific custom fields'),
  owner_id: z.string().optional().describe('ID of the contact owner/assignee'),
  tags: z.array(z.string()).optional().describe('Tags associated with the contact'),
});
export type Contact = z.infer<typeof ContactSchema>;

/**
 * CRM company/account model.
 */
export const CompanySchema = z.object({
  id: z.string().describe('Unique company identifier'),
  name: z.string().describe('Company name'),
  domain: z.string().optional().describe('Company website domain'),
  industry: z.string().optional().describe('Industry/sector'),
  employees: z.number().int().min(0).optional().describe('Number of employees'),
  annual_revenue: z.number().min(0).optional().describe('Annual revenue'),
  phone: z.string().optional().describe('Company phone number'),
  address: z.string().optional().describe('Company address'),
  city: z.string().optional().describe('City'),
  state: z.string().optional().describe('State/province'),
  country: z.string().optional().describe('Country'),
  postal_code: z.string().optional().describe('Postal/ZIP code'),
  url: z.string().url().optional().describe('URL to view company in provider system'),
  created_at: z.string().datetime().or(z.date()).optional().describe('Company creation timestamp'),
  updated_at: z.string().datetime().or(z.date()).optional().describe('Last update timestamp'),
  custom_fields: z.record(z.any()).optional().describe('Provider-specific custom fields'),
});
export type Company = z.infer<typeof CompanySchema>;

/**
 * CRM deal/opportunity model.
 */
export const DealSchema = z.object({
  id: z.string().describe('Unique deal identifier'),
  name: z.string().describe('Deal name'),
  amount: z.number().min(0).optional().describe('Deal amount/value'),
  currency: z.string().length(3).default('USD').describe('Currency code (ISO 4217)'),
  stage: z.string().describe('Current deal stage/status'),
  probability: z.number().min(0).max(1).optional().describe('Win probability (0-1)'),
  close_date: z.string().optional().describe('Expected close date (YYYY-MM-DD)'),
  contact_ids: z.array(z.string()).optional().describe('Associated contact IDs'),
  company_id: z.string().optional().describe('Associated company ID'),
  owner_id: z.string().optional().describe('Deal owner/assignee ID'),
  url: z.string().url().optional().describe('URL to view deal in provider system'),
  created_at: z.string().datetime().or(z.date()).optional().describe('Deal creation timestamp'),
  updated_at: z.string().datetime().or(z.date()).optional().describe('Last update timestamp'),
  custom_fields: z.record(z.any()).optional().describe('Provider-specific custom fields'),
});
export type Deal = z.infer<typeof DealSchema>;

/**
 * CRM note/activity model.
 */
export const NoteSchema = z.object({
  id: z.string().describe('Unique note identifier'),
  content: z.string().describe('Note content/body'),
  type: z.string().optional().describe("Note type (e.g., 'call_note', 'email', 'meeting')"),
  contact_id: z.string().optional().describe('Associated contact ID'),
  company_id: z.string().optional().describe('Associated company ID'),
  deal_id: z.string().optional().describe('Associated deal ID'),
  author_id: z.string().optional().describe('Note author/creator ID'),
  timestamp: z.string().datetime().or(z.date()).optional().describe('Note timestamp (when the activity occurred)'),
  created_at: z.string().datetime().or(z.date()).optional().describe('Note creation timestamp in system'),
});
export type Note = z.infer<typeof NoteSchema>;

/**
 * Contact data for creation.
 */
export const ContactDataSchema = z.object({
  email: z.string().email().describe('Contact email (required)'),
  first_name: z.string().optional().describe('First name'),
  last_name: z.string().optional().describe('Last name'),
  company: z.string().optional().describe('Company name'),
  phone: z.string().optional().describe('Phone number'),
  title: z.string().optional().describe('Job title'),
  owner_id: z.string().optional().describe('Owner ID'),
  tags: z.array(z.string()).optional().describe('Tags'),
  custom_fields: z.record(z.any()).optional().describe('Custom fields'),
});
export type ContactData = z.infer<typeof ContactDataSchema>;

/**
 * Options for contact creation.
 */
export const ContactOptionsSchema = z.object({
  dedupe_by: z.array(z.string()).optional().describe("Fields to check for duplicates (e.g., ['email'])"),
  update_if_exists: z.boolean().default(false).describe('Update contact if duplicate found'),
});
export type ContactOptions = z.infer<typeof ContactOptionsSchema>;

/**
 * Request to create a new CRM contact.
 */
export const CreateContactRequestSchema = ToolInputSchema.extend({
  contact: ContactDataSchema.describe('Contact data to create'),
  options: ContactOptionsSchema.optional().describe('Creation options'),
});
export type CreateContactRequest = z.infer<typeof CreateContactRequestSchema>;

/**
 * Request to update an existing CRM contact.
 */
export const UpdateContactRequestSchema = ToolInputSchema.extend({
  updates: z.record(z.any()).describe('Fields to update (partial update)'),
});
export type UpdateContactRequest = z.infer<typeof UpdateContactRequestSchema>;

/**
 * Deal data for creation.
 */
export const DealDataSchema = z.object({
  name: z.string().describe('Deal name'),
  amount: z.number().min(0).optional().describe('Deal amount'),
  currency: z.string().length(3).default('USD').describe('Currency code'),
  stage: z.string().describe('Deal stage'),
  probability: z.number().min(0).max(1).optional().describe('Win probability'),
  close_date: z.string().optional().describe('Expected close date (YYYY-MM-DD)'),
  contact_ids: z.array(z.string()).optional().describe('Associated contact IDs'),
  company_id: z.string().optional().describe('Associated company ID'),
  owner_id: z.string().optional().describe('Deal owner ID'),
  custom_fields: z.record(z.any()).optional().describe('Custom fields'),
});
export type DealData = z.infer<typeof DealDataSchema>;

/**
 * Request to create a new CRM deal/opportunity.
 */
export const CreateDealRequestSchema = ToolInputSchema.extend({
  deal: DealDataSchema.describe('Deal data to create'),
});
export type CreateDealRequest = z.infer<typeof CreateDealRequestSchema>;

/**
 * Request to update an existing CRM deal.
 */
export const UpdateDealRequestSchema = ToolInputSchema.extend({
  updates: z.record(z.any()).describe('Fields to update (partial update)'),
});
export type UpdateDealRequest = z.infer<typeof UpdateDealRequestSchema>;

/**
 * Note data for creation.
 */
export const NoteDataSchema = z.object({
  content: z.string().describe('Note content'),
  type: z.string().optional().describe('Note type'),
  timestamp: z.string().datetime().or(z.date()).optional().describe('When the activity occurred'),
});
export type NoteData = z.infer<typeof NoteDataSchema>;

/**
 * Request to add a note to a CRM entity.
 */
export const AddNoteRequestSchema = ToolInputSchema.extend({
  note: NoteDataSchema.describe('Note data to create'),
});
export type AddNoteRequest = z.infer<typeof AddNoteRequestSchema>;

/**
 * Request to search for CRM contacts.
 */
export const SearchContactsRequestSchema = z.object({
  query: z.string().optional().describe('Search query string'),
  fields: z.array(z.string()).optional().describe('Fields to return in results'),
  filters: z.record(z.any()).optional().describe('Additional filters to apply'),
  pagination: PaginationParamsSchema.optional().describe('Pagination parameters'),
});
export type SearchContactsRequest = z.infer<typeof SearchContactsRequestSchema>;

/**
 * A single contact search result with relevance score.
 */
export const ContactSearchMatchSchema = z.object({
  id: z.string().describe('Contact ID'),
  email: z.string().email().describe('Contact email'),
  first_name: z.string().optional().describe('First name'),
  last_name: z.string().optional().describe('Last name'),
  company: z.string().optional().describe('Company'),
  title: z.string().optional().describe('Job title'),
  phone: z.string().optional().describe('Phone'),
  score: z.number().min(0).max(1).describe('Relevance score (0-1)'),
  url: z.string().url().optional().describe('URL to view in provider system'),
});
export type ContactSearchMatch = z.infer<typeof ContactSearchMatchSchema>;

/**
 * Response from contact search operation.
 */
export const SearchContactsResponseSchema = z.object({
  matches: z.array(ContactSearchMatchSchema).describe('Search results'),
  pagination: PaginationResponseSchema.optional().describe('Pagination metadata'),
});
export type SearchContactsResponse = z.infer<typeof SearchContactsResponseSchema>;