/**
 * Knowledge schema definitions for Transform Army AI Adapter Service.
 * 
 * This module defines Zod schemas for knowledge base operations including
 * document indexing, searching, and retrieval.
 */

import { z } from 'zod';
import { ToolInputSchema, PaginationParamsSchema, PaginationResponseSchema } from './base';

/**
 * Metadata for a knowledge base document.
 */
export const DocumentMetadataSchema = z.object({
  author: z.string().optional().describe('Document author'),
  version: z.string().optional().describe('Document version'),
  language: z.string().default('en').describe('Document language code (ISO 639-1)'),
  category: z.string().optional().describe('Document category'),
  tags: z.array(z.string()).optional().describe('Document tags'),
  helpful_votes: z.number().int().min(0).optional().describe('Number of helpful votes'),
  unhelpful_votes: z.number().int().min(0).optional().describe('Number of unhelpful votes'),
  view_count: z.number().int().min(0).optional().describe('Number of views'),
  last_reviewed: z.string().datetime().or(z.date()).optional().describe('Last review date'),
}).passthrough();
export type DocumentMetadata = z.infer<typeof DocumentMetadataSchema>;

/**
 * Knowledge base document model.
 */
export const DocumentSchema = z.object({
  id: z.string().describe('Unique document identifier'),
  title: z.string().describe('Document title'),
  content: z.string().describe('Document content (supports markdown)'),
  url: z.string().url().optional().describe('URL to view document'),
  category: z.string().optional().describe('Document category'),
  tags: z.array(z.string()).optional().describe('Document tags'),
  published: z.boolean().default(false).describe('Whether document is published'),
  created_at: z.string().datetime().or(z.date()).describe('Document creation timestamp'),
  updated_at: z.string().datetime().or(z.date()).optional().describe('Last update timestamp'),
  published_at: z.string().datetime().or(z.date()).optional().describe('Publication timestamp'),
  metadata: DocumentMetadataSchema.optional().describe('Additional document metadata'),
  parent_id: z.string().optional().describe('Parent document ID (for hierarchical documents)'),
  related_ids: z.array(z.string()).optional().describe('Related document IDs'),
});
export type Document = z.infer<typeof DocumentSchema>;

/**
 * Knowledge base search result with relevance score.
 */
export const SearchResultSchema = z.object({
  id: z.string().describe('Document ID'),
  title: z.string().describe('Document title'),
  url: z.string().url().optional().describe('URL to view document'),
  score: z.number().min(0).max(1).describe('Relevance score (0-1)'),
  snippet: z.string().optional().describe('Relevant excerpt from document'),
  category: z.string().optional().describe('Document category'),
  tags: z.array(z.string()).optional().describe('Document tags'),
  metadata: z.record(z.any()).optional().describe('Additional metadata'),
  highlights: z.array(z.string()).optional().describe('Highlighted matching text segments'),
});
export type SearchResult = z.infer<typeof SearchResultSchema>;

/**
 * Article data for indexing.
 */
export const ArticleDataSchema = z.object({
  title: z.string().describe('Article title'),
  content: z.string().describe('Article content (markdown supported)'),
  category: z.string().optional().describe('Article category'),
  tags: z.array(z.string()).optional().describe('Article tags'),
  metadata: DocumentMetadataSchema.optional().describe('Additional metadata'),
  parent_id: z.string().optional().describe('Parent document ID'),
  related_ids: z.array(z.string()).optional().describe('Related document IDs'),
});
export type ArticleData = z.infer<typeof ArticleDataSchema>;

/**
 * Options for document indexing.
 */
export const IndexOptionsSchema = z.object({
  auto_vectorize: z.boolean().default(true).describe('Automatically create vector embeddings'),
  publish: z.boolean().default(false).describe('Publish document immediately'),
  update_if_exists: z.boolean().default(true).describe('Update document if it already exists'),
});
export type IndexOptions = z.infer<typeof IndexOptionsSchema>;

/**
 * Request to index or update a document in the knowledge base.
 */
export const IndexDocumentRequestSchema = ToolInputSchema.extend({
  article: ArticleDataSchema.describe('Article data to index'),
  options: IndexOptionsSchema.optional().describe('Indexing options'),
});
export type IndexDocumentRequest = z.infer<typeof IndexDocumentRequestSchema>;

/**
 * Filters for knowledge base search.
 */
export const SearchFiltersSchema = z.object({
  categories: z.array(z.string()).optional().describe('Filter by categories'),
  tags: z.array(z.string()).optional().describe('Filter by tags (any match)'),
  languages: z.array(z.string()).optional().describe('Filter by language codes'),
  published_only: z.boolean().default(true).describe('Only return published documents'),
  created_after: z.string().datetime().or(z.date()).optional().describe('Filter documents created after date'),
  updated_after: z.string().datetime().or(z.date()).optional().describe('Filter documents updated after date'),
});
export type SearchFilters = z.infer<typeof SearchFiltersSchema>;

/**
 * Options for knowledge base search.
 */
export const SearchOptionsSchema = z.object({
  max_results: z.number().int().min(1).max(100).default(10).describe('Maximum number of results to return'),
  min_score: z.number().min(0).max(1).default(0).describe('Minimum relevance score threshold'),
  include_snippets: z.boolean().default(true).describe('Include text snippets in results'),
  highlight_matches: z.boolean().default(false).describe('Highlight matching text in results'),
});
export type SearchOptions = z.infer<typeof SearchOptionsSchema>;

/**
 * Search query parameters.
 */
export const SearchQuerySchema = z.object({
  text: z.string().describe('Search query text'),
  filters: SearchFiltersSchema.optional().describe('Search filters'),
  options: SearchOptionsSchema.optional().describe('Search options'),
});
export type SearchQuery = z.infer<typeof SearchQuerySchema>;

/**
 * Request to search the knowledge base.
 */
export const SearchRequestSchema = z.object({
  correlation_id: z.string().optional().describe('Correlation ID for request tracing'),
  query: SearchQuerySchema.describe('Search query'),
});
export type SearchRequest = z.infer<typeof SearchRequestSchema>;

/**
 * Response from knowledge base search operation.
 */
export const SearchResponseSchema = z.object({
  results: z.array(SearchResultSchema).describe('Search results'),
  total_results: z.number().int().min(0).describe('Total number of matching documents'),
  query_duration_ms: z.number().int().min(0).optional().describe('Query execution time in milliseconds'),
  facets: z.record(z.any()).optional().describe('Faceted search results (categories, tags, etc.)'),
});
export type SearchResponse = z.infer<typeof SearchResponseSchema>;

/**
 * Request to list documents in the knowledge base.
 */
export const ListDocumentsRequestSchema = z.object({
  category: z.string().optional().describe('Filter by category'),
  tags: z.array(z.string()).optional().describe('Filter by tags (all must match)'),
  published_only: z.boolean().default(true).describe('Only return published documents'),
  language: z.string().optional().describe('Filter by language code'),
  parent_id: z.string().optional().describe('Filter by parent document ID'),
  sort_by: z.string().default('updated_at').describe("Field to sort by (e.g., 'title', 'created_at', 'updated_at')"),
  sort_order: z.enum(['asc', 'desc']).default('desc').describe("Sort order ('asc' or 'desc')"),
  pagination: PaginationParamsSchema.optional().describe('Pagination parameters'),
});
export type ListDocumentsRequest = z.infer<typeof ListDocumentsRequestSchema>;

/**
 * Response from list documents operation.
 */
export const ListDocumentsResponseSchema = z.object({
  documents: z.array(DocumentSchema).describe('List of documents'),
  pagination: PaginationResponseSchema.optional().describe('Pagination metadata'),
});
export type ListDocumentsResponse = z.infer<typeof ListDocumentsResponseSchema>;

/**
 * Analytics and statistics for a knowledge base document.
 */
export const DocumentAnalyticsSchema = z.object({
  document_id: z.string().describe('Document ID'),
  view_count: z.number().int().min(0).describe('Total views'),
  helpful_votes: z.number().int().min(0).describe('Helpful votes'),
  unhelpful_votes: z.number().int().min(0).describe('Unhelpful votes'),
  helpfulness_ratio: z.number().min(0).max(1).optional().describe('Ratio of helpful to total votes'),
  average_time_on_page_seconds: z.number().min(0).optional().describe('Average time spent on document'),
  search_appearances: z.number().int().min(0).optional().describe('Times document appeared in search results'),
  click_through_rate: z.number().min(0).max(1).optional().describe('Click-through rate from search'),
  last_viewed: z.string().datetime().or(z.date()).optional().describe('Last view timestamp'),
});
export type DocumentAnalytics = z.infer<typeof DocumentAnalyticsSchema>;