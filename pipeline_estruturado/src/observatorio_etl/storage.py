import json
from pathlib import Path
from typing import Any

import pandas as pd

from observatorio_etl.paths import ensure_dir


def write_json(path: Path, data: Any) -> Path:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    return path


def write_dataframe(path: Path, dataframe: pd.DataFrame) -> Path:
    ensure_dir(path.parent)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        dataframe.to_csv(path, index=False, encoding="utf-8")
    elif suffix == ".parquet":
        dataframe.to_parquet(path, index=False)
    else:
        raise ValueError(f"Formato não suportado: {suffix}")
    return path
