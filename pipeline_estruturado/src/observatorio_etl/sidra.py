import json
from datetime import datetime
from typing import Any
from urllib.parse import quote

import pandas as pd

from observatorio_etl.http_client import HttpClient


class SidraClient:
    def __init__(self, http_client: HttpClient | None = None):
        self.http_client = http_client or HttpClient()
        self.base_url = "https://apisidra.ibge.gov.br/values"

    def fetch_table(
        self,
        table: str,
        variable: str,
        period: str,
        territorial_level: str,
        localities: str,
        decimals: str = "0",
    ) -> list[dict[str, Any]]:
        path = f"/t/{table}/n{territorial_level}/{localities}/v/{variable}/p/{period}/d/v{variable}%20{quote(str(decimals))}"
        return self.http_client.get_json(f"{self.base_url}{path}")


def sidra_raw_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    header = rows[0]
    data = rows[1:]
    dataframe = pd.DataFrame(data)
    dataframe.attrs["sidra_header"] = header
    return dataframe


def sidra_to_long(rows: list[dict[str, Any]], dataset: str, fonte: str, tema: str) -> pd.DataFrame:
    if not rows or len(rows) == 1:
        return pd.DataFrame()

    header = rows[0]
    records = []
    collected_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    for row in rows[1:]:
        record = {
            "fonte": fonte,
            "tema": tema,
            "dataset": dataset,
            "codigo_serie": f"sidra_{dataset}",
            "periodo_codigo": extract_dimension_value(header, row, ["Ano", "Trimestre", "Mês", "Mês de referência", "Período"], code=True),
            "periodo_nome": extract_dimension_value(header, row, ["Ano", "Trimestre", "Mês", "Mês de referência", "Período"], code=False),
            "territorio_codigo": extract_dimension_value(header, row, ["Brasil", "Grande Região", "Unidade da Federação", "Município"], code=True),
            "territorio_nome": extract_dimension_value(header, row, ["Brasil", "Grande Região", "Unidade da Federação", "Município"], code=False),
            "variavel_codigo": extract_dimension_value(header, row, ["Variável"], code=True),
            "variavel_nome": extract_dimension_value(header, row, ["Variável"], code=False),
            "unidade": row.get("MN"),
            "valor": parse_number(row.get("V")),
            "coletado_em": collected_at,
            "extra_json": json.dumps(row, ensure_ascii=False),
        }
        records.append(record)

    return pd.DataFrame(records)


def extract_dimension_value(header: dict[str, str], row: dict[str, Any], terms: list[str], code: bool) -> Any:
    candidates = []
    for key, label in header.items():
        if key in {"NC", "NN", "MC", "MN", "V"}:
            continue
        if not any(term.lower() in str(label).lower() for term in terms):
            continue
        wants_code = "código" in str(label).lower() or "codigo" in str(label).lower()
        if wants_code == code:
            candidates.append(key)

    for key in candidates:
        value = row.get(key)
        if value not in {None, "", "...", "-"}:
            return value
    return None


def parse_number(value: Any) -> float | None:
    if value in {None, "", "...", "-"}:
        return None
    text = str(value).strip().replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None
