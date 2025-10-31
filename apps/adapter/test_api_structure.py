"""
Simple script to verify API structure is correct.
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Add packages directory for schema imports
packages_dir = Path(__file__).parent.parent.parent / "packages" / "schema" / "src" / "python"
sys.path.insert(0, str(packages_dir))

print("=" * 60)
print("API STRUCTURE VERIFICATION")
print("=" * 60)

try:
    print("\n1. Testing imports...")
    from core.config import settings
    print("   ✓ Config imported successfully")
    
    from core.exceptions import AdapterException
    print("   ✓ Exceptions imported successfully")
    
    from core.dependencies import get_tenant_config
    print("   ✓ Dependencies imported successfully")
    
    from core.middleware import TenantMiddleware
    print("   ✓ Middleware imported successfully")
    
    print("\n2. Testing schema imports...")
    from crm import ContactResponse, NoteResponse, SearchContactsResponse
    print("   ✓ CRM schemas imported successfully")
    
    print("\n3. Testing API router...")
    from api.crm import router
    print(f"   ✓ CRM router imported successfully")
    print(f"   ✓ Routes registered: {len(router.routes)}")
    
    # List all routes
    print("\n4. Available CRM endpoints:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"   • {methods:10s} {route.path}")
    
    print("\n5. Testing main application...")
    from main import app
    print(f"   ✓ Main application imported successfully")
    print(f"   ✓ Total routes: {len([r for r in app.routes if hasattr(r, 'path')])}")
    
    print("\n" + "=" * 60)
    print("✓ ALL CHECKS PASSED - API STRUCTURE IS CORRECT")
    print("=" * 60)
    
    print("\n6. Example curl commands:")
    print("\nCreate Contact:")
    print('curl -X POST http://localhost:8000/api/v1/crm/create_contact \\')
    print('  -H "X-Tenant-ID: test-tenant" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"email":"test@example.com","first_name":"John","last_name":"Doe"}\'')
    
    print("\nUpdate Contact:")
    print('curl -X POST http://localhost:8000/api/v1/crm/update_contact \\')
    print('  -H "X-Tenant-ID: test-tenant" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"contact_id":"cont_123","updates":{"title":"VP of Sales"}}\'')
    
    print("\nSearch Contacts:")
    print('curl -X POST http://localhost:8000/api/v1/crm/search_contacts \\')
    print('  -H "X-Tenant-ID: test-tenant" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"query":"john","limit":10}\'')
    
    print("\nAdd Note:")
    print('curl -X POST http://localhost:8000/api/v1/crm/add_note \\')
    print('  -H "X-Tenant-ID: test-tenant" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"contact_id":"cont_123","note_text":"Follow-up call scheduled","note_type":"call_note"}\'')
    
    print("\n7. To start the server:")
    print("   cd apps/adapter")
    print("   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n   Then visit: http://localhost:8000/docs")
    
except ImportError as e:
    print(f"\n✗ Import Error: {e}")
    print(f"   This is expected if dependencies aren't installed yet.")
    print(f"   Run: cd apps/adapter && pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)