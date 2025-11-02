'use client';

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Clock, TrendingUp, TrendingDown, Activity, Database, Zap, Server, AlertTriangle } from 'lucide-react';

// Types
interface BenchmarkStat {
  min_ms: number;
  max_ms: number;
  mean_ms: number;
  median_ms: number;
  stddev_ms: number;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
}

interface BenchmarkData {
  [category: string]: {
    [benchmarkName: string]: BenchmarkStat & { target_ms: number; baseline_ms: number };
  };
}

interface BaselineData {
  version: string;
  last_updated: string;
  benchmarks: BenchmarkData;
  history: Array<{
    timestamp: string;
    total_benchmarks: number;
    regressions: number;
    improvements: number;
  }>;
}

// Military-themed colors
const COLORS = {
  primary: '#10b981', // Green
  danger: '#ef4444', // Red
  warning: '#f59e0b', // Orange
  info: '#3b82f6', // Blue
  success: '#22c55e', // Light green
  muted: '#6b7280', // Gray
};

const CATEGORY_COLORS = {
  api: '#10b981',
  workflows: '#3b82f6',
  database: '#8b5cf6',
  llm: '#f59e0b',
};

export default function PerformancePage() {
  const [baselineData, setBaselineData] = useState<BaselineData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('30d');

  useEffect(() => {
    // Fetch baseline data
    fetchBaselineData();
  }, []);

  const fetchBaselineData = async () => {
    try {
      // In production, this would fetch from an API endpoint
      // For now, we'll use mock data based on the baseline structure
      const mockData: BaselineData = {
        version: '1.0.0',
        last_updated: new Date().toISOString(),
        benchmarks: {
          api: {
            health_endpoint: {
              target_ms: 50,
              baseline_ms: 25,
              p50_ms: 20,
              p95_ms: 45,
              p99_ms: 48,
              min_ms: 15,
              max_ms: 50,
              mean_ms: 25,
              median_ms: 22,
              stddev_ms: 8,
            },
            crm_list_contacts: {
              target_ms: 200,
              baseline_ms: 120,
              p50_ms: 110,
              p95_ms: 180,
              p99_ms: 195,
              min_ms: 95,
              max_ms: 200,
              mean_ms: 120,
              median_ms: 115,
              stddev_ms: 25,
            },
          },
          workflows: {
            simple_workflow_execution: {
              target_ms: 5000,
              baseline_ms: 3200,
              p50_ms: 3000,
              p95_ms: 4500,
              p99_ms: 4900,
              min_ms: 2800,
              max_ms: 5000,
              mean_ms: 3200,
              median_ms: 3100,
              stddev_ms: 450,
            },
          },
          database: {
            select_by_id: {
              target_ms: 10,
              baseline_ms: 5,
              p50_ms: 4,
              p95_ms: 8,
              p99_ms: 9,
              min_ms: 3,
              max_ms: 10,
              mean_ms: 5,
              median_ms: 4.5,
              stddev_ms: 1.5,
            },
            indexed_query: {
              target_ms: 30,
              baseline_ms: 18,
              p50_ms: 16,
              p95_ms: 26,
              p99_ms: 29,
              min_ms: 12,
              max_ms: 30,
              mean_ms: 18,
              median_ms: 17,
              stddev_ms: 5,
            },
          },
          llm: {
            token_count_medium: {
              target_ms: 10,
              baseline_ms: 6.5,
              p50_ms: 6,
              p95_ms: 9,
              p99_ms: 9.8,
              min_ms: 5,
              max_ms: 10,
              mean_ms: 6.5,
              median_ms: 6.2,
              stddev_ms: 1.2,
            },
          },
        },
        history: [
          { timestamp: '2025-11-01T00:00:00Z', total_benchmarks: 45, regressions: 0, improvements: 5 },
          { timestamp: '2025-11-02T00:00:00Z', total_benchmarks: 45, regressions: 1, improvements: 3 },
        ],
      };
      
      setBaselineData(mockData);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching baseline data:', error);
      setLoading(false);
    }
  };

  const calculateHealthScore = () => {
    if (!baselineData) return 0;
    
    let totalBenchmarks = 0;
    let passingBenchmarks = 0;
    
    Object.values(baselineData.benchmarks).forEach((category) => {
      Object.values(category).forEach((benchmark) => {
        totalBenchmarks++;
        if (benchmark.p95_ms <= benchmark.target_ms) {
          passingBenchmarks++;
        }
      });
    });
    
    return Math.round((passingBenchmarks / totalBenchmarks) * 100);
  };

  const getPerformanceStatus = (benchmark: BenchmarkStat & { target_ms: number }) => {
    if (benchmark.p95_ms <= benchmark.target_ms * 0.8) return 'excellent';
    if (benchmark.p95_ms <= benchmark.target_ms) return 'good';
    if (benchmark.p95_ms <= benchmark.target_ms * 1.2) return 'warning';
    return 'critical';
  };

  const getCategoryStats = () => {
    if (!baselineData) return [];
    
    return Object.entries(baselineData.benchmarks).map(([category, benchmarks]) => {
      const total = Object.keys(benchmarks).length;
      const passing = Object.values(benchmarks).filter(
        (b) => b.p95_ms <= b.target_ms
      ).length;
      const avgPerformance = Object.values(benchmarks).reduce(
        (sum, b) => sum + (b.p95_ms / b.target_ms) * 100,
        0
      ) / total;
      
      return {
        category: category.toUpperCase(),
        total,
        passing,
        avgPerformance: Math.round(avgPerformance),
        color: CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS],
      };
    });
  };

  const getPercentileData = () => {
    if (!baselineData || selectedCategory === 'all') return [];
    
    const category = baselineData.benchmarks[selectedCategory];
    if (!category) return [];
    
    return Object.entries(category).map(([name, data]) => ({
      name: name.replace(/_/g, ' '),
      P50: data.p50_ms,
      P95: data.p95_ms,
      P99: data.p99_ms,
      Target: data.target_ms,
    }));
  };

  const getTrendData = () => {
    if (!baselineData) return [];
    
    return baselineData.history.map((entry) => ({
      date: new Date(entry.timestamp).toLocaleDateString(),
      regressions: entry.regressions,
      improvements: entry.improvements,
      total: entry.total_benchmarks,
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading performance data...</div>
      </div>
    );
  }

  const healthScore = calculateHealthScore();
  const categoryStats = getCategoryStats();
  const percentileData = getPercentileData();
  const trendData = getTrendData();

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Activity className="w-8 h-8 text-green-500" />
          <h1 className="text-3xl font-bold">Performance Command Center</h1>
        </div>
        <p className="text-gray-400">Real-time performance monitoring and benchmarking</p>
      </div>

      {/* Health Score Card */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-gray-800 rounded-lg p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400">System Health</span>
            <Activity className="w-5 h-5 text-green-500" />
          </div>
          <div className="text-3xl font-bold text-green-500">{healthScore}%</div>
          <p className="text-sm text-gray-400 mt-1">Benchmarks Passing</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400">API Response</span>
            <Zap className="w-5 h-5 text-blue-500" />
          </div>
          <div className="text-3xl font-bold text-blue-500">
            {baselineData?.benchmarks.api.health_endpoint.p95_ms}ms
          </div>
          <p className="text-sm text-gray-400 mt-1">P95 Latency</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400">Database</span>
            <Database className="w-5 h-5 text-purple-500" />
          </div>
          <div className="text-3xl font-bold text-purple-500">
            {baselineData?.benchmarks.database.select_by_id.p95_ms}ms
          </div>
          <p className="text-sm text-gray-400 mt-1">Query Time</p>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400">Workflows</span>
            <Server className="w-5 h-5 text-orange-500" />
          </div>
          <div className="text-3xl font-bold text-orange-500">
            {Math.round(baselineData?.benchmarks.workflows.simple_workflow_execution.p95_ms || 0)}ms
          </div>
          <p className="text-sm text-gray-400 mt-1">Execution Time</p>
        </div>
      </div>

      {/* Category Performance */}
      <div className="bg-gray-800 rounded-lg p-6 mb-8">
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-green-500" />
          Category Performance Overview
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={categoryStats}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="category" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
              labelStyle={{ color: '#fff' }}
            />
            <Legend />
            <Bar dataKey="passing" fill={COLORS.success} name="Passing" />
            <Bar dataKey="total" fill={COLORS.info} name="Total" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Category Selector and Percentile Chart */}
      <div className="bg-gray-800 rounded-lg p-6 mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Clock className="w-6 h-6 text-blue-500" />
            Percentile Distribution
          </h2>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Categories</option>
            <option value="api">API</option>
            <option value="workflows">Workflows</option>
            <option value="database">Database</option>
            <option value="llm">LLM</option>
          </select>
        </div>
        
        {selectedCategory !== 'all' && percentileData.length > 0 && (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={percentileData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" label={{ value: 'Time (ms)', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                labelStyle={{ color: '#fff' }}
              />
              <Legend />
              <Bar dataKey="P50" fill={COLORS.success} name="P50" />
              <Bar dataKey="P95" fill={COLORS.warning} name="P95" />
              <Bar dataKey="P99" fill={COLORS.danger} name="P99" />
              <Bar dataKey="Target" fill={COLORS.muted} name="Target" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Performance Trends */}
      <div className="bg-gray-800 rounded-lg p-6 mb-8">
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-green-500" />
          Performance Trends
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="date" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
              labelStyle={{ color: '#fff' }}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="improvements"
              stackId="1"
              stroke={COLORS.success}
              fill={COLORS.success}
              name="Improvements"
            />
            <Area
              type="monotone"
              dataKey="regressions"
              stackId="1"
              stroke={COLORS.danger}
              fill={COLORS.danger}
              name="Regressions"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Performance Targets */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-yellow-500" />
          Performance Targets & SLAs
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-700 p-4 rounded-lg">
            <h3 className="font-semibold mb-2 text-green-500">✓ API Endpoints</h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li>• Response Time: &lt; 200ms (P95)</li>
              <li>• Health Check: &lt; 50ms</li>
              <li>• Error Rate: &lt; 0.1%</li>
            </ul>
          </div>
          <div className="bg-gray-700 p-4 rounded-lg">
            <h3 className="font-semibold mb-2 text-blue-500">✓ Database</h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li>• Query Time: &lt; 50ms (P95)</li>
              <li>• Connection Pool: &lt; 5ms</li>
              <li>• Transaction: &lt; 100ms</li>
            </ul>
          </div>
          <div className="bg-gray-700 p-4 rounded-lg">
            <h3 className="font-semibold mb-2 text-purple-500">✓ Workflows</h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li>• Simple: &lt; 5s</li>
              <li>• Complex: &lt; 15s</li>
              <li>• State Operations: &lt; 50ms</li>
            </ul>
          </div>
          <div className="bg-gray-700 p-4 rounded-lg">
            <h3 className="font-semibold mb-2 text-orange-500">✓ LLM Operations</h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li>• Token Counting: &lt; 10ms</li>
              <li>• Prompt Building: &lt; 20ms</li>
              <li>• Schema Conversion: &lt; 50ms</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-8 text-center text-gray-500 text-sm">
        <p>Last Updated: {baselineData?.last_updated ? new Date(baselineData.last_updated).toLocaleString() : 'N/A'}</p>
        <p className="mt-1">Performance metrics are continuously monitored and updated</p>
      </div>
    </div>
  );
}