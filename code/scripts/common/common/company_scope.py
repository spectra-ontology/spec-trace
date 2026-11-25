"""Share the Company inclusion threshold across initial builds and meeting updates."""
import json
from pathlib import Path


def company_min_tdocs(scope: dict) -> int:
    """Return the recorded Company inclusion threshold for a reproducible build."""
    value = scope.get("company_min_tdocs", 10)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("company_min_tdocs는 1 이상의 정수여야 한다")
    return value


def recorded_company_min_tdocs(root: Path) -> int:
    """Read the existing build scope; an installation without a scope uses ten."""
    path = root / "logs/common/bootstrap/scope.json"
    if not path.exists():
        return company_min_tdocs({})
    scope = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(scope, dict):
        raise ValueError(f"구축 범위는 JSON 객체여야 합니다: {path}")
    return company_min_tdocs(scope)
