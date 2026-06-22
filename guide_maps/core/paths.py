"""Shared paths for open-guide-maps."""

from __future__ import annotations

import os
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = CORE_DIR.parent
PROJECT_ROOT = PACKAGE_DIR.parent

THEMES_DIR = Path(os.environ.get("OPEN_GUIDE_MAPS_THEMES_DIR") or PACKAGE_DIR / "themes")
FONTS_DIR = Path(os.environ.get("OPEN_GUIDE_MAPS_FONTS_DIR") or PACKAGE_DIR / "fonts")
CACHE_DIR = Path(os.environ.get("OPEN_GUIDE_MAPS_CACHE_DIR") or PROJECT_ROOT / "cache")
OUTPUTS_DIR = Path(os.environ.get("OPEN_GUIDE_MAPS_OUTPUTS_DIR") or PROJECT_ROOT / "outputs")
POSTERS_DIR = Path(os.environ.get("OPEN_GUIDE_MAPS_POSTERS_DIR") or OUTPUTS_DIR / "posters")
STYLIZED_DIR = Path(os.environ.get("OPEN_GUIDE_MAPS_STYLIZED_DIR") or OUTPUTS_DIR / "stylized")
POI_SETS_DIR = Path(os.environ.get("OPEN_GUIDE_MAPS_POI_SETS_DIR") or OUTPUTS_DIR / "poi_sets")


def ensure_runtime_dirs() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    POI_SETS_DIR.mkdir(parents=True, exist_ok=True)
    POSTERS_DIR.mkdir(parents=True, exist_ok=True)
    STYLIZED_DIR.mkdir(parents=True, exist_ok=True)

