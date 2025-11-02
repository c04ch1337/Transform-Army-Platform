'use client';

import { useEffect, useState } from 'react';

interface SystemMetrics {
  timestamp: string;
  system: {
    cpu_percent: number;
    memory_percent: number;
    memory_used_gb: number;
    memory_total_gb: number;
    disk_percent: number;
    disk_used_gb: number;
    disk_total_gb: number;
  };
  application: {
    version: string;
    environment: string;
    uptime_seconds: number;
  };
}

interface HealthCheck {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  response_time_ms: number;
  message?: string;
  details?: any;
}

interface SystemStatus {
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  environment: string;
  uptime_seconds: number;
  checks: {
    healthy: number;
    degraded: number;
    unhealthy: number;
  };
  dependencies: Record<string, HealthCheck>;
  metrics: {
    total_check_time_ms: number;
    average_response_time_ms: number;
    slowest_check: string;
  };
}

export default function MonitoringPage() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [health, setHealth] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchData = async () => {
    try {
      const [metricsRes, healthRes] = await Promise.all([
        fetch('http://localhost:8000/metrics/summary'),
        fetch('http://localhost:8000/health/detailed')
      ]);

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }

      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setHealth(healthData);
      }

      setError(null);
    } catch (err) {
      setError('Failed to fetch monitoring data. Ensure the adapter service is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    if (autoRefresh) {
      const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy': return 'text-green-400 border-green-500';
      case 'degraded': return 'text-yellow-400 border-yellow-500';
      case 'unhealthy': return 'text-red-400 border-red-500';
      default: return 'text-gray-400 border-gray-500';
    }
  };

  const getStatusBadge = (status: string): string => {
    switch (status) {
      case 'healthy': return 'bg-green-500/20 text-green-400 border-green-500';
      case 'degraded': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500';
      case 'unhealthy': return 'bg-red-500/20 text-red-400 border-red-500';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500';
    }
  };

  const getMetricColor = (value: number, thresholds: { warning: number; critical: number }): string => {
    if (value >= thresholds.critical) return 'text-red-400';
    if (value >= thresholds.warning) return 'text-yellow-400';
    return 'text-green-400';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400 text-lg font-mono">
          <span className="animate-pulse">⬡ LOADING TACTICAL DISPLAY...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-mono">
      {/* Header */}
      <div className="mb-8 border-b-2 border-slate-800 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-100 mb-2">
              ⬡ OPERATIONAL MONITORING STATION
            </h1>
            <p className="text-slate-400">
              Transform Army AI - Real-time System Status
            </p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 border ${
                autoRefresh 
                  ? 'border-green-500 bg-green-500/10 text-green-400' 
                  : 'border-slate-600 bg-slate-800 text-slate-400'
              } hover:bg-opacity-20 transition-colors`}
            >
              {autoRefresh ? '● AUTO-REFRESH: ON' : '○ AUTO-REFRESH: OFF'}
            </button>
            <button
              onClick={fetchData}
              className="px-4 py-2 border border-slate-600 bg-slate-800 text-slate-400 hover:bg-slate-700 transition-colors"
            >
              ⟳ REFRESH NOW
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 border border-red-500 bg-red-500/10 text-red-400">
          <strong>⚠ CONNECTION ERROR:</strong> {error}
        </div>
      )}

      {/* Overall Status */}
      {health && (
        <div className={`mb-6 p-6 border-2 ${getStatusColor(health.overall_status)}`}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold mb-1">
                SYSTEM STATUS: <span className="uppercase">{health.overall_status}</span>
              </h2>
              <p className="text-sm text-slate-400">
                Environment: {health.environment.toUpperCase()} | Version: {health.version} | Uptime: {formatUptime(health.uptime_seconds)}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-400 mb-1">CHECKS</div>
              <div className="flex gap-4 text-lg">
                <span className="text-green-400">✓ {health.checks.healthy}</span>
                <span className="text-yellow-400">⚠ {health.checks.degraded}</span>
                <span className="text-red-400">✗ {health.checks.unhealthy}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* System Resources */}
        {metrics && (
          <div className="border border-slate-700 bg-slate-900 p-6">
            <h3 className="text-xl font-bold mb-4 text-slate-100">⬢ SYSTEM RESOURCES</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1 text-sm">
                  <span className="text-slate-400">CPU UTILIZATION</span>
                  <span className={getMetricColor(metrics.system.cpu_percent, { warning: 70, critical: 85 })}>
                    {metrics.system.cpu_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2">
                  <div 
                    className={`h-2 transition-all ${
                      metrics.system.cpu_percent >= 85 ? 'bg-red-500' :
                      metrics.system.cpu_percent >= 70 ? 'bg-yellow-500' :
                      'bg-green-500'
                    }`}
                    style={{ width: `${metrics.system.cpu_percent}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1 text-sm">
                  <span className="text-slate-400">MEMORY USAGE</span>
                  <span className={getMetricColor(metrics.system.memory_percent, { warning: 75, critical: 90 })}>
                    {metrics.system.memory_used_gb.toFixed(1)} / {metrics.system.memory_total_gb.toFixed(1)} GB ({metrics.system.memory_percent.toFixed(1)}%)
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2">
                  <div 
                    className={`h-2 transition-all ${
                      metrics.system.memory_percent >= 90 ? 'bg-red-500' :
                      metrics.system.memory_percent >= 75 ? 'bg-yellow-500' :
                      'bg-green-500'
                    }`}
                    style={{ width: `${metrics.system.memory_percent}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1 text-sm">
                  <span className="text-slate-400">DISK SPACE</span>
                  <span className={getMetricColor(metrics.system.disk_percent, { warning: 80, critical: 90 })}>
                    {metrics.system.disk_used_gb.toFixed(1)} / {metrics.system.disk_total_gb.toFixed(1)} GB ({metrics.system.disk_percent.toFixed(1)}%)
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2">
                  <div 
                    className={`h-2 transition-all ${
                      metrics.system.disk_percent >= 90 ? 'bg-red-500' :
                      metrics.system.disk_percent >= 80 ? 'bg-yellow-500' :
                      'bg-green-500'
                    }`}
                    style={{ width: `${metrics.system.disk_percent}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Performance Metrics */}
        {health && (
          <div className="border border-slate-700 bg-slate-900 p-6">
            <h3 className="text-xl font-bold mb-4 text-slate-100">⬢ PERFORMANCE METRICS</h3>
            <div className="space-y-4">
              <div className="flex justify-between p-3 bg-slate-800 border border-slate-700">
                <span className="text-slate-400">AVG RESPONSE TIME</span>
                <span className="text-green-400 font-bold">
                  {health.metrics.average_response_time_ms.toFixed(2)} ms
                </span>
              </div>
              <div className="flex justify-between p-3 bg-slate-800 border border-slate-700">
                <span className="text-slate-400">TOTAL CHECK TIME</span>
                <span className="text-slate-300 font-bold">
                  {health.metrics.total_check_time_ms.toFixed(2)} ms
                </span>
              </div>
              <div className="flex justify-between p-3 bg-slate-800 border border-slate-700">
                <span className="text-slate-400">SLOWEST COMPONENT</span>
                <span className="text-yellow-400 font-bold uppercase">
                  {health.metrics.slowest_check}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Dependency Status */}
      {health && (
        <div className="border border-slate-700 bg-slate-900 p-6">
          <h3 className="text-xl font-bold mb-4 text-slate-100">⬢ DEPENDENCY STATUS</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(health.dependencies).map(([name, check]) => (
              <div 
                key={name}
                className={`p-4 border ${getStatusBadge(check.status)}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold uppercase">{name}</span>
                  <span className={`text-xs px-2 py-1 border ${getStatusBadge(check.status)}`}>
                    {check.status.toUpperCase()}
                  </span>
                </div>
                <div className="text-sm text-slate-400 mb-1">
                  Response: {check.response_time_ms.toFixed(2)}ms
                </div>
                {check.message && (
                  <div className="text-xs text-slate-500 mt-2">
                    {check.message}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-8 text-center text-slate-500 text-sm border-t border-slate-800 pt-4">
        <p>Last Updated: {health?.timestamp || metrics?.timestamp || 'N/A'}</p>
        <p className="mt-1">Transform Army AI - Mission Control Dashboard</p>
      </div>
    </div>
  );
}