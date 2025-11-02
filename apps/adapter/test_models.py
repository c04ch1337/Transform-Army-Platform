"""Test script to verify database models are correctly implemented."""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all models can be imported."""
    print("Testing model imports...")
    
    try:
        # Test base imports
        from models.base import Base, TimestampMixin, UUIDMixin, generate_uuid
        print("✓ Base classes imported successfully")
        
        # Test model imports
        from models import Tenant, ActionLog, AuditLog, ActionType, ActionStatus
        print("✓ All models imported successfully")
        
        # Test database import that was failing
        from core.database import init_db, engine, get_db
        print("✓ Database configuration imports successfully")
        
        # Verify model attributes
        assert hasattr(Tenant, '__tablename__')
        assert Tenant.__tablename__ == 'tenants'
        print("✓ Tenant model has correct table name")
        
        assert hasattr(ActionLog, '__tablename__')
        assert ActionLog.__tablename__ == 'action_logs'
        print("✓ ActionLog model has correct table name")
        
        assert hasattr(AuditLog, '__tablename__')
        assert AuditLog.__tablename__ == 'audit_logs'
        print("✓ AuditLog model has correct table name")
        
        # Verify enums
        assert hasattr(ActionType, 'CRM_CREATE')
        assert hasattr(ActionType, 'HELPDESK_CREATE_TICKET')
        assert hasattr(ActionType, 'CALENDAR_CREATE_EVENT')
        assert hasattr(ActionType, 'EMAIL_SEND')
        assert hasattr(ActionType, 'KNOWLEDGE_STORE')
        print("✓ ActionType enum has all required values")
        
        assert hasattr(ActionStatus, 'PENDING')
        assert hasattr(ActionStatus, 'SUCCESS')
        assert hasattr(ActionStatus, 'FAILURE')
        assert hasattr(ActionStatus, 'TIMEOUT')
        assert hasattr(ActionStatus, 'RETRY')
        print("✓ ActionStatus enum has all required values")
        
        # Verify relationships
        assert hasattr(Tenant, 'action_logs')
        assert hasattr(Tenant, 'audit_logs')
        print("✓ Tenant relationships defined")
        
        assert hasattr(ActionLog, 'tenant')
        print("✓ ActionLog relationship defined")
        
        assert hasattr(AuditLog, 'tenant')
        print("✓ AuditLog relationship defined")
        
        # Verify Base is properly configured
        assert Base is not None
        print("✓ Base declarative class is properly configured")
        
        print("\n✅ All tests passed! Models are correctly implemented.")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"\n❌ Assertion error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)