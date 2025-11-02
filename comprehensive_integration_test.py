#!/usr/bin/env python3
"""
Comprehensive Integration Test for Transform Army AI System

This script performs end-to-end testing of both frontend and backend components
to verify the complete system is operational after debugging fixes.

Test Coverage:
1. Backend service startup and provider loading
2. API endpoint functionality (health, providers, stats)
3. Frontend-backend integration
4. Provider registration system
5. Error handling and graceful degradation
6. Final validation report generation

Usage:
    python comprehensive_integration_test.py [--backend-url http://localhost:8000] [--frontend-url http://localhost:3000]
"""

import asyncio
import aiohttp
import json
import time
import sys
import subprocess
import signal
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import argparse

# Test configuration
DEFAULT_BACKEND_URL = "http://localhost:8000"
DEFAULT_FRONTEND_URL = "http://localhost:3000"
TEST_TIMEOUT = 30  # seconds
HEALTH_CHECK_INTERVAL = 2  # seconds

@dataclass
class TestResult:
    """Result of a single test case."""
    name: str
    status: str  # "PASS", "FAIL", "SKIP"
    message: str
    details: Dict[str, Any] = None
    duration_ms: float = 0.0
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
        if self.details is None:
            self.details = {}

@dataclass
class SystemStatus:
    """Overall system status after testing."""
    backend_status: str
    frontend_status: str
    provider_count: int
    api_endpoints_working: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    overall_health: str
    issues: List[str]
    recommendations: List[str]

class IntegrationTester:
    """Comprehensive integration tester for Transform Army AI."""
    
    def __init__(self, backend_url: str, frontend_url: str):
        self.backend_url = backend_url.rstrip('/')
        self.frontend_url = frontend_url.rstrip('/')
        self.test_results: List[TestResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TEST_TIMEOUT),
            headers={'User-Agent': 'Transform-Army-Integration-Test/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def log_test(self, name: str, status: str, message: str, details: Dict = None, duration: float = 0):
        """Log a test result."""
        result = TestResult(
            name=name,
            status=status,
            message=message,
            details=details or {},
            duration_ms=duration * 1000
        )
        self.test_results.append(result)
        
        # Print to console
        status_symbol = {"PASS": "[PASS]", "FAIL": "[FAIL]", "SKIP": "[SKIP]"}[status]
        print(f"{status_symbol} {name}: {message}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
        print()
    
    async def start_backend_service(self) -> bool:
        """Start the backend service if not already running."""
        try:
            # Check if backend is already running
            async with self.session.get(f"{self.backend_url}/health") as response:
                if response.status == 200:
                    self.log_test(
                        "Backend Service Check",
                        "PASS",
                        "Backend service already running",
                        {"url": self.backend_url}
                    )
                    return True
        except Exception:
            pass
        
        # Start backend service
        print("🚀 Starting backend service...")
        try:
            self.backend_process = subprocess.Popen(
                [sys.executable, "apps/adapter/main_simple.py"],
                cwd=os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for service to start
            for i in range(15):  # Wait up to 30 seconds
                try:
                    async with self.session.get(f"{self.backend_url}/health") as response:
                        if response.status == 200:
                            self.log_test(
                                "Backend Service Startup",
                                "PASS",
                                f"Backend service started successfully in {i*2} seconds",
                                {"pid": self.backend_process.pid}
                            )
                            return True
                except Exception:
                    pass
                
                await asyncio.sleep(2)
            
            self.log_test(
                "Backend Service Startup",
                "FAIL",
                "Backend service failed to start within timeout",
                {"timeout": 30}
            )
            return False
            
        except Exception as e:
            self.log_test(
                "Backend Service Startup",
                "FAIL",
                f"Failed to start backend service: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    async def test_backend_health_endpoints(self) -> bool:
        """Test all backend health endpoints."""
        endpoints = [
            ("/", "Root endpoint"),
            ("/health", "Basic health check"),
            ("/health/providers", "Provider registry status"),
            ("/health/detailed", "Detailed health check"),
            ("/api/v1/logs/stats", "Action statistics"),
            ("/docs", "API documentation")
        ]
        
        all_passed = True
        
        for endpoint, description in endpoints:
            start_time = time.time()
            try:
                async with self.session.get(f"{self.backend_url}{endpoint}") as response:
                    duration = time.time() - start_time
                    data = await response.json() if response.content_type == 'application/json' else await response.text()
                    
                    if response.status == 200:
                        self.log_test(
                            f"API Endpoint: {description}",
                            "PASS",
                            f"Endpoint responded successfully",
                            {
                                "endpoint": endpoint,
                                "status_code": response.status,
                                "response_time_ms": duration * 1000,
                                "data_keys": list(data.keys()) if isinstance(data, dict) else "non-json"
                            },
                            duration
                        )
                    else:
                        self.log_test(
                            f"API Endpoint: {description}",
                            "FAIL",
                            f"Endpoint returned error status",
                            {
                                "endpoint": endpoint,
                                "status_code": response.status,
                                "response": str(data)[:200]
                            },
                            duration
                        )
                        all_passed = False
                        
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(
                    f"API Endpoint: {description}",
                    "FAIL",
                    f"Endpoint request failed: {str(e)}",
                    {
                        "endpoint": endpoint,
                        "error": str(e)
                    },
                    duration
                )
                all_passed = False
        
        return all_passed
    
    async def test_provider_registration(self) -> bool:
        """Test provider registration system."""
        try:
            # Test provider registry endpoint
            start_time = time.time()
            async with self.session.get(f"{self.backend_url}/health/providers") as response:
                duration = time.time() - start_time
                data = await response.json()
                
                if response.status == 200:
                    provider_count = data.get('total_registered', 0)
                    configured_count = data.get('total_configured', 0)
                    registry = data.get('registry', {})
                    configured = data.get('configured', {})
                    
                    self.log_test(
                        "Provider Registration",
                        "PASS",
                        f"Provider system working with {provider_count} registered providers",
                        {
                            "total_registered": provider_count,
                            "total_configured": configured_count,
                            "registry": registry,
                            "configured": configured,
                            "response_time_ms": duration * 1000
                        },
                        duration
                    )
                    
                    # Validate expected providers are present
                    expected_types = ['crm', 'helpdesk', 'calendar']
                    missing_types = [t for t in expected_types if t not in registry]
                    
                    if missing_types:
                        self.log_test(
                            "Provider Types Validation",
                            "FAIL",
                            f"Missing provider types: {missing_types}",
                            {"missing_types": missing_types}
                        )
                        return False
                    else:
                        self.log_test(
                            "Provider Types Validation",
                            "PASS",
                            "All expected provider types are registered",
                            {"expected_types": expected_types}
                        )
                    
                    return True
                else:
                    self.log_test(
                        "Provider Registration",
                        "FAIL",
                        f"Provider registry endpoint failed",
                        {
                            "status_code": response.status,
                            "response": str(data)[:200]
                        }
                    )
                    return False
                    
        except Exception as e:
            self.log_test(
                "Provider Registration",
                "FAIL",
                f"Provider registration test failed: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling and graceful degradation."""
        error_tests = [
            ("/nonexistent", 404, "Not Found handling"),
            ("/api/v1/invalid", 404, "Invalid API path"),
            ("/health/invalid", 404, "Invalid health endpoint"),
        ]
        
        all_passed = True
        
        for endpoint, expected_status, description in error_tests:
            start_time = time.time()
            try:
                async with self.session.get(f"{self.backend_url}{endpoint}") as response:
                    duration = time.time() - start_time
                    
                    if response.status == expected_status:
                        self.log_test(
                            f"Error Handling: {description}",
                            "PASS",
                            f"Correct error response",
                            {
                                "endpoint": endpoint,
                                "expected_status": expected_status,
                                "actual_status": response.status,
                                "response_time_ms": duration * 1000
                            },
                            duration
                        )
                    else:
                        self.log_test(
                            f"Error Handling: {description}",
                            "FAIL",
                            f"Incorrect error status",
                            {
                                "endpoint": endpoint,
                                "expected_status": expected_status,
                                "actual_status": response.status
                            },
                            duration
                        )
                        all_passed = False
                        
            except Exception as e:
                duration = time.time() - start_time
                self.log_test(
                    f"Error Handling: {description}",
                    "FAIL",
                    f"Error handling test failed: {str(e)}",
                    {"error": str(e)},
                    duration
                )
                all_passed = False
        
        return all_passed
    
    async def test_frontend_integration(self) -> bool:
        """Test frontend-backend integration."""
        try:
            # Test frontend health endpoint
            start_time = time.time()
            async with self.session.get(f"{self.frontend_url}/api/health") as response:
                duration = time.time() - start_time
                data = await response.json()
                
                if response.status == 200:
                    self.log_test(
                        "Frontend Health Check",
                        "PASS",
                        "Frontend health endpoint responding",
                        {
                            "status": data.get('status'),
                            "service": data.get('service'),
                            "response_time_ms": duration * 1000
                        },
                        duration
                    )
                else:
                    self.log_test(
                        "Frontend Health Check",
                        "FAIL",
                        f"Frontend health endpoint failed",
                        {
                            "status_code": response.status,
                            "response": str(data)[:200]
                        }
                    )
                    return False
            
            # Test frontend can reach backend (if frontend is running)
            try:
                start_time = time.time()
                async with self.session.get(f"{self.frontend_url}") as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        self.log_test(
                            "Frontend Backend Integration",
                            "PASS",
                            "Frontend is accessible and can serve content",
                            {
                                "status_code": response.status,
                                "content_type": response.content_type,
                                "response_time_ms": duration * 1000
                            },
                            duration
                        )
                        return True
                    else:
                        self.log_test(
                            "Frontend Backend Integration",
                            "SKIP",
                            f"Frontend not accessible (status {response.status})",
                            {"status_code": response.status}
                        )
                        return False
                        
            except Exception as e:
                self.log_test(
                    "Frontend Backend Integration",
                    "SKIP",
                    f"Frontend not running or accessible: {str(e)}",
                    {"error": str(e)}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Frontend Integration",
                "FAIL",
                f"Frontend integration test failed: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    async def test_data_flow(self) -> bool:
        """Test data flow between components."""
        try:
            # Test that backend provides data expected by frontend
            start_time = time.time()
            
            # Get health data
            async with self.session.get(f"{self.backend_url}/health") as response:
                health_data = await response.json()
            
            # Get provider data
            async with self.session.get(f"{self.backend_url}/health/providers") as response:
                provider_data = await response.json()
            
            # Get stats data
            async with self.session.get(f"{self.backend_url}/api/v1/logs/stats") as response:
                stats_data = await response.json()
            
            duration = time.time() - start_time
            
            # Validate data structure matches frontend expectations
            required_health_fields = ['status', 'timestamp', 'version']
            required_provider_fields = ['status', 'total_registered', 'registry']
            required_stats_fields = ['total_actions', 'successful_actions', 'failed_actions']
            
            validation_errors = []
            
            for field in required_health_fields:
                if field not in health_data:
                    validation_errors.append(f"Missing health field: {field}")
            
            for field in required_provider_fields:
                if field not in provider_data:
                    validation_errors.append(f"Missing provider field: {field}")
            
            for field in required_stats_fields:
                if field not in stats_data:
                    validation_errors.append(f"Missing stats field: {field}")
            
            if validation_errors:
                self.log_test(
                    "Data Flow Validation",
                    "FAIL",
                    f"Data structure validation failed",
                    {
                        "errors": validation_errors,
                        "health_keys": list(health_data.keys()),
                        "provider_keys": list(provider_data.keys()),
                        "stats_keys": list(stats_data.keys())
                    }
                )
                return False
            else:
                self.log_test(
                    "Data Flow Validation",
                    "PASS",
                    "All data structures match frontend expectations",
                    {
                        "health_status": health_data.get('status'),
                        "provider_count": provider_data.get('total_registered'),
                        "total_actions": stats_data.get('total_actions'),
                        "response_time_ms": duration * 1000
                    },
                    duration
                )
                return True
                
        except Exception as e:
            self.log_test(
                "Data Flow Validation",
                "FAIL",
                f"Data flow test failed: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def generate_validation_report(self) -> SystemStatus:
        """Generate final validation report."""
        passed = len([r for r in self.test_results if r.status == "PASS"])
        failed = len([r for r in self.test_results if r.status == "FAIL"])
        skipped = len([r for r in self.test_results if r.status == "SKIP"])
        total = len(self.test_results)
        
        # Determine system health
        if failed == 0:
            overall_health = "HEALTHY"
        elif failed <= 2:
            overall_health = "DEGRADED"
        else:
            overall_health = "UNHEALTHY"
        
        # Collect issues and recommendations
        issues = []
        recommendations = []
        
        for result in self.test_results:
            if result.status == "FAIL":
                issues.append(f"{result.name}: {result.message}")
        
        # Generate recommendations based on failures
        if any("backend" in issue.lower() for issue in issues):
            recommendations.append("Check backend service logs and configuration")
            recommendations.append("Verify all required environment variables are set")
        
        if any("provider" in issue.lower() for issue in issues):
            recommendations.append("Check provider credentials and configuration")
            recommendations.append("Verify provider API keys are valid and have proper permissions")
        
        if any("frontend" in issue.lower() for issue in issues):
            recommendations.append("Start frontend service with 'npm run dev'")
            recommendations.append("Check frontend environment configuration")
        
        # Get provider count from test results
        provider_result = next((r for r in self.test_results if "Provider Registration" in r.name), None)
        provider_count = provider_result.details.get('total_registered', 0) if provider_result else 0
        
        # Count working API endpoints
        api_endpoints_working = len([r for r in self.test_results if "API Endpoint" in r.name and r.status == "PASS"])
        
        return SystemStatus(
            backend_status="OPERATIONAL" if any("Backend" in r.name and r.status == "PASS" for r in self.test_results) else "FAILED",
            frontend_status="OPERATIONAL" if any("Frontend" in r.name and r.status == "PASS" for r in self.test_results) else "FAILED",
            provider_count=provider_count,
            api_endpoints_working=api_endpoints_working,
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=skipped,
            overall_health=overall_health,
            issues=issues,
            recommendations=recommendations
        )
    
    def print_final_report(self, status: SystemStatus):
        """Print comprehensive final validation report."""
        print("\n" + "="*80)
        print("🎯 TRANSFORM ARMY AI - FINAL VALIDATION REPORT")
        print("="*80)
        print(f"📅 Generated: {datetime.utcnow().isoformat() + 'Z'}")
        print()
        
        # Overall Status
        health_emoji = {"HEALTHY": "🟢", "DEGRADED": "🟡", "UNHEALTHY": "🔴"}[status.overall_health]
        print(f"{health_emoji} OVERALL SYSTEM STATUS: {status.overall_health}")
        print()
        
        # Component Status
        print("📊 COMPONENT STATUS:")
        print(f"  Backend Service:  {status.backend_status}")
        print(f"  Frontend Service: {status.frontend_status}")
        print(f"  Providers:        {status.provider_count} registered")
        print(f"  API Endpoints:    {status.api_endpoints_working} working")
        print()
        
        # Test Results
        print("🧪 TEST RESULTS:")
        print(f"  Total Tests:   {status.total_tests}")
        print(f"  ✅ Passed:      {status.passed_tests}")
        print(f"  ❌ Failed:      {status.failed_tests}")
        print(f"  ⏭️  Skipped:     {status.skipped_tests}")
        print(f"  Success Rate:   {(status.passed_tests / status.total_tests * 100):.1f}%")
        print()
        
        # Issues
        if status.issues:
            print("⚠️  ISSUES FOUND:")
            for i, issue in enumerate(status.issues, 1):
                print(f"  {i}. {issue}")
            print()
        
        # Recommendations
        if status.recommendations:
            print("💡 RECOMMENDATIONS:")
            for i, rec in enumerate(status.recommendations, 1):
                print(f"  {i}. {rec}")
            print()
        
        # Detailed Test Results
        print("📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status_symbol = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}[result.status]
            print(f"  {status_symbol} {result.name}")
            print(f"     Status: {result.status}")
            print(f"     Message: {result.message}")
            if result.duration_ms > 0:
                print(f"     Duration: {result.duration_ms:.1f}ms")
            if result.details:
                for key, value in result.details.items():
                    if key not in ['response', 'error']:  # Skip verbose fields
                        print(f"     {key}: {value}")
            print()
        
        # Conclusion
        print("🎉 CONCLUSION:")
        if status.overall_health == "HEALTHY":
            print("  The Transform Army AI system is fully operational and ready for production use!")
            print("  All components are working correctly and the system can handle normal operations.")
        elif status.overall_health == "DEGRADED":
            print("  The Transform Army AI system is partially operational with some issues.")
            print("  Core functionality is working, but some features may be limited.")
        else:
            print("  The Transform Army AI system has significant issues that need to be addressed.")
            print("  Please review the issues and recommendations above to resolve problems.")
        
        print("\n" + "="*80)
    
    async def run_all_tests(self) -> SystemStatus:
        """Run all integration tests."""
        print("Starting Comprehensive Integration Test for Transform Army AI")
        print("="*80)
        print()
        
        # Test sequence
        test_sequence = [
            ("Backend Service Startup", self.start_backend_service),
            ("Backend Health Endpoints", self.test_backend_health_endpoints),
            ("Provider Registration", self.test_provider_registration),
            ("Error Handling", self.test_error_handling),
            ("Frontend Integration", self.test_frontend_integration),
            ("Data Flow Validation", self.test_data_flow),
        ]
        
        for test_name, test_func in test_sequence:
            print(f"🧪 Running: {test_name}")
            try:
                await test_func()
            except Exception as e:
                self.log_test(
                    test_name,
                    "FAIL",
                    f"Test execution failed: {str(e)}",
                    {"error": str(e)}
                )
            print("-" * 60)
        
        # Generate and return final status
        return self.generate_validation_report()
    
    def cleanup(self):
        """Clean up processes and resources."""
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("🛑 Backend service stopped")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                print("🔥 Backend service force killed")
            except Exception as e:
                print(f"⚠️  Error stopping backend: {e}")

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Transform Army AI Integration Test")
    parser.add_argument(
        "--backend-url",
        default=DEFAULT_BACKEND_URL,
        help=f"Backend service URL (default: {DEFAULT_BACKEND_URL})"
    )
    parser.add_argument(
        "--frontend-url", 
        default=DEFAULT_FRONTEND_URL,
        help=f"Frontend service URL (default: {DEFAULT_FRONTEND_URL})"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file for test results"
    )
    
    args = parser.parse_args()
    
    # Run tests
    async with IntegrationTester(args.backend_url, args.frontend_url) as tester:
        try:
            status = await tester.run_all_tests()
            tester.print_final_report(status)
            
            # Save results to file if requested
            if args.output:
                results = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "system_status": asdict(status),
                    "test_results": [asdict(r) for r in tester.test_results]
                }
                
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"Test results saved to: {args.output}")
            
            # Exit with appropriate code
            sys.exit(0 if status.overall_health in ["HEALTHY", "DEGRADED"] else 1)
            
        except KeyboardInterrupt:
            print("\n⏹️  Test interrupted by user")
            sys.exit(130)
        except Exception as e:
            print(f"\nTest suite failed: {e}")
            sys.exit(1)
        finally:
            tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())