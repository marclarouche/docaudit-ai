"""Safe loading and validation of local style-guide configuration."""
from pathlib import Path
import yaml
from .models import AuditConfig

def load_config(path: str | Path) -> AuditConfig:
    raw = Path(path).read_bytes()
    if len(raw) > 64 * 1024:
        raise ValueError("configuration_size_limit")
    return AuditConfig.model_validate(yaml.safe_load(raw))
