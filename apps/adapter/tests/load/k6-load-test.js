/**
 * K6 Load Testing Script for Transform Army AI Adapter Service
 * 
 * This script provides comprehensive load testing scenarios using k6.
 * 
 * Test Scenarios:
 * - smoke: Minimal load test (1 VU, 30s) - Sanity check
 * - load: Average load test (100 VUs, 10m) - Normal conditions
 * - stress: Stress test (0→500 VUs, 20m) - Find breaking point
 * - spike: Spike test (0→200 VUs instantly, 5m) - Traffic spike handling
 * - soak: Soak test (50 VUs, 2h) - Memory leak detection
 * 
 * Usage:
 *   # Run specific scenario
 *   k6 run --env SCENARIO=smoke k6-load-test.js
 *   
 *   # Run with custom host
 *   k6 run --env HOST=https://api.example.com --env SCENARIO=load k6-load-test.js
 *   
 *   # Generate HTML report
 *   k6 run --out json=results.json k6-load-test.js
 *   k6 report results.json --output report.html
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';
import { randomString, randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

// ============================================================================
// Configuration
// ============================================================================

const BASE_URL = __ENV.HOST || 'http://localhost:8000';
const SCENARIO = __ENV.SCENARIO || 'smoke';
const TENANT_ID = __ENV.TENANT_ID || 'tenant_001';

// ============================================================================
// Custom Metrics
// ============================================================================

const apiErrorRate = new Rate('api_errors');
const providerCallDuration = new Trend('provider_call_duration');
const workflowExecutionDuration = new Trend('workflow_execution_duration');
const authenticationRate = new Rate('authentication_success');
const idempotencyHitRate = new Rate('idempotency_cache_hit');
const rateLimitHits = new Counter('rate_limit_hits');
const multiTenantIsolation = new Rate('tenant_isolation_success');

// ============================================================================
// Test Scenarios Configuration
// ============================================================================

export const options = {
  scenarios: {
    // Smoke test - Minimal load for sanity check
    smoke: {
      executor: 'constant-vus',
      vus: 1,
      duration: '30s',
      gracefulStop: '5s',
      exec: 'smokeTest',
      startTime: '0s',
      tags: { test_type: 'smoke' },
    },
    
    // Load test - Average production load
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // Ramp up to 50 users
        { duration: '5m', target: 100 },  // Ramp up to 100 users
        { duration: '2m', target: 100 },  // Stay at 100 for 2 minutes
        { duration: '1m', target: 0 },    // Ramp down
      ],
      gracefulRampDown: '30s',
      exec: 'loadTest',
      tags: { test_type: 'load' },
    },
    
    // Stress test - Push to breaking point
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },   // Ramp up to 100
        { duration: '5m', target: 200 },   // Ramp up to 200
        { duration: '5m', target: 300 },   // Ramp up to 300
        { duration: '5m', target: 400 },   // Ramp up to 400
        { duration: '2m', target: 500 },   // Push to 500
        { duration: '1m', target: 0 },     // Ramp down
      ],
      gracefulRampDown: '1m',
      exec: 'stressTest',
      tags: { test_type: 'stress' },
    },
    
    // Spike test - Sudden traffic spike
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 200 },  // Spike to 200 users instantly
        { duration: '3m', target: 200 },   // Stay at spike level
        { duration: '10s', target: 0 },    // Drop back down
        { duration: '1m', target: 0 },     // Recovery period
      ],
      gracefulRampDown: '30s',
      exec: 'spikeTest',
      tags: { test_type: 'spike' },
    },
    
    // Soak test - Long duration for memory leaks
    soak: {
      executor: 'constant-vus',
      vus: 50,
      duration: '2h',
      gracefulStop: '1m',
      exec: 'soakTest',
      tags: { test_type: 'soak' },
    },
  },
  
  // Performance thresholds
  thresholds: {
    // Overall HTTP metrics
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],  // 95% < 500ms, 99% < 1s
    'http_req_failed': ['rate<0.05'],                   // Error rate < 5%
    'http_req_duration{endpoint:health}': ['p(95)<100'], // Health checks fast
    
    // API-specific metrics
    'api_errors': ['rate<0.05'],                        // API error rate < 5%
    'provider_call_duration': ['p(95)<2000'],           // Provider calls < 2s
    'workflow_execution_duration': ['p(95)<5000'],      // Workflows < 5s
    'authentication_success': ['rate>0.95'],            // Auth success > 95%
    
    // Rate limiting
    'rate_limit_hits': ['count<100'],                   // Minimal rate limit hits
    
    // Multi-tenancy
    'tenant_isolation_success': ['rate>0.99'],          // Tenant isolation > 99%
    
    // Idempotency
    'idempotency_cache_hit': ['rate>0'],                // Some cache hits expected
  },
  
  // Test execution settings (only used if no scenario matches)
  vus: 10,
  duration: '1m',
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Generate standardized headers for API requests
 */
function getHeaders(includeIdempotency = false) {
  const correlationId = `cor_k6_${Date.now()}_${randomString(8)}`;
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ta_test_${TENANT_ID}`,
    'X-Correlation-ID': correlationId,
    'X-Tenant-ID': TENANT_ID,
  };
  
  if (includeIdempotency) {
    headers['X-Idempotency-Key'] = `idm_k6_${randomString(32)}`;
  }
  
  return headers;
}

/**
 * Check response for common issues
 */
function checkResponse(response, name) {
  const success = check(response, {
    [`${name}: status is 2xx`]: (r) => r.status >= 200 && r.status < 300,
    [`${name}: has correlation_id`]: (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.correlation_id !== undefined || body.error?.correlation_id !== undefined;
      } catch {
        return false;
      }
    },
    [`${name}: response time OK`]: (r) => r.timings.duration < 1000,
  });
  
  apiErrorRate.add(!success);
  
  // Track rate limiting
  if (response.status === 429) {
    rateLimitHits.add(1);
  }
  
  // Track authentication
  if (response.status === 401 || response.status === 403) {
    authenticationRate.add(0);
  } else if (response.status < 300) {
    authenticationRate.add(1);
  }
  
  return success;
}

/**
 * Generate random contact data
 */
function generateContactData() {
  return {
    idempotency_key: `idm_contact_${randomString(32)}`,
    correlation_id: `cor_k6_${Date.now()}`,
    contact: {
      email: `k6test.${randomString(8)}@example.com`,
      first_name: `K6Test${randomIntBetween(1, 1000)}`,
      last_name: `User${randomIntBetween(1, 1000)}`,
      company: randomItem(['Acme Corp', 'Tech Innovations', 'Global Solutions', 'Digital Dynamics']),
      phone: `+1-555-${randomIntBetween(1000, 9999)}`,
      title: randomItem(['VP Sales', 'Director', 'Manager', 'Engineer', 'Analyst']),
      custom_fields: {
        lead_source: randomItem(['website', 'referral', 'campaign', 'partner']),
        lead_score: randomIntBetween(50, 100),
      },
    },
    options: {
      dedupe_by: ['email'],
      update_if_exists: false,
    },
  };
}

/**
 * Generate random ticket data
 */
function generateTicketData() {
  const subjects = [
    'Login issue', 'Performance problem', 'Feature request',
    'Bug report', 'Integration question', 'Data sync error'
  ];
  const priorities = ['low', 'normal', 'high', 'urgent'];
  
  return {
    idempotency_key: `idm_ticket_${randomString(32)}`,
    correlation_id: `cor_k6_${Date.now()}`,
    ticket: {
      subject: `${randomItem(subjects)} - K6 Load Test`,
      description: `K6 load test ticket created at ${new Date().toISOString()}`,
      requester: {
        email: `k6test.${randomString(8)}@example.com`,
        name: `K6User${randomIntBetween(1, 1000)}`,
      },
      priority: randomItem(priorities),
      tags: ['k6-test', randomItem(['api', 'ui', 'performance', 'integration'])],
      custom_fields: {
        environment: randomItem(['production', 'staging', 'development']),
        browser: randomItem(['Chrome', 'Firefox', 'Safari', 'Edge']),
      },
    },
    options: {
      send_notification: false,
      auto_assign: true,
    },
  };
}

// ============================================================================
// Test Groups
// ============================================================================

/**
 * Health check operations
 */
function healthChecks() {
  group('Health Checks', () => {
    const healthResponse = http.get(`${BASE_URL}/health`, {
      tags: { endpoint: 'health' },
    });
    checkResponse(healthResponse, 'Health Check');
    
    const rootResponse = http.get(`${BASE_URL}/`, {
      tags: { endpoint: 'root' },
    });
    checkResponse(rootResponse, 'Root Endpoint');
  });
}

/**
 * CRM operations
 */
function crmOperations() {
  group('CRM Operations', () => {
    // Create contact
    const createStart = Date.now();
    const createResponse = http.post(
      `${BASE_URL}/api/v1/crm/contacts`,
      JSON.stringify(generateContactData()),
      {
        headers: getHeaders(true),
        tags: { endpoint: 'crm_create_contact', type: 'write' },
      }
    );
    providerCallDuration.add(Date.now() - createStart);
    const createSuccess = checkResponse(createResponse, 'CRM Create Contact');
    
    // Search contacts
    const searchResponse = http.get(
      `${BASE_URL}/api/v1/crm/contacts/search?query=k6test&limit=10`,
      {
        headers: getHeaders(),
        tags: { endpoint: 'crm_search_contacts', type: 'read' },
      }
    );
    checkResponse(searchResponse, 'CRM Search Contacts');
    
    // Create deal (less frequently)
    if (randomIntBetween(1, 100) <= 30) {  // 30% of the time
      const dealData = {
        idempotency_key: `idm_deal_${randomString(32)}`,
        correlation_id: `cor_k6_${Date.now()}`,
        deal: {
          name: `K6 Test Deal - ${randomItem(['Enterprise', 'Standard', 'Premium'])}`,
          amount: randomItem([10000, 25000, 50000, 100000]),
          currency: 'USD',
          stage: randomItem(['qualification', 'proposal', 'negotiation']),
          close_date: new Date(Date.now() + randomIntBetween(30, 90) * 86400000).toISOString().split('T')[0],
          custom_fields: {
            deal_source: 'k6_load_test',
            product_interest: randomItem(['enterprise', 'standard']),
          },
        },
      };
      
      const dealResponse = http.post(
        `${BASE_URL}/api/v1/crm/deals`,
        JSON.stringify(dealData),
        {
          headers: getHeaders(true),
          tags: { endpoint: 'crm_create_deal', type: 'write' },
        }
      );
      checkResponse(dealResponse, 'CRM Create Deal');
    }
  });
}

/**
 * Helpdesk operations
 */
function helpdeskOperations() {
  group('Helpdesk Operations', () => {
    // Create ticket
    const createStart = Date.now();
    const createResponse = http.post(
      `${BASE_URL}/api/v1/helpdesk/tickets`,
      JSON.stringify(generateTicketData()),
      {
        headers: getHeaders(true),
        tags: { endpoint: 'helpdesk_create_ticket', type: 'write' },
      }
    );
    providerCallDuration.add(Date.now() - createStart);
    checkResponse(createResponse, 'Helpdesk Create Ticket');
    
    // Search tickets
    const statuses = randomItem(['open', 'pending', 'solved']);
    const priorities = randomItem(['high', 'urgent', 'normal']);
    const searchResponse = http.get(
      `${BASE_URL}/api/v1/helpdesk/tickets/search?status=${statuses}&priority=${priorities}&limit=20`,
      {
        headers: getHeaders(),
        tags: { endpoint: 'helpdesk_search_tickets', type: 'read' },
      }
    );
    checkResponse(searchResponse, 'Helpdesk Search Tickets');
  });
}

/**
 * Workflow operations
 */
function workflowOperations() {
  group('Workflow Operations', () => {
    // Execute workflow
    const workflowStart = Date.now();
    const workflowData = {
      idempotency_key: `idm_workflow_${randomString(32)}`,
      correlation_id: `cor_k6_${Date.now()}`,
      workflow_id: randomItem(['lead_qualification', 'support_triage', 'ops_monitoring']),
      input: {
        email: `k6test.${randomString(8)}@example.com`,
        company: `K6TestCompany${randomIntBetween(1, 100)}`,
        priority: randomItem(['normal', 'high']),
      },
      options: {
        timeout: 30,
        retry_on_failure: true,
      },
    };
    
    const executeResponse = http.post(
      `${BASE_URL}/api/v1/workflows/execute`,
      JSON.stringify(workflowData),
      {
        headers: getHeaders(true),
        tags: { endpoint: 'workflow_execute', type: 'write' },
      }
    );
    workflowExecutionDuration.add(Date.now() - workflowStart);
    checkResponse(executeResponse, 'Workflow Execute');
    
    // List workflows
    const listResponse = http.get(
      `${BASE_URL}/api/v1/workflows`,
      {
        headers: getHeaders(),
        tags: { endpoint: 'workflow_list', type: 'read' },
      }
    );
    checkResponse(listResponse, 'Workflow List');
  });
}

/**
 * Knowledge base operations
 */
function knowledgeOperations() {
  group('Knowledge Operations', () => {
    const queries = [
      'How do I reset my password?',
      'API authentication guide',
      'Rate limiting documentation',
      'Integration examples',
      'Troubleshooting common errors',
    ];
    
    const searchData = {
      correlation_id: `cor_k6_${Date.now()}`,
      query: {
        text: randomItem(queries),
        filters: {
          published_only: true,
        },
        options: {
          max_results: 5,
          min_score: 0.7,
          include_snippets: true,
        },
      },
    };
    
    const searchResponse = http.post(
      `${BASE_URL}/api/v1/knowledge/search`,
      JSON.stringify(searchData),
      {
        headers: getHeaders(),
        tags: { endpoint: 'knowledge_search', type: 'read' },
      }
    );
    checkResponse(searchResponse, 'Knowledge Search');
  });
}

/**
 * Test multi-tenant isolation
 */
function multiTenantTest() {
  const tenantIds = ['tenant_001', 'tenant_002', 'tenant_003'];
  
  group('Multi-Tenant Isolation', () => {
    const testTenant = randomItem(tenantIds);
    const headers = getHeaders(true);
    headers['X-Tenant-ID'] = testTenant;
    
    // Create resource with specific tenant
    const createResponse = http.post(
      `${BASE_URL}/api/v1/crm/contacts`,
      JSON.stringify(generateContactData()),
      { headers, tags: { endpoint: 'tenant_isolation_test' } }
    );
    
    const isolated = check(createResponse, {
      'Tenant isolation: status OK': (r) => r.status < 300,
      'Tenant isolation: correct tenant': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.tenant_id === testTenant || r.status === 401;
        } catch {
          return false;
        }
      },
    });
    
    multiTenantIsolation.add(isolated);
  });
}

// ============================================================================
// Scenario Implementations
// ============================================================================

/**
 * Smoke test - Minimal load sanity check
 */
export function smokeTest() {
  healthChecks();
  sleep(1);
  
  crmOperations();
  sleep(1);
  
  helpdeskOperations();
  sleep(1);
}

/**
 * Load test - Average production load
 */
export function loadTest() {
  // Randomize behavior to simulate real users
  const rand = randomIntBetween(1, 100);
  
  if (rand <= 10) {
    healthChecks();
  } else if (rand <= 50) {
    crmOperations();
  } else if (rand <= 80) {
    helpdeskOperations();
  } else if (rand <= 90) {
    workflowOperations();
  } else {
    knowledgeOperations();
  }
  
  // Variable think time
  sleep(randomIntBetween(1, 5));
}

/**
 * Stress test - Push system to limits
 */
export function stressTest() {
  // More aggressive testing with less think time
  const rand = randomIntBetween(1, 100);
  
  if (rand <= 40) {
    crmOperations();
  } else if (rand <= 70) {
    helpdeskOperations();
  } else if (rand <= 90) {
    workflowOperations();
  } else {
    multiTenantTest();
  }
  
  sleep(randomIntBetween(0.5, 2));
}

/**
 * Spike test - Sudden load increase
 */
export function spikeTest() {
  // Rapid-fire requests during spike
  crmOperations();
  helpdeskOperations();
  
  // Minimal sleep during spike
  sleep(0.5);
}

/**
 * Soak test - Long duration for stability
 */
export function soakTest() {
  // Steady, realistic load over long period
  loadTest();
}

// ============================================================================
// Lifecycle Hooks
// ============================================================================

export function setup() {
  console.log(`Starting k6 load test against ${BASE_URL}`);
  console.log(`Scenario: ${SCENARIO}`);
  console.log(`Tenant: ${TENANT_ID}`);
  
  // Verify service is accessible
  const healthCheck = http.get(`${BASE_URL}/health`);
  if (healthCheck.status !== 200) {
    throw new Error(`Service not available: ${healthCheck.status}`);
  }
  
  return { startTime: Date.now() };
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`\nTest completed after ${duration.toFixed(2)} seconds`);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'k6-results.json': JSON.stringify(data),
    'k6-summary.html': htmlReport(data),
  };
}

// Helper function for text summary
function textSummary(data, options) {
  const indent = options.indent || '';
  const enableColors = options.enableColors || false;
  
  let summary = `\n${indent}Test Summary\n${indent}============\n\n`;
  
  // Metrics summary
  for (const [name, metric] of Object.entries(data.metrics)) {
    if (metric.values) {
      summary += `${indent}${name}:\n`;
      for (const [key, value] of Object.entries(metric.values)) {
        summary += `${indent}  ${key}: ${value}\n`;
      }
    }
  }
  
  return summary;
}

// Helper function for HTML report
function htmlReport(data) {
  return `
<!DOCTYPE html>
<html>
<head>
  <title>K6 Load Test Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    h1 { color: #333; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #4CAF50; color: white; }
    .pass { color: green; }
    .fail { color: red; }
  </style>
</head>
<body>
  <h1>K6 Load Test Report</h1>
  <h2>Test Configuration</h2>
  <p>Scenario: ${SCENARIO}</p>
  <p>Host: ${BASE_URL}</p>
  <p>Tenant: ${TENANT_ID}</p>
  
  <h2>Metrics</h2>
  <pre>${JSON.stringify(data.metrics, null, 2)}</pre>
  
  <h2>Thresholds</h2>
  <pre>${JSON.stringify(data.root_group.checks, null, 2)}</pre>
</body>
</html>
  `;
}