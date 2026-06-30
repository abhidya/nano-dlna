# This file makes 'web/backend' a Python package.
#
# Much of the backend uses app-root imports such as `from database.database`
# because production scripts run from this directory. Package imports
# (`web.backend.main`) need the same import root during tests.
import os
import sys

backend_dir = os.path.dirname(__file__)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
