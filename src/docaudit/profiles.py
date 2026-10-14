"""Trusted bundled profiles and explicit section-exclusion policy."""
import fnmatch
import re
from pathlib import Path
from .config import load_config
from .models import AuditConfig, Section


def load_profile(name: str, directory: str | Path) -> AuditConfig:
    if name not in {"technical", "academic"}:
        raise ValueError("unknown_profile")
    return load_config(Path(directory) / f"{name}.yaml")


def is_excluded(section: Section, config: AuditConfig) -> bool:
    for title in section.heading_path or (section.title,):
        heading = re.sub(r"^\s*\d+(?:\.\d+)*[.)]?\s+", "", title).strip().casefold()
        if any(fnmatch.fnmatchcase(heading, pattern.strip().casefold()) for pattern in config.excluded_headings):
            return True
    return False
