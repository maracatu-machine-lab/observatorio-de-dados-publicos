import json
from datetime import datetime
from typing import Any
from urllib.parse import quote

import pandas as pd

from observatorio_etl.http_client import HttpClient


class IpeaDataClient:
    def __init__(self, http_client: HttpClient | None = None):
        self.http_client = http_client or HttpClient()
        self.base_url = "https://www.ipeadata.gov.br/api/odata4"

    def fetch_metadata(self, series_code: str) -> dict[str, Any] | list[dict[str, Any]]:
        encoded = quote(series_code, safe="")
        return self.http_client.get_json(f"{self.base_url}/Metadados('{encoded}')")

    def fetch_values(self, series_code: str) -> dict[str, Any] | list[dict[str, Any]]:
        encoded = quote(series_code, safe="")
        return self.http_client.get_json(f"{self.base_url}/Metadados('{encoded}')/Valores")


def ipea_values_to_dataframe(payload: Any) -> pd.DataFrame:
    return pd.DataFrame(as_records(payload))


def ipea_to_long(values_payload: Any, metadata_payload: Any, dataset: str, fonte: str, tema: str, series_code: str) -> pd.DataFrame:
    values = as_records(values_payload)
    metadata = as_single_record(metadata_payload)
    collected_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    records = []

    for row in values:
        records.append(
            {
                "fonte": fonte,
                "tema": tema,
                "dataset": dataset,
                "codigo_serie": series_code,
                "periodo_codigo": first_present(row, ["VALDATA", "VALDATAINICIO", "VALDATAFIM"]),
                "periodo_nome": first_present(row, ["VALDATA", "VALDATAINICIO", "VALDATAFIM"]),
                "territorio_codigo": first_present(row, ["TERCODIGO", "PAICODIGO", "NIVCODIGO"]),
                "territorio_nome": first_present(row, ["TERNOME", "PAINOME", "NIVNOME"]),
                "variavel_codigo": series_code,
                "variavel_nome": first_present(metadata, ["SERNOME", "SERNOMECOMPLETO", "SERCOMENTARIO", "SERCODIGO"]),
                "unidade": first_present(metadata, ["SERUNIDADE", "UNINOME"]),
                "valor": parse_number(first_present(row, ["VALVALOR", "VALVALORORIGINAL"])),
                "coletado_em": collected_at,
                "extra_json": json.dumps(row, ensure_ascii=False),
            }
        )

    return pd.DataFrame(records)


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
    ignored_keys = {"@odata.context", "@odata.count", "@odata.nextLink"}
    return any(key not in ignored_keys for key in data)


def first_present(data: Any, keys: list[str]) -> Any:
    if not isinstance(data, dict):
        return None

    for key in keys:
        value = data.get(key)
        if value not in {None, "", "...", "-"}:
            return value

    return None


def parse_number(value: Any) -> float | None:
    if value in {None, "", "...", "-"}:
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
