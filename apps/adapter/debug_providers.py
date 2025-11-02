#!/usr/bin/env python3
"""
Debug script to validate provider registration and imports.
Run this script to identify the exact issues preventing backend startup.
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all provider imports and report issues."""
    print("🔍 TESTING PROVIDER IMPORTS...")
    print("=" * 50)
    
    # Test base imports
    try:
        from providers.base import ProviderPlugin, CRMProvider, HelpdeskProvider, CalendarProvider
        print("✅ Base provider imports: SUCCESS")
    except Exception as e:
        print(f"❌ Base provider imports: FAILED - {e}")
        traceback.print_exc()
    
    # Test registry imports
    try:
        from providers.registry import ProviderType, register_provider
        print("✅ Registry imports: SUCCESS")
    except Exception as e:
        print(f"❌ Registry imports: FAILED - {e}")
        traceback.print_exc()
    
    # Test factory imports
    try:
        from providers.factory import register_provider as factory_register_provider
        print("✅ Factory imports: SUCCESS")
    except Exception as e:
        print(f"❌ Factory imports: FAILED - {e}")
        traceback.print_exc()
    
    print("\n🔍 TESTING PROVIDER IMPLEMENTATIONS...")
    print("=" * 50)
    
    # Test CRM providers
    try:
        from providers.crm import HubSpotProvider, SalesforceProvider
        print("✅ CRM providers: SUCCESS")
        print(f"   - HubSpotProvider: {HubSpotProvider}")
        print(f"   - SalesforceProvider: {SalesforceProvider}")
    except Exception as e:
        print(f"❌ CRM providers: FAILED - {e}")
        traceback.print_exc()
    
    # Test Helpdesk providers
    try:
        from providers.helpdesk import ZendeskProvider
        print("✅ Helpdesk providers: SUCCESS")
        print(f"   - ZendeskProvider: {ZendeskProvider}")
    except Exception as e:
        print(f"❌ Helpdesk providers: FAILED - {e}")
        traceback.print_exc()
    
    # Test Calendar providers
    try:
        from providers.calendar import GoogleCalendarProvider
        print("✅ Calendar providers: SUCCESS")
        print(f"   - GoogleCalendarProvider: {GoogleCalendarProvider}")
    except Exception as e:
        print(f"❌ Calendar providers: FAILED - {e}")
        traceback.print_exc()
    
    # Test Email providers
    try:
        from providers.email import GmailProvider
        print("✅ Email providers: SUCCESS")
        print(f"   - GmailProvider: {GmailProvider}")
    except Exception as e:
        print(f"❌ Email providers: FAILED - {e}")
        traceback.print_exc()

def test_file_structure():
    """Check if all required provider files exist."""
    print("\n" + "=" * 50 + " TESTING FILE STRUCTURE..." + "=" * 50)
    
    base_dir = Path(__file__).parent / "providers"
    
    required_files = [
        "base.py",
        "registry.py", 
        "factory.py",
        "crm/__init__.py",
        "crm/hubspot.py",
        "crm/salesforce.py",
        "helpdesk/__init__.py",
        "helpdesk/zendesk.py",
        "calendar/__init__.py",
        "calendar/google.py",
        "email/__init__.py",
        "email/gmail.py",
        "knowledge/__init__.py"
    ]
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")

def test_config():
    """Test configuration loading."""
    print("\n🔍 TESTING CONFIGURATION...")
    print("=" * 50)
    
    try:
        from core.config import settings
        print("✅ Settings import: SUCCESS")
        
        # Check critical settings
        print(f"   Database URL: {settings.DATABASE_URL[:20]}...")
        print(f"   Redis URL: {settings.REDIS_URL}")
        print(f"   API Secret Key: {'SET' if len(settings.API_SECRET_KEY) > 31 else 'NOT SET/TOO SHORT'}")
        print(f"   Environment: {settings.environment}")
        
    except Exception as e:
        print(f"❌ Configuration test: FAILED - {e}")
        traceback.print_exc()

def test_api_imports():
    """Test API router imports."""
    print("\n🔍 TESTING API IMPORTS...")
    print("=" * 50)
    
    api_modules = [
        "api.crm",
        "api.helpdesk", 
        "api.calendar",
        "api.email",
        "api.knowledge",
        "api.admin",
        "api.logs",
        "api.workflows",
        "api.metrics"
    ]
    
    for module in api_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module} - {e}")

if __name__ == "__main__":
    print("TRANSFORM ARMY AI - PROVIDER DEBUG SCRIPT")
    print("=" * 50)
    
    test_file_structure()
    test_imports()
    test_config()
    test_api_imports()
    
    print("\n🎯 DIAGNOSIS COMPLETE")
    print("=" * 50)
    print("Review the output above to identify the specific issues")
    print("preventing the backend service from starting.")