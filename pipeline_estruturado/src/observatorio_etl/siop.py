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

DIMENSION_PARAMS = {
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

GOLD_COLUMNS = [
    "fonte",
    "tema",
    "dataset",
    "exercicio",
    "valor_empenhado",
    "valor_liquidado",
    "valor_pago",
    "coletado_em",
]

PREVIDENCIA_FUNCAO_CODIGO = "09"
PREVIDENCIA_FUNCAO_DESCRICAO = "Previdência Social"
PREVIDENCIA_SUBFUNCOES = {
    "271": "Previdência Básica",
    "272": "Previdência do Regime Estatutário",
    "273": "Previdência Complementar",
    "274": "Previdência Especial",
}


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
            "Falha ao consultar a LOA detalhada do SIOP "
            f"para o exercício {exercicio}: {last_error}"
        ) from last_error


def validate_complete_loa_params(params: dict[str, Any]) -> None:
    disabled_dimensions = sorted(
        dimension for dimension in DIMENSION_PARAMS if params.get(dimension) is not True
    )

    if disabled_dimensions and params.get("detalhe_maximo") is not True:
        disabled_text = ", ".join(disabled_dimensions)
        raise ValueError(
            "A coleta completa da LOA exige todas as dimensões ou "
            f"detalhe_maximo=true. Dimensões desativadas: {disabled_text}"
        )

    required_metrics = [
        "valor_ploa",
        "valor_loa",
        "valor_loa_mais_credito",
        "valor_empenhado",
        "valor_liquidado",
        "valor_pago",
    ]

    disabled_metrics = [
        metric for metric in required_metrics if params.get(metric) is not True
    ]

    if disabled_metrics:
        disabled_text = ", ".join(disabled_metrics)
        raise ValueError(
            "A camada bronze completa exige todos os campos monetários. "
            f"Campos desativados: {disabled_text}"
        )

    if params.get("inclui_descricoes") is not True:
        raise ValueError("A camada bronze completa exige inclui_descricoes=true.")


def prepare_siop_dataframe(
    dataframe: pd.DataFrame,
    dataset: str,
    fonte: str,
    tema: str,
    exercicio: int,
    coletado_em: str | None = None,
) -> pd.DataFrame:
    if dataframe.empty:
        raise ValueError(f"O SIOP não retornou dados para o exercício {exercicio}.")

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
        if column not in result.columns:
            result[column] = pd.NA

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    timestamp = coletado_em or datetime.now(timezone.utc).isoformat(timespec="seconds")

    result.insert(0, "dataset", dataset)
    result.insert(0, "tema", tema)
    result.insert(0, "fonte", fonte)
    result["coletado_em"] = timestamp

    preferred_columns = [
        "fonte",
        "tema",
        "dataset",
        "exercicio",
    ]

    dimension_columns = sorted(
        column
        for column in result.columns
        if column.endswith("_codigo") or column.endswith("_nome")
    )

    preferred_columns.extend(dimension_columns)
    preferred_columns.extend(METRIC_COLUMNS)
    preferred_columns.append("coletado_em")

    remaining_columns = [
        column for column in result.columns if column not in preferred_columns
    ]

    return result[preferred_columns + remaining_columns]


def build_total_loa_row(
    dataframe: pd.DataFrame,
    fonte: str,
    exercicio: int,
    coletado_em: str,
) -> pd.DataFrame:
    return build_execution_row(
        dataframe=dataframe,
        fonte=fonte,
        tema="execucao_orcamentaria",
        dataset="siop_loa_total_por_ano",
        exercicio=exercicio,
        coletado_em=coletado_em,
    )


def build_previdencia_publica_row(
    dataframe: pd.DataFrame,
    fonte: str,
    exercicio: int,
    coletado_em: str,
) -> pd.DataFrame:
    previdencia = filter_previdencia_publica(dataframe)

    if previdencia.empty:
        raise ValueError(
            "Nenhuma linha da função 09 - Previdência Social foi encontrada "
            f"no exercício {exercicio}."
        )

    return build_execution_row(
        dataframe=previdencia,
        fonte=fonte,
        tema="previdencia_publica",
        dataset="siop_loa_previdencia_publica_por_ano",
        exercicio=exercicio,
        coletado_em=coletado_em,
    )


def build_execution_row(
    dataframe: pd.DataFrame,
    fonte: str,
    tema: str,
    dataset: str,
    exercicio: int,
    coletado_em: str,
) -> pd.DataFrame:
    required_columns = {
        "valor_empenhado",
        "valor_liquidado",
        "valor_pago",
    }

    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))
        raise ValueError(
            "Não foi possível gerar o resumo da execução. "
            f"Colunas ausentes: {missing_text}"
        )

    totals = {}

    for column in [
        "valor_empenhado",
        "valor_liquidado",
        "valor_pago",
    ]:
        numeric_values = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )
        totals[column] = numeric_values.sum(min_count=1)

    result = pd.DataFrame(
        [
            {
                "fonte": fonte,
                "tema": tema,
                "dataset": dataset,
                "exercicio": exercicio,
                "valor_empenhado": totals["valor_empenhado"],
                "valor_liquidado": totals["valor_liquidado"],
                "valor_pago": totals["valor_pago"],
                "coletado_em": coletado_em,
            }
        ]
    )

    result["exercicio"] = result["exercicio"].astype("Int64")

    for column in [
        "valor_empenhado",
        "valor_liquidado",
        "valor_pago",
    ]:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).round(2)

    return result[GOLD_COLUMNS]


def filter_previdencia_publica(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    function_column = find_function_code_column(dataframe)
    normalized_codes = normalize_budget_code(
        dataframe[function_column],
        width=2,
    )

    return dataframe.loc[normalized_codes.eq(PREVIDENCIA_FUNCAO_CODIGO)].copy()


def find_function_code_column(dataframe: pd.DataFrame) -> str:
    candidates = [
        "funcao_codigo",
        "funcao_cod",
        "cod_funcao",
        "codfuncao",
    ]

    for candidate in candidates:
        if candidate in dataframe.columns:
            return candidate

    raise ValueError(
        "A coluna do código da função não foi encontrada. "
        "A coleta da LOA precisa incluir a dimensão função."
    )


def normalize_budget_code(
    values: pd.Series,
    width: int,
) -> pd.Series:
    normalized = (
        values.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.extract(r"(\d+)", expand=False)
    )

    return normalized.str.zfill(width)


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
