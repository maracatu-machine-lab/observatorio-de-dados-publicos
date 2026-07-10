import re
import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from orcamentobr import despesa_detalhada


ALLOWED_PARAMS = {
    "exercicio",
    "esfera",
    "orgao",
    "uo",
    "funcao",
    "sub_funcao",
    "programa",
    "acao",
    "plano_orcamentario",
    "subtitulo",
    "categoria_economica",
    "gnd",
    "modalidade_aplicacao",
    "elemento_despesa",
    "fonte",
    "id_uso",
    "resultado_primario",
    "valor_ploa",
    "valor_loa",
    "valor_loa_mais_credito",
    "valor_empenhado",
    "valor_liquidado",
    "valor_pago",
    "inclui_descricoes",
    "detalhe_maximo",
    "ignore_secure_certificate",
    "timeout",
    "print_url",
}

VALUE_ALIASES = {
    "ploa": "valor_ploa",
    "valor_ploa": "valor_ploa",
    "loa": "dotacao_inicial",
    "valor_loa": "dotacao_inicial",
    "loa_mais_credito": "dotacao_atualizada",
    "valor_loa_mais_credito": "dotacao_atualizada",
    "empenhado": "valor_empenhado",
    "valor_empenhado": "valor_empenhado",
    "liquidado": "valor_liquidado",
    "valor_liquidado": "valor_liquidado",
    "pago": "valor_pago",
    "valor_pago": "valor_pago",
}

METRIC_COLUMNS = [
    "valor_ploa",
    "dotacao_inicial",
    "dotacao_atualizada",
    "valor_empenhado",
    "valor_liquidado",
    "valor_pago",
]


class SiopClient:
    def fetch_expenses(
        self,
        params: dict[str, Any],
        max_attempts: int = 3,
    ) -> pd.DataFrame:
        invalid_params = sorted(set(params) - ALLOWED_PARAMS)

        if invalid_params:
            invalid_text = ", ".join(invalid_params)
            raise ValueError(f"Parâmetros do SIOP não reconhecidos: {invalid_text}")

        request_params = {
            key: value for key, value in params.items() if value is not None
        }

        exercicio = request_params.get("exercicio", "não informado")
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                result = despesa_detalhada(**request_params)

                if isinstance(result, pd.DataFrame):
                    return result

                return pd.DataFrame(result)
            except Exception as error:
                last_error = error

                if attempt < max_attempts:
                    time.sleep(attempt * 5)

        raise RuntimeError(
            "Falha ao consultar a execução orçamentária "
            f"do SIOP para o exercício {exercicio}: {last_error}"
        ) from last_error


def prepare_siop_dataframe(
    dataframe: pd.DataFrame,
    dataset: str,
    fonte: str,
    tema: str,
    exercicio: int,
) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame()

    result = dataframe.copy()
    result.columns = [normalize_column_name(column) for column in result.columns]
    result = result.rename(columns=VALUE_ALIASES)

    if "exercicio" not in result.columns:
        result["exercicio"] = exercicio
    else:
        result["exercicio"] = result["exercicio"].fillna(exercicio)

    result["exercicio"] = pd.to_numeric(
        result["exercicio"],
        errors="coerce",
    ).astype("Int64")

    for column in METRIC_COLUMNS:
        if column in result.columns:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    for required_column in [
        "valor_empenhado",
        "valor_liquidado",
        "valor_pago",
    ]:
        if required_column not in result.columns:
            result[required_column] = pd.NA

    result.insert(0, "dataset", dataset)
    result.insert(0, "tema", tema)
    result.insert(0, "fonte", fonte)

    result["coletado_em"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    preferred_columns = [
        "fonte",
        "tema",
        "dataset",
        "exercicio",
        "valor_empenhado",
        "valor_liquidado",
        "valor_pago",
        "coletado_em",
    ]

    remaining_columns = [
        column for column in result.columns if column not in preferred_columns
    ]

    return result[preferred_columns + remaining_columns]


def build_execucao_por_ano_table(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    required_columns = {
        "exercicio",
        "valor_empenhado",
        "valor_liquidado",
        "valor_pago",
    }

    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))
        raise ValueError(
            "Não foi possível gerar a tabela de execução por ano. "
            f"Colunas ausentes: {missing_text}"
        )

    result = dataframe[
        [
            "exercicio",
            "valor_empenhado",
            "valor_liquidado",
            "valor_pago",
        ]
    ].copy()

    for column in [
        "valor_empenhado",
        "valor_liquidado",
        "valor_pago",
    ]:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result = (
        result.groupby(
            "exercicio",
            as_index=False,
            dropna=False,
        )
        .agg(
            EMPENHADO=("valor_empenhado", "sum"),
            LIQUIDADO=("valor_liquidado", "sum"),
            PAGO=("valor_pago", "sum"),
        )
        .rename(columns={"exercicio": "ANO"})
        .sort_values("ANO")
        .reset_index(drop=True)
    )

    result["ANO"] = result["ANO"].astype("Int64")

    for column in [
        "EMPENHADO",
        "LIQUIDADO",
        "PAGO",
    ]:
        result[column] = result[column].round(2)

    return result[
        [
            "ANO",
            "EMPENHADO",
            "LIQUIDADO",
            "PAGO",
        ]
    ]


def normalize_column_name(column: Any) -> str:
    normalized = camel_to_snake(str(column))

    if normalized.endswith("_cod"):
        return f"{normalized[:-4]}_codigo"

    if normalized.endswith("_desc"):
        return f"{normalized[:-5]}_nome"

    return normalized


def camel_to_snake(value: str) -> str:
    first_pass = re.sub(
        r"(.)([A-Z][a-z]+)",
        r"\1_\2",
        value,
    )

    second_pass = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1_\2",
        first_pass,
    )

    return second_pass.replace("-", "_").replace(" ", "_").lower()
