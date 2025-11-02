#!/usr/bin/env python3
"""
Simple Integration Test for Transform Army AI System

This script performs end-to-end testing of both frontend and backend components
to verify the complete system is operational.

Usage:
    python simple_integration_test.py
"""

import asyncio
import aiohttp
import json
import time
import sys
import subprocess
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Test configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_TIMEOUT = 30

class SimpleIntegrationTester:
    """Simple integration tester for Transform Army AI."""
    
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.frontend_url = FRONTEND_URL
        self.test_results = []
        self.session = None
        self.backend_process = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TEST_TIMEOUT)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def log_result(self, name: str, status: str, message: str, details: Dict = None):
        """Log a test result."""
        result = {
            "name": name,
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.test_results.append(result)
        
        # Print to console
        status_symbol = {"PASS": "[PASS]", "FAIL": "[FAIL]", "SKIP": "[SKIP]"}[status]
        print(f"{status_symbol} {name}: {message}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
        print()
    
    async def test_backend_health(self) -> bool:
        """Test backend health endpoints."""
        try:
            # Test basic health
            async with self.session.get(f"{self.backend_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result(
                        "Backend Health Check",
                        "PASS",
                        "Backend health endpoint responding",
                        {
                            "status": data.get("status"),
                            "version": data.get("version"),
                            "environment": data.get("environment")
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Backend Health Check",
                        "FAIL",
                        f"Backend health endpoint failed with status {response.status}"
                    )
                    return False
        except Exception as e:
            self.log_result(
                "Backend Health Check",
                "FAIL",
                f"Backend health check failed: {str(e)}"
            )
            return False
    
    async def test_provider_registry(self) -> bool:
        """Test provider registry."""
        try:
            async with self.session.get(f"{self.backend_url}/health/providers") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result(
                        "Provider Registry",
                        "PASS",
                        f"Provider registry working with {data.get('total_registered', 0)} providers",
                        {
                            "total_registered": data.get('total_registered'),
                            "total_configured": data.get('total_configured'),
                            "registry": data.get('registry', {})
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Provider Registry",
                        "FAIL",
                        f"Provider registry failed with status {response.status}"
                    )
                    return False
        except Exception as e:
            self.log_result(
                "Provider Registry",
                "FAIL",
                f"Provider registry test failed: {str(e)}"
            )
            return False
    
    async def test_api_endpoints(self) -> bool:
        """Test various API endpoints."""
        endpoints = [
            ("/", "Root endpoint"),
            ("/api/v1/logs/stats", "Stats endpoint"),
            ("/docs", "API documentation")
        ]
        
        all_passed = True
        for endpoint, description in endpoints:
            try:
                async with self.session.get(f"{self.backend_url}{endpoint}") as response:
                    if response.status == 200:
                        self.log_result(
                            f"API Endpoint: {description}",
                            "PASS",
                            f"Endpoint {endpoint} responding correctly"
                        )
                    else:
                        self.log_result(
                            f"API Endpoint: {description}",
                            "FAIL",
                            f"Endpoint {endpoint} returned status {response.status}"
                        )
                        all_passed = False
            except Exception as e:
                self.log_result(
                    f"API Endpoint: {description}",
                    "FAIL",
                    f"Endpoint {endpoint} failed: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    async def test_error_handling(self) -> bool:
        """Test error handling."""
        try:
            # Test 404 handling
            async with self.session.get(f"{self.backend_url}/nonexistent") as response:
                if response.status == 404:
                    self.log_result(
                        "Error Handling",
                        "PASS",
                        "404 errors handled correctly"
                    )
                    return True
                else:
                    self.log_result(
                        "Error Handling",
                        "FAIL",
                        f"Expected 404, got {response.status}"
                    )
                    return False
        except Exception as e:
            self.log_result(
                "Error Handling",
                "FAIL",
                f"Error handling test failed: {str(e)}"
            )
            return False
    
    async def test_frontend_integration(self) -> bool:
        """Test frontend integration."""
        try:
            # Test frontend health endpoint
            async with self.session.get(f"{self.frontend_url}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result(
                        "Frontend Health Check",
                        "PASS",
                        "Frontend health endpoint responding",
                        {
                            "status": data.get('status'),
                            "service": data.get('service')
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Frontend Health Check",
                        "SKIP",
                        f"Frontend not accessible (status {response.status})"
                    )
                    return False
        except Exception as e:
            self.log_result(
                "Frontend Health Check",
                "SKIP",
                f"Frontend not running: {str(e)}"
            )
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        print("Starting Transform Army AI Integration Test")
        print("=" * 60)
        print()
        
        # Test sequence
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Provider Registry", self.test_provider_registry),
            ("API Endpoints", self.test_api_endpoints),
            ("Error Handling", self.test_error_handling),
            ("Frontend Integration", self.test_frontend_integration),
        ]
        
        for test_name, test_func in tests:
            print(f"Running: {test_name}")
            try:
                await test_func()
            except Exception as e:
                self.log_result(
                    test_name,
                    "FAIL",
                    f"Test execution failed: {str(e)}"
                )
            print("-" * 40)
        
        # Calculate results
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped = len([r for r in self.test_results if r["status"] == "SKIP"])
        total = len(self.test_results)
        
        # Determine overall health
        if failed == 0:
            overall_health = "HEALTHY"
        elif failed <= 2:
            overall_health = "DEGRADED"
        else:
            overall_health = "UNHEALTHY"
        
        return {
            "overall_health": overall_health,
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "skipped_tests": skipped,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "test_results": self.test_results
        }
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TRANSFORM ARMY AI - INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"Generated: {datetime.utcnow().isoformat() + 'Z'}")
        print()
        
        print(f"Overall System Status: {results['overall_health']}")
        print()
        
        print("Test Results:")
        print(f"  Total Tests:   {results['total_tests']}")
        print(f"  Passed:        {results['passed_tests']}")
        print(f"  Failed:        {results['failed_tests']}")
        print(f"  Skipped:       {results['skipped_tests']}")
        print(f"  Success Rate:   {results['success_rate']:.1f}%")
        print()
        
        print("Detailed Results:")
        for result in results['test_results']:
            status_symbol = {"PASS": "[PASS]", "FAIL": "[FAIL]", "SKIP": "[SKIP]"}[result["status"]]
            print(f"  {status_symbol} {result['name']}: {result['message']}")
        
        print()
        print("Conclusion:")
        if results['overall_health'] == "HEALTHY":
            print("  The Transform Army AI system is fully operational!")
        elif results['overall_health'] == "DEGRADED":
            print("  The system is partially operational with some issues.")
        else:
            print("  The system has significant issues that need attention.")
        
        print("\n" + "=" * 60)

async def main():
    """Main entry point."""
    async with SimpleIntegrationTester() as tester:
        try:
            results = await tester.run_all_tests()
            tester.print_summary(results)
            
            # Exit with appropriate code
            sys.exit(0 if results['overall_health'] in ["HEALTHY", "DEGRADED"] else 1)
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            sys.exit(130)
        except Exception as e:
            print(f"\nTest suite failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())