from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd

from observatorio_etl.http_client import HttpClient
from observatorio_etl.ipeadata import as_records


CATALOG_URL = "https://www.ipeadata.gov.br/api/odata4/Metadados"
OUTPUT_DIR = Path("outputs")
OUTPUT_FILE = OUTPUT_DIR / "ipeadata_series_previdencia_candidatas.csv"
SUMMARY_FILE = OUTPUT_DIR / "ipeadata_series_previdencia_resumo.csv"

SEARCH_GROUPS: dict[str, tuple[str, ...]] = {
    "arrecadacao_rgps": (
        "arrecadacao liquida",
        "arrecadacao do rgps",
        "arrecadacao previdenciaria",
        "receita previdenciaria",
        "receitas previdenciarias",
        "contribuicoes previdenciarias",
        "regime geral de previdencia social",
        "rgps",
    ),
    "despesa_beneficios_rgps": (
        "despesa com beneficios",
        "despesas com beneficios",
        "beneficios previdenciarios",
        "beneficios emitidos",
        "beneficios pagos",
        "pagamento de beneficios",
        "valor dos beneficios previdenciarios",
    ),
    "resultado_previdenciario": (
        "resultado previdenciario",
        "resultado do rgps",
        "saldo previdenciario",
        "deficit previdenciario",
        "superavit previdenciario",
        "necessidade de financiamento",
    ),
    "aposentadorias": (
        "aposentadoria",
        "aposentadorias",
        "aposentado",
        "aposentados",
    ),
    "pensoes": (
        "pensao",
        "pensoes",
        "pensionista",
        "pensionistas",
    ),
    "auxilios_previdenciarios": (
        "auxilio-doenca",
        "auxilio doenca",
        "auxilio por incapacidade",
        "auxilio-acidente",
        "auxilio acidente",
        "auxilio-reclusao",
        "auxilio reclusao",
        "salario-maternidade",
        "salario maternidade",
        "salario-familia",
        "salario familia",
    ),
    "rpps_uniao": (
        "rpps",
        "regime proprio",
        "regime estatutario",
        "previdencia dos servidores",
        "servidor publico federal",
        "servidores publicos federais",
        "aposentadorias e pensoes civis da uniao",
    ),
}

SEARCH_COLUMNS = (
    "SERCODIGO",
    "SERNOME",
    "SERNOMECOMPLETO",
    "SERCOMENTARIO",
    "FNTNOME",
    "FNTSIGLA",
    "UNINOME",
    "PERNOME",
    "MULNOME",
)

OUTPUT_COLUMNS = (
    "grupo_pesquisa",
    "termos_encontrados",
    "pontuacao",
    "SERCODIGO",
    "SERNOME",
    "SERNOMECOMPLETO",
    "PERNOME",
    "UNINOME",
    "MULNOME",
    "FNTSIGLA",
    "FNTNOME",
    "SERSTATUS",
    "SERATUALIZACAO",
    "PAICODIGO",
    "TEMCODIGO",
    "SERCOMENTARIO",
)


def normalize_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""

    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(
        character for character in text if not unicodedata.combining(character)
    )
    return " ".join(text.casefold().split())


def fetch_catalog(http_client: HttpClient) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    next_url: str | None = CATALOG_URL
    visited_urls: set[str] = set()

    while next_url:
        if next_url in visited_urls:
            raise RuntimeError(
                "A API retornou um link de paginação repetido. "
                "A coleta foi interrompida para evitar um ciclo infinito."
            )

        visited_urls.add(next_url)
        payload = http_client.get_json(next_url)
        records.extend(as_records(payload))

        if not isinstance(payload, dict):
            break

        next_link = payload.get("@odata.nextLink")
        if not next_link:
            break

        next_url = urljoin(CATALOG_URL, str(next_link))

    return records


def build_search_text(dataframe: pd.DataFrame) -> pd.Series:
    available_columns = [
        column for column in SEARCH_COLUMNS if column in dataframe.columns
    ]

    if not available_columns:
        raise RuntimeError(
            "O catálogo não contém nenhuma das colunas esperadas para pesquisa."
        )

    return (
        dataframe[available_columns]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .map(normalize_text)
    )


def score_match(text: str, normalized_terms: tuple[str, ...]) -> tuple[int, list[str]]:
    matched_terms = [term for term in normalized_terms if term in text]

    if not matched_terms:
        return 0, []

    score = sum(3 if " " in term else 1 for term in matched_terms)
    return score, matched_terms


def build_candidates(catalog: pd.DataFrame) -> pd.DataFrame:
    catalog = catalog.copy()
    catalog["_texto_busca"] = build_search_text(catalog)
    candidate_frames: list[pd.DataFrame] = []

    for group, terms in SEARCH_GROUPS.items():
        normalized_terms = tuple(normalize_text(term) for term in terms)
        scores = catalog["_texto_busca"].map(
            lambda text: score_match(text, normalized_terms)
        )
        mask = scores.map(lambda item: item[0] > 0)

        if not mask.any():
            continue

        group_frame = catalog.loc[mask].copy()
        group_scores = scores.loc[mask]
        group_frame.insert(0, "grupo_pesquisa", group)
        group_frame.insert(
            1,
            "termos_encontrados",
            group_scores.map(lambda item: " | ".join(item[1])),
        )
        group_frame.insert(
            2,
            "pontuacao",
            group_scores.map(lambda item: item[0]),
        )
        candidate_frames.append(group_frame)

    if not candidate_frames:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    result = pd.concat(candidate_frames, ignore_index=True)

    if "SERCODIGO" in result.columns:
        result = result.drop_duplicates(
            subset=["grupo_pesquisa", "SERCODIGO"],
            keep="first",
        )

    for column in OUTPUT_COLUMNS:
        if column not in result.columns:
            result[column] = pd.NA

    result = result[list(OUTPUT_COLUMNS)].sort_values(
        ["grupo_pesquisa", "pontuacao", "SERNOME", "SERCODIGO"],
        ascending=[True, False, True, True],
        na_position="last",
    )

    return result.reset_index(drop=True)


def build_summary(candidates: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for group in SEARCH_GROUPS:
        group_frame = candidates.loc[candidates["grupo_pesquisa"].eq(group)]
        rows.append(
            {
                "grupo_pesquisa": group,
                "series_candidatas": len(group_frame),
                "series_com_codigo": int(group_frame["SERCODIGO"].notna().sum()),
                "series_com_periodicidade": int(group_frame["PERNOME"].notna().sum()),
                "series_com_unidade": int(group_frame["UNINOME"].notna().sum()),
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    http_client = HttpClient()
    records = fetch_catalog(http_client)

    if not records:
        raise RuntimeError("O catálogo de metadados do IPEAData retornou vazio.")

    catalog = pd.DataFrame(records)
    candidates = build_candidates(catalog)
    summary = build_summary(candidates)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    summary.to_csv(SUMMARY_FILE, index=False, encoding="utf-8")

    print(f"Metadados consultados: {len(catalog):,}")
    print(f"Séries candidatas: {len(candidates):,}")
    print("\nResumo por grupo:")
    print(summary.to_string(index=False))

    display_columns = [
        "grupo_pesquisa",
        "SERCODIGO",
        "SERNOME",
        "PERNOME",
        "UNINOME",
        "FNTSIGLA",
        "SERSTATUS",
    ]
    available_display_columns = [
        column for column in display_columns if column in candidates.columns
    ]

    if not candidates.empty:
        print("\nPrimeiras séries candidatas:")
        print(
            candidates[available_display_columns]
            .groupby("grupo_pesquisa", group_keys=False)
            .head(10)
            .to_string(index=False)
        )

    print("\nArquivos gerados:")
    print(OUTPUT_FILE)
    print(SUMMARY_FILE)


if __name__ == "__main__":
    main()
