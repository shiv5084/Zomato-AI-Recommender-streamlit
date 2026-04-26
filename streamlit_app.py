"""Streamlit Cloud entrypoint for Phase 8.

This file sits at the repo root so Streamlit Community Cloud can discover it
as the default app entrypoint. It adds src/ to PYTHONPATH and delegates to
the main application logic inside src/phase8/app.py.
"""

import sys
from pathlib import Path

_src = Path(__file__).parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from phase8.app import main

if __name__ == "__main__":
    main()
