#!/usr/bin/env python3
"""
Simple debug script to test provider imports without Unicode issues.
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("TRANSFORM ARMY AI - DEBUG SCRIPT")
    print("=" * 50)
    
    # Test 1: Check file structure
    print("\n1. CHECKING FILE STRUCTURE:")
    base_dir = Path(__file__).parent / "src" / "providers"
    
    required_files = [
        "base.py",
        "registry.py", 
        "factory.py",
        "crm/__init__.py",
        "crm/hubspot.py",
        "helpdesk/__init__.py",
        "helpdesk/zendesk.py",
        "calendar/__init__.py",
        "calendar/google.py",
        "email/__init__.py",
        "email/gmail.py"
    ]
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"   EXISTS: {file_path}")
        else:
            print(f"   MISSING: {file_path}")
    
    # Test 2: Try imports
    print("\n2. TESTING IMPORTS:")
    
    # Base imports
    try:
        from providers.base import ProviderPlugin, CRMProvider
        print("   SUCCESS: Base providers")
    except Exception as e:
        print(f"   FAILED: Base providers - {e}")
    
    # Registry imports
    try:
        from providers.registry import ProviderType, register_provider
        print("   SUCCESS: Registry")
    except Exception as e:
        print(f"   FAILED: Registry - {e}")
    
    # Factory imports
    try:
        from providers.factory import register_provider as factory_register
        print("   SUCCESS: Factory")
    except Exception as e:
        print(f"   FAILED: Factory - {e}")
    
    # CRM imports
    try:
        from providers.crm import HubSpotProvider
        print("   SUCCESS: CRM HubSpot")
    except Exception as e:
        print(f"   FAILED: CRM HubSpot - {e}")
    
    # Helpdesk imports
    try:
        from providers.helpdesk import ZendeskProvider
        print("   SUCCESS: Helpdesk Zendesk")
    except Exception as e:
        print(f"   FAILED: Helpdesk Zendesk - {e}")
    
    # Calendar imports
    try:
        from providers.calendar import GoogleCalendarProvider
        print("   SUCCESS: Calendar Google")
    except Exception as e:
        print(f"   FAILED: Calendar Google - {e}")
    
    # Email imports
    try:
        from providers.email import GmailProvider
        print("   SUCCESS: Email Gmail")
    except Exception as e:
        print(f"   FAILED: Email Gmail - {e}")
    
    # Test 3: Check for duplicate definitions
    print("\n3. CHECKING FOR DUPLICATES:")
    try:
        from providers.registry import ProviderType as RegistryProviderType
        from providers.factory import ProviderType as FactoryProviderType
        
        if RegistryProviderType.CRM.value == FactoryProviderType.CRM.value:
            print("   WARNING: Duplicate ProviderType definitions found")
            print("   This causes import conflicts!")
        
    except Exception as e:
        print(f"   FAILED: Duplicate check - {e}")
    
    print("\nDIAGNOSIS COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()