from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_PATH = PROJECT_ROOT / "outputs" / "inspecao_gold_ibge_postgres.json"

DATASETS = {
    "ibge_populacao_ano": (
        PROJECT_ROOT / "data" / "gold" / "ibge" / "populacao_brasil_por_ano.parquet"
    ),
    "ibge_pib_nominal_ano": (
        PROJECT_ROOT / "data" / "gold" / "ibge" / "pib_nominal_brasil_por_ano.parquet"
    ),
    "ibge_ipca_ano": (
        PROJECT_ROOT / "data" / "gold" / "ibge" / "ipca_brasil_por_ano.parquet"
    ),
    "pnad_estrutura_etaria_ano": (
        PROJECT_ROOT
        / "data"
        / "gold"
        / "ibge"
        / "estrutura_etaria_brasil_por_ano.parquet"
    ),
    "pnad_mercado_trabalho_ano": (
        PROJECT_ROOT
        / "data"
        / "gold"
        / "ibge"
        / "mercado_trabalho_brasil_por_ano.parquet"
    ),
    "pnad_contribuicao_previdenciaria_ano": (
        PROJECT_ROOT
        / "data"
        / "gold"
        / "ibge"
        / "contribuicao_previdenciaria_brasil_por_ano.parquet"
    ),
    "ibge_nucleo_anual": (
        PROJECT_ROOT / "data" / "gold" / "ibge" / "nucleo_ibge_anual.parquet"
    ),
}


class InspectionError(RuntimeError):
    """Erro durante a inspeção dos produtos Gold."""


def calculate_sha256(path: Path) -> str:
    """Calcula o hash SHA-256 de um arquivo."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def to_json_safe(value: Any) -> Any:
    """Converte valores do pandas e NumPy para JSON."""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass

    return value


def collect_examples(
    series: pd.Series,
    limit: int = 3,
) -> list[Any]:
    """Coleta exemplos distintos e não nulos."""
    examples: list[Any] = []
    seen: set[str] = set()

    for value in series:
        safe_value = to_json_safe(value)

        if safe_value is None:
            continue

        key = json.dumps(
            safe_value,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )

        if key in seen:
            continue

        seen.add(key)
        examples.append(safe_value)

        if len(examples) >= limit:
            break

    return examples


def count_distinct(
    series: pd.Series,
) -> int | None:
    """Conta valores distintos quando o tipo permite."""
    try:
        return int(series.nunique(dropna=True))
    except TypeError:
        return None


def inspect_column(
    dataframe: pd.DataFrame,
    parquet_schema: Any,
    column_name: str,
) -> dict[str, Any]:
    """Inspeciona uma coluna do DataFrame."""
    series = dataframe[column_name]

    parquet_type = None

    if column_name in parquet_schema.names:
        parquet_type = str(parquet_schema.field(column_name).type)

    result: dict[str, Any] = {
        "nome": column_name,
        "tipo_pandas": str(series.dtype),
        "tipo_parquet": parquet_type,
        "nulos": int(series.isna().sum()),
        "nao_nulos": int(series.notna().sum()),
        "valores_distintos": count_distinct(series),
        "exemplos": collect_examples(series),
    }

    if pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(
            series,
            errors="coerce",
        ).dropna()

        if not numeric.empty:
            result["minimo"] = to_json_safe(numeric.min())
            result["maximo"] = to_json_safe(numeric.max())

    elif pd.api.types.is_datetime64_any_dtype(series):
        valid_dates = series.dropna()

        if not valid_dates.empty:
            result["minimo"] = to_json_safe(valid_dates.min())
            result["maximo"] = to_json_safe(valid_dates.max())

    return result


def inspect_dataset(
    dataset: str,
    path: Path,
) -> dict[str, Any]:
    """Inspeciona um arquivo Parquet."""
    if not path.is_file():
        raise InspectionError(f"Arquivo não encontrado para {dataset}: {path}")

    parquet_schema = pq.read_schema(path)
    dataframe = pd.read_parquet(path)

    columns = [
        inspect_column(
            dataframe,
            parquet_schema,
            column_name,
        )
        for column_name in dataframe.columns
    ]

    first_year = None
    last_year = None
    year_count = None
    duplicate_year_rows = None

    if "exercicio" in dataframe.columns:
        years = pd.to_numeric(
            dataframe["exercicio"],
            errors="coerce",
        ).dropna()

        duplicate_year_rows = int(
            dataframe.duplicated(
                subset=["exercicio"],
                keep=False,
            ).sum()
        )

        if not years.empty:
            first_year = int(years.min())
            last_year = int(years.max())
            year_count = int(years.nunique())

    return {
        "dataset": dataset,
        "arquivo": str(path.relative_to(PROJECT_ROOT)),
        "tamanho_bytes": path.stat().st_size,
        "sha256": calculate_sha256(path),
        "linhas": int(len(dataframe)),
        "quantidade_colunas": int(len(dataframe.columns)),
        "colunas": columns,
        "verificacao_exercicio": {
            "primeiro_exercicio": first_year,
            "ultimo_exercicio": last_year,
            "quantidade_exercicios": year_count,
            "linhas_com_exercicio_duplicado": (duplicate_year_rows),
        },
    }


def print_summary(
    result: dict[str, Any],
) -> None:
    """Apresenta um resumo no terminal."""
    period = result["verificacao_exercicio"]

    print()
    print("=" * 78)
    print(f"DATASET: {result['dataset']}")
    print("=" * 78)
    print(f"Arquivo: {result['arquivo']}")
    print(f"Linhas: {result['linhas']}")
    print(f"Colunas: {result['quantidade_colunas']}")
    print(f"SHA-256: {result['sha256']}")

    if period["primeiro_exercicio"] is not None:
        print(
            f"Exercícios: {period['primeiro_exercicio']} a {period['ultimo_exercicio']}"
        )
        print(f"Exercícios distintos: {period['quantidade_exercicios']}")
        print(
            "Linhas com exercício duplicado: "
            f"{period['linhas_com_exercicio_duplicado']}"
        )

    print()
    print("COLUNAS")

    for index, column in enumerate(
        result["colunas"],
        start=1,
    ):
        line = (
            f"{index:02d}. {column['nome']}"
            f" | pandas={column['tipo_pandas']}"
            f" | parquet={column['tipo_parquet']}"
            f" | nulos={column['nulos']}"
            f" | distintos="
            f"{column['valores_distintos']}"
        )

        if "minimo" in column:
            line += f" | mínimo={column['minimo']}"

        if "maximo" in column:
            line += f" | máximo={column['maximo']}"

        print(line)
        print(f"    Exemplos: {column['exemplos']}")


def run_inspection() -> list[dict[str, Any]]:
    """Inspeciona todos os produtos configurados."""
    results: list[dict[str, Any]] = []

    for dataset, path in DATASETS.items():
        result = inspect_dataset(
            dataset,
            path,
        )

        results.append(result)
        print_summary(result)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "quantidade_datasets": len(results),
                "datasets": results,
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    return results


def main() -> int:
    try:
        results = run_inspection()

    except InspectionError as error:
        print(
            f"Erro de inspeção: {error}",
            file=sys.stderr,
        )
        return 1

    except Exception as error:
        print(
            f"Erro inesperado: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 2

    print()
    print("=" * 78)
    print("INSPEÇÃO CONCLUÍDA")
    print("=" * 78)
    print(f"Datasets inspecionados: {len(results)}")
    print(f"Relatório salvo em: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
