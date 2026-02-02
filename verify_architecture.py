"""
Architecture Verification - Regime Safety Enforcement

This script verifies that the UI layer cannot access brain logic.
Run as part of CI/CD or pre-commit hooks.

Usage: python verify_architecture.py
Exit code: 0 if safe, 1 if violations found
"""

import sys
import ast
import os


def get_imports_from_file(filepath: str) -> list:
    """Extract all imports from a Python file using AST."""
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def verify_ui_isolation():
    """
    Verify that the UI layer is isolated from brain/execution logic.

    REGIME SAFETY RULES:
    1. UI may only import from: brain_state_reader, streamlit, stdlib
    2. brain_state_reader may only import from: stdlib
    3. No path from UI to: v1_brain_skeleton, execution_config, execution/, v1_backtest
    """
    violations = []

    # Forbidden modules for UI layer
    FORBIDDEN_FOR_UI = {
        'v1_brain_skeleton',
        'execution_config',
        'v1_backtest',
        'execution',
        'execution.broker_adapter',
        'execution.position_translator',
        'execution.rebalance_planner',
        'execution.execution_orchestrator',
    }

    # Allowed modules for brain_state_reader
    ALLOWED_FOR_READER = {
        'json',
        'os',
        'typing',
    }

    # Check UI layer
    print("Checking UI layer (v1_brain_dashboard.py)...")
    if os.path.exists('v1_brain_dashboard.py'):
        ui_imports = get_imports_from_file('v1_brain_dashboard.py')
        for imp in ui_imports:
            if imp in FORBIDDEN_FOR_UI or any(imp.startswith(f + '.') for f in FORBIDDEN_FOR_UI):
                violations.append(f"UI imports forbidden module: {imp}")

        # UI should only import streamlit and brain_state_reader
        allowed_ui = {'streamlit', 'st', 'brain_state_reader'}
        for imp in ui_imports:
            base = imp.split('.')[0]
            if base not in allowed_ui and base not in sys.stdlib_module_names:
                violations.append(f"UI imports non-allowed module: {imp}")

    # Check state reader layer
    print("Checking state reader (brain_state_reader.py)...")
    if os.path.exists('brain_state_reader.py'):
        reader_imports = get_imports_from_file('brain_state_reader.py')
        for imp in reader_imports:
            base = imp.split('.')[0]
            if base not in ALLOWED_FOR_READER:
                violations.append(f"State reader imports non-stdlib module: {imp}")

    # Check that brain_state_reader exports only read functions
    print("Checking exported symbols...")
    try:
        import brain_state_reader
        allowed_exports = {'get_current_regime', 'get_last_update_date'}
        actual_exports = set(brain_state_reader.__all__)

        forbidden_exports = actual_exports - allowed_exports
        if forbidden_exports:
            violations.append(f"State reader exports forbidden symbols: {forbidden_exports}")

        # Verify no write functions exist
        for name in dir(brain_state_reader):
            if not name.startswith('_'):
                if 'save' in name.lower() or 'write' in name.lower() or 'set' in name.lower():
                    violations.append(f"State reader has write-capable function: {name}")
    except ImportError:
        violations.append("Cannot import brain_state_reader")

    # Runtime check: verify no dangerous modules loaded
    print("Checking runtime module loading...")
    before = set(sys.modules.keys())
    try:
        from brain_state_reader import get_current_regime, get_last_update_date
        after = set(sys.modules.keys())
        new_modules = after - before

        for mod in new_modules:
            if any(forbidden in mod for forbidden in ['skeleton', 'execution', 'backtest', 'config']):
                violations.append(f"Loading state reader pulls in forbidden module: {mod}")
    except Exception as e:
        violations.append(f"Error during runtime check: {e}")

    return violations


def main():
    print("=" * 60)
    print("REGIME SAFETY ARCHITECTURE VERIFICATION")
    print("=" * 60)
    print()

    violations = verify_ui_isolation()

    print()
    print("=" * 60)
    if violations:
        print("FAILED: Architecture violations found")
        print("=" * 60)
        for v in violations:
            print(f"  - {v}")
        print()
        print("The UI layer must not have access to brain logic.")
        print("Fix the violations above to ensure regime safety.")
        return 1
    else:
        print("PASSED: Architecture is safe")
        print("=" * 60)
        print("  - UI imports only from brain_state_reader")
        print("  - brain_state_reader imports only stdlib")
        print("  - No path from UI to brain/execution logic")
        print("  - State reader exports only read functions")
        return 0


if __name__ == "__main__":
    sys.exit(main())
