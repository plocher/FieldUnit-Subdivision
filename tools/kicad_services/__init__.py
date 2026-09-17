"""Generic KiCad read services (jBOM-shaped; candidate for a shared API later)."""

from __future__ import annotations

import sys
from pathlib import Path

# POC: prefer an installed jbom; otherwise use the local Dropbox checkout.
_JBOM_SRC = Path.home() / "Dropbox" / "KiCad" / "jBOM" / "src"
if _JBOM_SRC.is_dir() and str(_JBOM_SRC) not in sys.path:
    sys.path.insert(0, str(_JBOM_SRC))
