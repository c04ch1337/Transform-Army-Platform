'use client';

import { useState, useEffect } from 'react';

export default function ApiDocsPage() {
  const [apiUrl, setApiUrl] = useState('http://localhost:8000');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const env = process.env.NEXT_PUBLIC_ENV || 'development';
    const urls = {
      development: 'http://localhost:8000',
      staging: 'https://api-staging.transform-army.ai',
      production: 'https://api.transform-army.ai',
    };
    setApiUrl(urls[env as keyof typeof urls] || urls.development);
    setIsLoading(false);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <header className="bg-slate-950 border-b-2 border-amber-500 shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-16 h-16 bg-gradient-to-br from-amber-600 to-amber-800 rounded-full flex items-center justify-center border-4 border-amber-500 shadow-xl">
                  <span className="text-3xl">⚡</span>
                </div>
                <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-2 border-slate-950"></div>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-600">
                  Transform Army AI
                </h1>
                <p className="text-amber-200 font-semibold">API OPERATIONS CENTER</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 bg-slate-900 px-6 py-3 rounded-lg border border-green-500/30">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-green-400 font-mono text-sm">OPERATIONAL</span>
              <div className="h-6 w-px bg-slate-700"></div>
              <span className="text-amber-400 font-mono text-sm">v1.0.0</span>
            </div>
          </div>
          <div className="mt-6 bg-slate-900/50 border-l-4 border-amber-500 p-4 rounded-r-lg">
            <p className="text-amber-100 text-sm">
              <span className="font-bold text-amber-400">MISSION:</span> Interactive API documentation and testing interface. 
              Explore endpoints, test operations, and generate code snippets.
            </p>
          </div>
        </div>
      </header>

      <div className="bg-slate-900 border-b border-slate-700">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-xs font-mono text-slate-400">Quick Deploy:</span>
              <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-md">
                🔑 Get API Key
              </button>
              <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-semibold rounded-md">
                📘 View Guide
              </button>
            </div>
            <div className="flex items-center space-x-3">
              <span className="text-xs font-mono text-slate-400">Base URL:</span>
              <select
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                className="bg-slate-800 text-amber-400 border border-slate-600 rounded-md px-3 py-1.5 text-sm font-mono"
              >
                <option value="http://localhost:8000">🏠 Local</option>
                <option value="https://api-dev.transform-army.ai">🔧 Dev</option>
                <option value="https://api-staging.transform-army.ai">🧪 Staging</option>
                <option value="https://api.transform-army.ai">🎯 Production</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-amber-500/50 transition-colors">
            <h3 className="text-lg font-bold text-amber-400 mb-3">🔐 Authentication</h3>
            <p className="text-slate-300 text-sm mb-3">
              All endpoints require API key via <code className="text-amber-400 bg-slate-900 px-1.5 py-0.5 rounded text-xs">X-API-Key</code> header.
            </p>
            <button className="text-xs text-amber-400 hover:text-amber-300 font-semibold">Learn more →</button>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-amber-500/50 transition-colors">
            <h3 className="text-lg font-bold text-amber-400 mb-3">⚡ Rate Limits</h3>
            <p className="text-slate-300 text-sm mb-3">
              Default: <span className="text-amber-400 font-bold">60 req/min</span>. Monitor via response headers.
            </p>
            <button className="text-xs text-amber-400 hover:text-amber-300 font-semibold">View details →</button>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-amber-500/50 transition-colors">
            <h3 className="text-lg font-bold text-amber-400 mb-3">📚 Resources</h3>
            <p className="text-slate-300 text-sm mb-3">
              Comprehensive guides, SDK examples, and webhook documentation available.
            </p>
            <button className="text-xs text-amber-400 hover:text-amber-300 font-semibold">Browse docs →</button>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg border-2 border-slate-700 shadow-2xl overflow-hidden">
          <div className="bg-gradient-to-r from-slate-900 to-slate-800 border-b-2 border-amber-500 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-amber-600 rounded-lg flex items-center justify-center border-2 border-amber-500">
                  <span className="text-2xl">💻</span>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">API EXPLORER</h2>
                  <p className="text-xs text-amber-400 font-mono">Interactive Testing Interface</p>
                </div>
              </div>
              <span className="text-xs text-green-400 font-mono font-bold">● ONLINE</span>
            </div>
          </div>

          <div className="p-8 min-h-[600px]">
            {isLoading ? (
              <div className="flex items-center justify-center h-96">
                <div className="text-center">
                  <div className="w-16 h-16 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-amber-400 font-mono">Loading API specifications...</p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="bg-slate-900 border border-amber-500/30 rounded-lg p-6">
                  <h3 className="text-xl font-bold text-amber-400 mb-4">📖 Interactive Documentation</h3>
                  <p className="text-slate-300 mb-4">
                    Access full interactive API documentation with try-it-now functionality:
                  </p>
                  <div className="flex flex-col space-y-3">
                    <a
                      href={`${apiUrl}/docs`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block bg-blue-600 hover:bg-blue-700 text-white text-center px-6 py-3 rounded-md font-semibold transition-colors"
                    >
                      Open Swagger UI →
                    </a>
                    <a
                      href={`${apiUrl}/redoc`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block bg-purple-600 hover:bg-purple-700 text-white text-center px-6 py-3 rounded-md font-semibold transition-colors"
                    >
                      Open ReDoc →
                    </a>
                    <a
                      href={`${apiUrl}/openapi.json`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block bg-green-600 hover:bg-green-700 text-white text-center px-6 py-3 rounded-md font-semibold transition-colors"
                    >
                      View OpenAPI JSON →
                    </a>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                    <h4 className="text-lg font-bold text-amber-400 mb-4">🎯 Quick Links</h4>
                    <ul className="space-y-2">
                      <li><a href="/docs/API_GUIDE.md" className="text-slate-300 hover:text-amber-400 transition-colors">API Guide</a></li>
                      <li><a href="/docs/API_REFERENCE.md" className="text-slate-300 hover:text-amber-400 transition-colors">API Reference</a></li>
                      <li><a href="/docs/SDK_EXAMPLES.md" className="text-slate-300 hover:text-amber-400 transition-colors">SDK Examples</a></li>
                      <li><a href="/docs/WEBHOOKS.md" className="text-slate-300 hover:text-amber-400 transition-colors">Webhooks</a></li>
                      <li><a href="/docs/API_CHANGELOG.md" className="text-slate-300 hover:text-amber-400 transition-colors">Changelog</a></li>
                    </ul>
                  </div>

                  <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
                    <h4 className="text-lg font-bold text-amber-400 mb-4">🚀 Getting Started</h4>
                    <ol className="space-y-2 list-decimal list-inside text-slate-300">
                      <li>Get your API key from the dashboard</li>
                      <li>Test the connection at /health/</li>
                      <li>Create your first contact</li>
                      <li>Explore all endpoints</li>
                      <li>Integrate with your app</li>
                    </ol>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h3 className="text-lg font-bold text-amber-400 mb-4">💻 Code Generation</h3>
            <p className="text-slate-300 text-sm mb-4">
              Click the "Try it out" button on any endpoint to:
            </p>
            <ul className="text-slate-300 text-sm space-y-2">
              <li className="flex items-start">
                <span className="text-amber-500 mr-2">▸</span>
                <span>Generate code snippets in multiple languages</span>
              </li>
              <li className="flex items-start">
                <span className="text-amber-500 mr-2">▸</span>
                <span>Test requests with your API key</span>
              </li>
              <li className="flex items-start">
                <span className="text-amber-500 mr-2">▸</span>
                <span>View real-time response data</span>
              </li>
              <li className="flex items-start">
                <span className="text-amber-500 mr-2">▸</span>
                <span>Export as cURL, Python, JavaScript, etc.</span>
              </li>
            </ul>
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h3 className="text-lg font-bold text-amber-400 mb-4">❓ Need Help?</h3>
            <div className="space-y-3">
              <a href="/docs/API_GUIDE.md" className="block text-sm text-slate-300 hover:text-amber-400 transition-colors">
                📖 API Guide
              </a>
              <a href="/docs/API_REFERENCE.md" className="block text-sm text-slate-300 hover:text-amber-400 transition-colors">
                📚 API Reference
              </a>
              <a href="/docs/SDK_EXAMPLES.md" className="block text-sm text-slate-300 hover:text-amber-400 transition-colors">
                💻 SDK Examples
              </a>
              <a href="/docs/WEBHOOKS.md" className="block text-sm text-slate-300 hover:text-amber-400 transition-colors">
                🔔 Webhook Guide
              </a>
              <a href="mailto:support@transform-army.ai" className="block text-sm text-slate-300 hover:text-amber-400 transition-colors">
                ✉️ Contact Support
              </a>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}