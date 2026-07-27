import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import pandas as pd

from observatorio_etl.http_client import HttpClient


class IpeaDataClient:
    def __init__(self, http_client: HttpClient | None = None):
        self.http_client = http_client or HttpClient()
        self.base_url = "https://www.ipeadata.gov.br/api/odata4"

    def fetch_metadata(
        self,
        series_code: str,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        encoded = quote(series_code, safe="")
        return self.http_client.get_json(f"{self.base_url}/Metadados('{encoded}')")

    def fetch_values(
        self,
        series_code: str,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        encoded = quote(series_code, safe="")
        return self.http_client.get_json(
            f"{self.base_url}/Metadados('{encoded}')/Valores"
        )


def ipea_values_to_dataframe(payload: Any) -> pd.DataFrame:
    return pd.DataFrame(as_records(payload))


def ipea_to_long(
    values_payload: Any,
    metadata_payload: Any,
    dataset: str,
    fonte: str,
    tema: str,
    series_code: str,
) -> pd.DataFrame:
    values = as_records(values_payload)
    metadata = as_single_record(metadata_payload)
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    periodicity = normalize_periodicity(
        first_present(
            metadata,
            [
                "PERNOME",
                "SERPERIODICIDADE",
                "PERIODICIDADE",
            ],
        )
    )
    variable_name = first_present(
        metadata,
        [
            "SERNOME",
            "SERNOMECOMPLETO",
            "SERCOMENTARIO",
            "SERCODIGO",
        ],
    )
    unit_code = first_present(
        metadata,
        [
            "UNICODIGO",
            "UNNCODIGO",
            "UNIDADE_CODIGO",
        ],
    )
    unit = first_present(
        metadata,
        [
            "SERUNIDADE",
            "UNINOME",
        ],
    )
    metadata_territory_code = first_present(
        metadata,
        [
            "TERCODIGO",
            "PAICODIGO",
            "NIVCODIGO",
        ],
    )
    metadata_territory_name = first_present(
        metadata,
        [
            "TERNOME",
            "PAINOME",
            "NIVNOME",
        ],
    )
    records = []

    for row in values:
        period_value = first_present(
            row,
            [
                "VALDATA",
                "VALDATAINICIO",
                "VALDATAFIM",
            ],
        )
        year, month, quarter = parse_period_parts(period_value)
        original_value = first_present(
            row,
            [
                "VALVALOR",
                "VALVALORORIGINAL",
            ],
        )

        records.append(
            {
                "fonte": fonte,
                "tema": tema,
                "dataset": dataset,
                "codigo_serie": series_code,
                "periodicidade": periodicity,
                "periodo_codigo": period_value,
                "periodo_nome": period_value,
                "exercicio": year,
                "mes": month,
                "trimestre": quarter,
                "territorio_codigo": first_present(
                    row,
                    [
                        "TERCODIGO",
                        "PAICODIGO",
                        "NIVCODIGO",
                    ],
                )
                or metadata_territory_code,
                "territorio_nome": first_present(
                    row,
                    [
                        "TERNOME",
                        "PAINOME",
                        "NIVNOME",
                    ],
                )
                or metadata_territory_name,
                "variavel_codigo": series_code,
                "variavel_nome": variable_name,
                "unidade_codigo": unit_code,
                "unidade": unit,
                "valor_original": original_value,
                "valor": parse_number(original_value),
                "coletado_em": collected_at,
                "extra_json": json.dumps(
                    row,
                    ensure_ascii=False,
                ),
            }
        )

    columns = [
        "fonte",
        "tema",
        "dataset",
        "codigo_serie",
        "periodicidade",
        "periodo_codigo",
        "periodo_nome",
        "exercicio",
        "mes",
        "trimestre",
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

    return pd.DataFrame(
        records,
        columns=columns,
    )


def as_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        value = payload.get("value")

        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

        if isinstance(value, dict):
            return [value]

        if looks_like_record(payload):
            return [payload]

        return []

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    return []


def as_single_record(payload: Any) -> dict[str, Any]:
    records = as_records(payload)

    if records:
        return records[0]

    return {}


def looks_like_record(data: dict[str, Any]) -> bool:
    ignored_keys = {
        "@odata.context",
        "@odata.count",
        "@odata.nextLink",
    }
    return any(key not in ignored_keys for key in data)


def first_present(
    data: Any,
    keys: list[str],
) -> Any:
    if not isinstance(data, dict):
        return None

    for key in keys:
        value = data.get(key)

        if value not in {
            None,
            "",
            "...",
            "-",
        }:
            return value

    return None


def parse_period_parts(
    value: Any,
) -> tuple[int | None, int | None, int | None]:
    if value in {
        None,
        "",
        "...",
        "-",
    }:
        return None, None, None

    timestamp = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(timestamp):
        return None, None, None

    year = int(timestamp.year)
    month = int(timestamp.month)
    quarter = (month - 1) // 3 + 1

    return year, month, quarter


def normalize_periodicity(value: Any) -> str | None:
    if value in {
        None,
        "",
        "...",
        "-",
    }:
        return None

    text = str(value).strip().casefold()

    return text or None


def parse_number(value: Any) -> float | None:
    if value in {
        None,
        "",
        "...",
        "-",
    }:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return None
