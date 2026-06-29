import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceConfig:
    name: str
    type: str
    source: str
    theme: str
    params: dict[str, Any]


@dataclass(frozen=True)
class EtlConfig:
    project_name: str
    sources: list[SourceConfig]


def load_config(path: Path) -> EtlConfig:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    sources = []
    for item in data.get("sources", []):
        base_keys = {"name", "type", "source", "theme"}
        params = {key: value for key, value in item.items() if key not in base_keys}
        sources.append(
            SourceConfig(
                name=item["name"],
                type=item["type"],
                source=item["source"],
                theme=item["theme"],
                params=params,
            )
        )

    return EtlConfig(project_name=data.get("project_name", "observatorio_etl"), sources=sources)
