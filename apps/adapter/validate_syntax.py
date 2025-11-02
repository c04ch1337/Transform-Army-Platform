"""Syntax validation script for database models.

This script validates Python syntax without requiring dependencies to be installed.
"""

import py_compile
import sys
from pathlib import Path


def validate_file_syntax(file_path: Path) -> tuple[bool, str]:
    """Validate Python syntax of a file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Tuple of (success, message)
    """
    try:
        py_compile.compile(str(file_path), doraise=True)
        return True, f"[OK] {file_path.name}: Syntax valid"
    except py_compile.PyCompileError as e:
        return False, f"[ERROR] {file_path.name}: Syntax error\n  {e}"


def main() -> int:
    """Validate all model files."""
    print("Validating database model syntax...\n")
    
    models_dir = Path(__file__).parent / "src" / "models"
    
    if not models_dir.exists():
        print(f"✗ Models directory not found: {models_dir}")
        return 1
    
    # Files to validate
    model_files = [
        models_dir / "__init__.py",
        models_dir / "base.py",
        models_dir / "tenant.py",
        models_dir / "action_log.py",
        models_dir / "audit_log.py",
    ]
    
    all_valid = True
    
    for file_path in model_files:
        if not file_path.exists():
            print(f"[ERROR] File not found: {file_path.name}")
            all_valid = False
            continue
        
        valid, message = validate_file_syntax(file_path)
        print(message)
        
        if not valid:
            all_valid = False
    
    print("\n" + "=" * 60)
    
    if all_valid:
        print("SUCCESS: All model files have valid Python syntax!")
        print("\nModel structure created:")
        print("  - base.py          (Base classes and mixins)")
        print("  - tenant.py        (Tenant model)")
        print("  - action_log.py    (ActionLog model with enums)")
        print("  - audit_log.py     (AuditLog model)")
        print("  - __init__.py      (Package exports)")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Configure database connection in .env")
        print("  3. Run migrations: alembic upgrade head")
        return 0
    else:
        print("FAILED: Some files have syntax errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())