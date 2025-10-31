/**
 * Calendar schema definitions for Transform Army AI Adapter Service.
 * 
 * This module defines Zod schemas for calendar operations including events,
 * attendees, availability checks, and related functionality.
 */

import { z } from 'zod';
import { ToolInputSchema, PaginationParamsSchema, PaginationResponseSchema } from './base';

/**
 * Location information for a calendar event.
 */
export const EventLocationSchema = z.object({
  type: z.string().describe("Location type (e.g., 'physical', 'video', 'phone')"),
  url: z.string().url().optional().describe('URL for video/online meetings'),
  display_name: z.string().optional().describe('Display name for the location'),
  address: z.string().optional().describe('Physical address'),
  phone: z.string().optional().describe('Phone number for phone meetings'),
});
export type EventLocation = z.infer<typeof EventLocationSchema>;

/**
 * Reminder configuration for a calendar event.
 */
export const EventReminderSchema = z.object({
  method: z.string().describe("Reminder method (e.g., 'email', 'notification', 'sms')"),
  minutes_before: z.number().int().min(0).describe('Minutes before event to send reminder'),
});
export type EventReminder = z.infer<typeof EventReminderSchema>;

/**
 * Calendar event attendee.
 */
export const AttendeeSchema = z.object({
  email: z.string().email().describe('Attendee email address'),
  name: z.string().optional().describe('Attendee name'),
  required: z.boolean().default(true).describe('Whether attendance is required'),
  response_status: z.string().optional().describe("Response status (e.g., 'accepted', 'declined', 'tentative', 'needsAction')"),
  is_organizer: z.boolean().default(false).describe('Whether this attendee is the event organizer'),
  comment: z.string().optional().describe("Attendee's comment/note"),
});
export type Attendee = z.infer<typeof AttendeeSchema>;

/**
 * Calendar event model.
 */
export const CalendarEventSchema = z.object({
  id: z.string().describe('Unique event identifier'),
  calendar_id: z.string().optional().describe('Calendar identifier where event is stored'),
  title: z.string().describe('Event title/summary'),
  description: z.string().optional().describe('Event description'),
  start_time: z.string().datetime().or(z.date()).describe('Event start time'),
  end_time: z.string().datetime().or(z.date()).describe('Event end time'),
  timezone: z.string().default('UTC').describe("Timezone for the event (e.g., 'America/New_York')"),
  all_day: z.boolean().default(false).describe('Whether this is an all-day event'),
  attendees: z.array(AttendeeSchema).optional().describe('Event attendees'),
  location: EventLocationSchema.optional().describe('Event location'),
  reminders: z.array(EventReminderSchema).optional().describe('Event reminders'),
  status: z.string().optional().describe("Event status (e.g., 'confirmed', 'tentative', 'cancelled')"),
  visibility: z.string().default('default').describe("Event visibility (e.g., 'default', 'public', 'private')"),
  recurrence: z.array(z.string()).optional().describe('Recurrence rules (RRULE format)'),
  url: z.string().url().optional().describe('URL to view event in provider system'),
  meeting_url: z.string().url().optional().describe('URL to join online meeting'),
  created_at: z.string().datetime().or(z.date()).optional().describe('Event creation timestamp'),
  updated_at: z.string().datetime().or(z.date()).optional().describe('Last update timestamp'),
  organizer_email: z.string().email().optional().describe('Event organizer email'),
  organizer_name: z.string().optional().describe('Event organizer name'),
});
export type CalendarEvent = z.infer<typeof CalendarEventSchema>;

/**
 * Event data for creation.
 */
export const EventDataSchema = z.object({
  title: z.string().describe('Event title'),
  description: z.string().optional().describe('Event description'),
  start_time: z.string().datetime().or(z.date()).describe('Start time'),
  end_time: z.string().datetime().or(z.date()).describe('End time'),
  timezone: z.string().default('UTC').describe('Event timezone'),
  all_day: z.boolean().default(false).describe('All-day event flag'),
  attendees: z.array(AttendeeSchema).optional().describe('Event attendees'),
  location: EventLocationSchema.optional().describe('Event location'),
  reminders: z.array(EventReminderSchema).optional().describe('Event reminders'),
  visibility: z.string().default('default').describe('Event visibility'),
  recurrence: z.array(z.string()).optional().describe('Recurrence rules'),
  calendar_id: z.string().optional().describe('Target calendar ID'),
});
export type EventData = z.infer<typeof EventDataSchema>;

/**
 * Options for event creation.
 */
export const EventOptionsSchema = z.object({
  send_notifications: z.boolean().default(true).describe('Send invitations to attendees'),
  check_availability: z.boolean().default(false).describe('Check attendee availability before creating'),
});
export type EventOptions = z.infer<typeof EventOptionsSchema>;

/**
 * Request to create a new calendar event.
 */
export const CreateEventRequestSchema = ToolInputSchema.extend({
  event: EventDataSchema.describe('Event data to create'),
  options: EventOptionsSchema.optional().describe('Creation options'),
});
export type CreateEventRequest = z.infer<typeof CreateEventRequestSchema>;

/**
 * Request to update an existing calendar event.
 */
export const UpdateEventRequestSchema = ToolInputSchema.extend({
  updates: z.record(z.any()).describe('Fields to update (partial update)'),
  send_notifications: z.boolean().default(true).describe('Notify attendees of changes'),
});
export type UpdateEventRequest = z.infer<typeof UpdateEventRequestSchema>;

/**
 * Working hours configuration for availability checking.
 */
export const WorkingHoursSchema = z.object({
  start: z.string().regex(/^\d{2}:\d{2}$/).describe('Start time (HH:MM format)'),
  end: z.string().regex(/^\d{2}:\d{2}$/).describe('End time (HH:MM format)'),
  timezone: z.string().describe('Timezone for working hours'),
  exclude_weekends: z.boolean().default(true).describe('Exclude weekends from available times'),
});
export type WorkingHours = z.infer<typeof WorkingHoursSchema>;

/**
 * Date range for availability search.
 */
export const DateRangeSchema = z.object({
  start: z.string().describe('Start date (YYYY-MM-DD)'),
  end: z.string().describe('End date (YYYY-MM-DD)'),
});
export type DateRange = z.infer<typeof DateRangeSchema>;

/**
 * Availability query parameters.
 */
export const AvailabilityQuerySchema = z.object({
  attendees: z.array(z.string().email()).describe('Email addresses to check availability for'),
  duration_minutes: z.number().int().min(1).describe('Required meeting duration in minutes'),
  date_range: DateRangeSchema.describe('Date range to search'),
  working_hours: WorkingHoursSchema.optional().describe('Working hours constraints'),
  buffer_minutes: z.number().int().min(0).default(0).describe('Buffer time before/after existing events'),
});
export type AvailabilityQuery = z.infer<typeof AvailabilityQuerySchema>;

/**
 * Request to check calendar availability.
 */
export const CheckAvailabilityRequestSchema = z.object({
  correlation_id: z.string().optional().describe('Correlation ID for request tracing'),
  query: AvailabilityQuerySchema.describe('Availability query'),
});
export type CheckAvailabilityRequest = z.infer<typeof CheckAvailabilityRequestSchema>;

/**
 * An available time slot.
 */
export const AvailableSlotSchema = z.object({
  start: z.string().datetime().or(z.date()).describe('Slot start time'),
  end: z.string().datetime().or(z.date()).describe('Slot end time'),
  all_available: z.boolean().describe('Whether all attendees are available'),
  available_attendees: z.array(z.string().email()).optional().describe('List of available attendees'),
  unavailable_attendees: z.array(z.string().email()).optional().describe('List of unavailable attendees'),
});
export type AvailableSlot = z.infer<typeof AvailableSlotSchema>;

/**
 * Response from availability check.
 */
export const CheckAvailabilityResponseSchema = z.object({
  available_slots: z.array(AvailableSlotSchema).describe('List of available time slots'),
  checked_calendars: z.number().int().describe('Number of calendars checked'),
  timezone: z.string().describe('Timezone for results'),
});
export type CheckAvailabilityResponse = z.infer<typeof CheckAvailabilityResponseSchema>;

/**
 * Request to list calendar events.
 */
export const ListEventsRequestSchema = z.object({
  calendar_id: z.string().optional().describe('Calendar ID to list events from'),
  start_date: z.string().optional().describe('Start date filter (YYYY-MM-DD)'),
  end_date: z.string().optional().describe('End date filter (YYYY-MM-DD)'),
  pagination: PaginationParamsSchema.optional().describe('Pagination parameters'),
});
export type ListEventsRequest = z.infer<typeof ListEventsRequestSchema>;

/**
 * Response from list events operation.
 */
export const ListEventsResponseSchema = z.object({
  events: z.array(CalendarEventSchema).describe('List of events'),
  pagination: PaginationResponseSchema.optional().describe('Pagination metadata'),
});
export type ListEventsResponse = z.infer<typeof ListEventsResponseSchema>;