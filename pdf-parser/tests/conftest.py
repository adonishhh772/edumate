"""Pytest configuration for uok-doc-parser tests.

Adds the project root to sys.path so `import app.main` resolves regardless of
where pytest is invoked from (root or tests/).
"""

from __future__ import annotations

import sys
from pathlib import Path


_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
