import pytest
import sys
from pathlib import Path

# Ensure the project root is on the Python path so that `web.backend` can be imported
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session", autouse=True)
def clear_global_sqlalchemy_metadata_for_tests_directory(request):
    """
    Fixture to clear SQLAlchemy global metadata before tests in the 'tests/'
    directory run. This helps prevent "Table already defined" errors when
    models are imported multiple times across different test files that
    share the same global Base.metadata.
    """
    try:
        from web.backend.database.database import Base
        print("INFO: tests/conftest.py: clear_global_sqlalchemy_metadata_for_tests_directory fixture running.")
        # print("Clearing Base.metadata for tests/ directory session.")
        # Base.metadata.clear() # Commenting this out as it likely causes "no such table" errors for web/backend/tests_backend/
        print("INFO: tests/conftest.py: Base.metadata.clear() is currently COMMENTED OUT.")
    except ImportError:
        print("Warning: Could not import Base to clear metadata in tests/conftest.py.")
    except Exception as e:
        print(f"Warning: Error clearing metadata in tests/conftest.py: {e}")
