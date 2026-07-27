import json
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import pandas as pd

from observatorio_etl.http_client import HttpClient


SPECIAL_VALUES = {None, "", "...", "..", "-", "X", "x"}
MONTH_NAMES = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


class SidraClient:
    def __init__(self, http_client: HttpClient | None = None):
        self.http_client = http_client or HttpClient()
        self.base_url = "https://apisidra.ibge.gov.br/values"
        self.metadata_base_url = "https://servicodados.ibge.gov.br/api/v3/agregados"

    def fetch_table(
        self,
        table: str,
        variable: str | list[str],
        period: str | list[str],
        territorial_level: str,
        localities: str | list[str],
        decimals: str | None = None,
        classifications: dict[str, str | list[str]] | None = None,
    ) -> list[dict[str, Any]]:
        url = self.build_table_url(
            table=table,
            variable=variable,
            period=period,
            territorial_level=territorial_level,
            localities=localities,
            decimals=decimals,
            classifications=classifications,
        )
        result = self.http_client.get_json(url)

        if not isinstance(result, list):
            raise RuntimeError(
                f"O SIDRA retornou um formato inesperado para a tabela {table}."
            )

        return result

    def fetch_metadata(self, table: str) -> Any:
        url = f"{self.metadata_base_url}/{table}/metadados"
        return self.http_client.get_json(url)

    def resolve_classifications(
        self,
        metadata: Any,
        requested: str | dict[str, str | list[str]] | None,
    ) -> dict[str, str | list[str]]:
        if requested is None:
            return {}

        if isinstance(requested, dict):
            return requested

        if requested != "all":
            raise ValueError(
                "O campo 'classifications' deve ser um objeto JSON, 'all' ou nulo."
            )

        classification_ids = extract_classification_ids(metadata)
        return {classification_id: "all" for classification_id in classification_ids}

    def build_table_url(
        self,
        table: str,
        variable: str | list[str],
        period: str | list[str],
        territorial_level: str,
        localities: str | list[str],
        decimals: str | None = None,
        classifications: dict[str, str | list[str]] | None = None,
    ) -> str:
        variable_selection = format_selection(variable)
        period_selection = format_selection(period)
        locality_selection = format_selection(localities)

        path = (
            f"/t/{table}"
            f"/n{territorial_level}/{locality_selection}"
            f"/v/{variable_selection}"
            f"/p/{period_selection}"
        )

        for classification_id, categories in sorted(
            (classifications or {}).items(),
            key=lambda item: (
                (0, int(item[0])) if str(item[0]).isdigit() else (1, str(item[0]))
            ),
        ):
            category_selection = format_selection(categories)
            path += f"/c{classification_id}/{category_selection}"

        if (
            decimals is not None
            and variable_selection.lower() != "all"
            and "," not in variable_selection
        ):
            path += f"/d/v{variable_selection}%20{quote(str(decimals))}"

        return f"{self.base_url}{path}"

    def build_query_description(
        self,
        table: str,
        variable: str | list[str],
        period: str | list[str],
        territorial_level: str,
        localities: str | list[str],
        decimals: str | None = None,
        classifications: dict[str, str | list[str]] | None = None,
    ) -> dict[str, Any]:
        return {
            "table": table,
            "variable": variable,
            "period": period,
            "territorial_level": territorial_level,
            "localities": localities,
            "decimals": decimals,
            "classifications": classifications or {},
            "url": self.build_table_url(
                table=table,
                variable=variable,
                period=period,
                territorial_level=territorial_level,
                localities=localities,
                decimals=decimals,
                classifications=classifications,
            ),
        }


def format_selection(value: str | list[str]) -> str:
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


def extract_classification_ids(metadata: Any) -> list[str]:
    discovered: set[str] = set()

    def walk(value: Any, parent_key: str = "") -> None:
        if isinstance(value, dict):
            normalized_parent = normalize_text(parent_key)
            identifier = value.get("id")

            if (
                identifier is not None
                and "classific" in normalized_parent
                and str(identifier).strip()
            ):
                discovered.add(str(identifier))

            for key, child in value.items():
                walk(child, str(key))
            return

        if isinstance(value, list):
            for child in value:
                walk(child, parent_key)

    walk(metadata)

    return sorted(
        discovered,
        key=lambda item: (0, int(item)) if item.isdigit() else (1, item),
    )


def sidra_raw_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    header = rows[0]
    data = rows[1:]
    dataframe = pd.DataFrame(data)
    dataframe.attrs["sidra_header"] = header
    return dataframe


def sidra_to_long(
    rows: list[dict[str, Any]],
    dataset: str,
    fonte: str,
    tema: str,
    periodicidade: str | None = None,
    table: str | None = None,
) -> pd.DataFrame:
    if not rows or len(rows) == 1:
        return pd.DataFrame()

    header = rows[0]
    records = []
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for row in rows[1:]:
        dimensions = extract_all_dimensions(header, row)
        period_code, period_name = find_period_dimension(dimensions)
        territory_code, territory_name = find_territory_dimension(dimensions)
        variable_code, variable_name = find_variable_dimension(dimensions)
        resolved_periodicity = periodicidade or infer_periodicity(
            period_code,
            period_name,
        )
        exercicio = extract_year(period_code, period_name)
        mes = extract_month(period_code, period_name, resolved_periodicity)
        trimestre = extract_quarter(
            period_code,
            period_name,
            resolved_periodicity,
        )

        record = {
            **dimensions,
            "fonte": fonte,
            "tema": tema,
            "dataset": dataset,
            "tabela_sidra": table,
            "codigo_serie": f"sidra_{dataset}",
            "periodicidade": resolved_periodicity,
            "periodo_codigo": period_code,
            "periodo_nome": period_name,
            "exercicio": exercicio,
            "mes": mes,
            "trimestre": trimestre,
            "territorio_nivel_codigo": row.get("NC"),
            "territorio_nivel_nome": row.get("NN"),
            "territorio_codigo": territory_code,
            "territorio_nome": territory_name,
            "variavel_codigo": variable_code,
            "variavel_nome": variable_name,
            "unidade_codigo": row.get("MC"),
            "unidade": row.get("MN"),
            "valor_original": row.get("V"),
            "valor": parse_number(row.get("V")),
            "coletado_em": collected_at,
            "extra_json": json.dumps(row, ensure_ascii=False),
        }
        records.append(record)

    dataframe = pd.DataFrame(records)

    preferred_columns = [
        "fonte",
        "tema",
        "dataset",
        "tabela_sidra",
        "codigo_serie",
        "periodicidade",
        "periodo_codigo",
        "periodo_nome",
        "exercicio",
        "mes",
        "trimestre",
        "territorio_nivel_codigo",
        "territorio_nivel_nome",
        "territorio_codigo",
        "territorio_nome",
        "variavel_codigo",
        "variavel_nome",
        "unidade_codigo",
        "unidade",
        "valor_original",
        "valor",
        "coletado_em",
        "extra_json",
    ]
    dimension_columns = sorted(
        column for column in dataframe.columns if column not in preferred_columns
    )

    ordered_columns = (
        preferred_columns[:-2] + dimension_columns + preferred_columns[-2:]
    )
    return dataframe[ordered_columns]


def extract_all_dimensions(
    header: dict[str, Any],
    row: dict[str, Any],
) -> dict[str, Any]:
    dimensions: dict[str, Any] = {}

    for key, label in header.items():
        if not str(key).startswith("D"):
            continue

        label_text = str(label)
        is_code = has_code_marker(label_text)
        base_label = remove_code_marker(label_text)
        slug = normalize_name(base_label)

        if not slug:
            slug = str(key).lower()

        suffix = "codigo" if is_code else "nome"
        column = f"{slug}_{suffix}"

        if column in dimensions:
            column = f"{column}_{str(key).lower()}"

        dimensions[column] = row.get(key)

    return dimensions


def find_period_dimension(
    dimensions: dict[str, Any],
) -> tuple[Any, Any]:
    return find_dimension_pair(
        dimensions,
        ["ano", "trimestre", "mes", "periodo"],
    )


def find_territory_dimension(
    dimensions: dict[str, Any],
) -> tuple[Any, Any]:
    return find_dimension_pair(
        dimensions,
        [
            "municipio",
            "unidade_da_federacao",
            "grande_regiao",
            "regiao_metropolitana",
            "brasil",
        ],
    )


def find_variable_dimension(
    dimensions: dict[str, Any],
) -> tuple[Any, Any]:
    return find_dimension_pair(dimensions, ["variavel"])


def find_dimension_pair(
    dimensions: dict[str, Any],
    terms: list[str],
) -> tuple[Any, Any]:
    for term in terms:
        code_column = next(
            (
                column
                for column in dimensions
                if term in column and column.endswith("_codigo")
            ),
            None,
        )
        name_column = next(
            (
                column
                for column in dimensions
                if term in column and column.endswith("_nome")
            ),
            None,
        )

        if code_column or name_column:
            return (
                dimensions.get(code_column) if code_column else None,
                dimensions.get(name_column) if name_column else None,
            )

    return None, None


def has_code_marker(label: str) -> bool:
    return "codigo" in normalize_text(label)


def remove_code_marker(label: str) -> str:
    return re.sub(
        r"\s*\((?:c[oó]digo|code)\)\s*",
        "",
        label,
        flags=re.IGNORECASE,
    ).strip()


def normalize_name(value: str) -> str:
    normalized = normalize_text(value)
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(
        character for character in text if not unicodedata.combining(character)
    )
    return text.lower().strip()


def extract_year(code: Any, name: Any) -> int | None:
    for value in [code, name]:
        match = re.search(r"(19|20)\d{2}", str(value or ""))
        if match:
            return int(match.group(0))
    return None


def extract_month(
    code: Any,
    name: Any,
    periodicity: str | None,
) -> int | None:
    if periodicity != "mensal":
        return None

    code_text = re.sub(r"\D", "", str(code or ""))
    if len(code_text) >= 6:
        month = int(code_text[-2:])
        if 1 <= month <= 12:
            return month

    normalized_name = normalize_text(name)
    for month_name, month_number in MONTH_NAMES.items():
        if month_name in normalized_name:
            return month_number

    numeric_match = re.search(
        r"(?:^|\D)(0?[1-9]|1[0-2])(?:\D|$)",
        str(name or ""),
    )
    if numeric_match:
        return int(numeric_match.group(1))

    return None


def extract_quarter(
    code: Any,
    name: Any,
    periodicity: str | None,
) -> int | None:
    if periodicity != "trimestral":
        return None

    name_match = re.search(
        r"([1-4])\s*[ºo]?\s*trimestre",
        normalize_text(name),
    )
    if name_match:
        return int(name_match.group(1))

    code_text = re.sub(r"\D", "", str(code or ""))
    if len(code_text) >= 5:
        quarter = int(code_text[-1])
        if 1 <= quarter <= 4:
            return quarter

    return None


def infer_periodicity(code: Any, name: Any) -> str | None:
    normalized_name = normalize_text(name)
    code_text = re.sub(r"\D", "", str(code or ""))

    if "trimestre" in normalized_name:
        return "trimestral"

    if any(month in normalized_name for month in MONTH_NAMES):
        return "mensal"

    if len(code_text) == 6 and code_text[-2:] in {
        f"{month:02d}" for month in range(1, 13)
    }:
        return "mensal"

    if re.fullmatch(r"(19|20)\d{2}", code_text):
        return "anual"

    return None


def parse_number(value: Any) -> float | None:
    if value in SPECIAL_VALUES:
        return None

    text = str(value).strip().replace("\u00a0", "")
    text = re.sub(r"[^0-9,\.\-+eE]", "", text)

    if not text:
        return None

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return None
