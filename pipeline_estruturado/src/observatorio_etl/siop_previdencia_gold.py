from typing import Any

import pandas as pd

from observatorio_etl.siop import (
    filter_previdencia_publica,
    normalize_budget_code,
)


EXECUTION_COLUMNS = [
    "valor_empenhado",
    "valor_liquidado",
    "valor_pago",
]

SUBFUNCTION_COLUMNS = [
    "exercicio",
    "subfuncao_codigo",
    "subfuncao_nome",
    "valor_empenhado",
    "valor_liquidado",
    "valor_pago",
]

ACTION_COLUMNS = [
    "exercicio",
    "orgao_codigo",
    "orgao_nome",
    "uo_codigo",
    "uo_nome",
    "subfuncao_codigo",
    "subfuncao_nome",
    "programa_codigo",
    "programa_nome",
    "acao_codigo",
    "acao_nome",
    "valor_empenhado",
    "valor_liquidado",
    "valor_pago",
]

VALIDATION_COLUMNS = [
    "exercicio",
    "funcao_09_valor_empenhado",
    "subfuncoes_valor_empenhado",
    "acoes_valor_empenhado",
    "diferenca_subfuncoes_empenhado",
    "diferenca_acoes_empenhado",
    "funcao_09_valor_liquidado",
    "subfuncoes_valor_liquidado",
    "acoes_valor_liquidado",
    "diferenca_subfuncoes_liquidado",
    "diferenca_acoes_liquidado",
    "funcao_09_valor_pago",
    "subfuncoes_valor_pago",
    "acoes_valor_pago",
    "diferenca_subfuncoes_pago",
    "diferenca_acoes_pago",
    "status_validacao",
]

RGPS_CORE_2015_2021 = {
    "0E81",
    "0E82",
}
RGPS_CORE_2022_ONWARDS = {
    "00SJ",
}
RGPS_COMPENSATION_CODES = {
    "009W",
}
RGPS_EXTRAORDINARY_REFUND_CODES = {
    "00XK",
}
RPPS_CIVIL_MAIN_CODES = {
    "0181",
}
MILITARY_PENSION_CODES = {
    "0179",
}
SPECIAL_PENSION_OBLIGATION_CODES = {
    "0053",
    "0054",
    "0055",
    "00Q2",
    "00QD",
    "00QN",
    "009K",
    "0397",
    "0536",
    "0739",
    "0C01",
}
RPPS_EMPLOYER_CONTRIBUTION_CODES = {
    "09HB",
}


def build_siop_previdencia_gold_outputs(
    frames: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    prepared_frames: list[pd.DataFrame] = []

    for frame in frames.values():
        if frame.empty:
            continue

        prepared_frames.append(prepare_siop_previdencia_frame(frame))

    if not prepared_frames:
        return {}

    previdencia = pd.concat(
        prepared_frames,
        ignore_index=True,
    )

    by_subfunction = build_previdencia_by_subfunction(previdencia)
    by_action = build_previdencia_by_action(previdencia)
    components = build_previdencia_components(previdencia)
    validation = build_previdencia_validation(
        previdencia=previdencia,
        by_subfunction=by_subfunction,
        by_action=by_action,
    )

    return {
        "previdencia_federal_por_subfuncao_ano": (by_subfunction),
        "previdencia_federal_por_acao_ano": (by_action),
        "previdencia_federal_componentes_por_ano": (components),
        "previdencia_federal_validacao_por_ano": (validation),
    }


def prepare_siop_previdencia_frame(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    previdencia = filter_previdencia_publica(dataframe).copy()

    if previdencia.empty:
        return previdencia

    required_dimensions = [
        "exercicio",
        "orgao_codigo",
        "orgao_nome",
        "uo_codigo",
        "uo_nome",
        "subfuncao_codigo",
        "subfuncao_nome",
        "programa_codigo",
        "programa_nome",
        "acao_codigo",
        "acao_nome",
    ]

    for column in required_dimensions:
        if column not in previdencia.columns:
            previdencia[column] = pd.NA

    previdencia["exercicio"] = pd.to_numeric(
        previdencia["exercicio"],
        errors="coerce",
    ).astype("Int64")

    code_widths = {
        "orgao_codigo": 5,
        "uo_codigo": 5,
        "subfuncao_codigo": 3,
        "programa_codigo": 4,
    }

    for column, width in code_widths.items():
        previdencia[column] = normalize_budget_code(
            previdencia[column],
            width=width,
        )

    previdencia["acao_codigo"] = normalize_action_code(
        previdencia["acao_codigo"],
    )

    for column in EXECUTION_COLUMNS:
        if column not in previdencia.columns:
            previdencia[column] = pd.NA

        previdencia[column] = pd.to_numeric(
            previdencia[column],
            errors="coerce",
        )

    return previdencia


def build_previdencia_by_subfunction(
    previdencia: pd.DataFrame,
) -> pd.DataFrame:
    if previdencia.empty:
        return pd.DataFrame(columns=SUBFUNCTION_COLUMNS)

    group_columns = [
        "exercicio",
        "subfuncao_codigo",
        "subfuncao_nome",
    ]

    result = aggregate_execution(
        dataframe=previdencia,
        group_columns=group_columns,
    )

    result["exercicio"] = pd.to_numeric(
        result["exercicio"],
        errors="coerce",
    ).astype("Int64")

    return (
        result[SUBFUNCTION_COLUMNS]
        .sort_values(
            [
                "exercicio",
                "subfuncao_codigo",
                "subfuncao_nome",
            ],
            na_position="last",
        )
        .reset_index(drop=True)
    )


def build_previdencia_by_action(
    previdencia: pd.DataFrame,
) -> pd.DataFrame:
    if previdencia.empty:
        return pd.DataFrame(columns=ACTION_COLUMNS)

    group_columns = [
        "exercicio",
        "orgao_codigo",
        "orgao_nome",
        "uo_codigo",
        "uo_nome",
        "subfuncao_codigo",
        "subfuncao_nome",
        "programa_codigo",
        "programa_nome",
        "acao_codigo",
        "acao_nome",
    ]

    result = aggregate_execution(
        dataframe=previdencia,
        group_columns=group_columns,
    )

    result["exercicio"] = pd.to_numeric(
        result["exercicio"],
        errors="coerce",
    ).astype("Int64")

    return (
        result[ACTION_COLUMNS]
        .sort_values(
            [
                "exercicio",
                "subfuncao_codigo",
                "programa_codigo",
                "acao_codigo",
                "orgao_codigo",
                "uo_codigo",
            ],
            na_position="last",
        )
        .reset_index(drop=True)
    )


def build_previdencia_components(
    previdencia: pd.DataFrame,
) -> pd.DataFrame:
    if previdencia.empty:
        return pd.DataFrame()

    years = sorted(
        int(year) for year in (previdencia["exercicio"].dropna().unique().tolist())
    )
    records: list[dict[str, Any]] = []

    for year in years:
        year_frame = previdencia.loc[previdencia["exercicio"].eq(year)].copy()

        if year <= 2021:
            rgps_core_codes = RGPS_CORE_2015_2021
            rgps_rule = "0E81+0E82"
            rgps_mapping_status = "mapeado_urbano_rural"
        else:
            rgps_core_codes = RGPS_CORE_2022_ONWARDS
            rgps_rule = "00SJ"
            rgps_mapping_status = "mapeado_acao_unificada"

        record: dict[str, Any] = {
            "exercicio": year,
            "regra_rgps_beneficios_nucleo": (rgps_rule),
            "status_mapeamento_rgps": (rgps_mapping_status),
        }

        for metric in EXECUTION_COLUMNS:
            suffix = metric.removeprefix("valor_")

            function_total = sum_with_min_count(year_frame[metric])
            rgps_core = sum_action_codes(
                dataframe=year_frame,
                action_codes=rgps_core_codes,
                metric=metric,
            )
            rgps_compensation = sum_action_codes(
                dataframe=year_frame,
                action_codes=(RGPS_COMPENSATION_CODES),
                metric=metric,
            )
            rgps_extraordinary_refund = sum_action_codes(
                dataframe=year_frame,
                action_codes=(RGPS_EXTRAORDINARY_REFUND_CODES),
                metric=metric,
            )
            rpps_civil = sum_action_codes(
                dataframe=year_frame,
                action_codes=(RPPS_CIVIL_MAIN_CODES),
                metric=metric,
            )
            military_pensions = sum_action_codes(
                dataframe=year_frame,
                action_codes=(MILITARY_PENSION_CODES),
                metric=metric,
            )
            special_obligations = sum_action_codes(
                dataframe=year_frame,
                action_codes=(SPECIAL_PENSION_OBLIGATION_CODES),
                metric=metric,
            )
            rpps_employer_contribution = sum_action_codes(
                dataframe=year_frame,
                action_codes=(RPPS_EMPLOYER_CONTRIBUTION_CODES),
                metric=metric,
            )

            rgps_core_plus_compensation = rgps_core + rgps_compensation
            rgps_broad = rgps_core_plus_compensation + rgps_extraordinary_refund
            mapped_benefit_components = (
                rgps_broad + rpps_civil + military_pensions + special_obligations
            )
            mapped_total = mapped_benefit_components + rpps_employer_contribution

            if function_total is None:
                residual = None
            else:
                residual = function_total - mapped_total

            record[f"funcao_09_{metric}"] = function_total
            record[f"rgps_beneficios_nucleo_{metric}"] = rgps_core
            record[f"rgps_compensacao_previdenciaria_{metric}"] = rgps_compensation
            record[f"rgps_beneficios_com_compensacao_{metric}"] = (
                rgps_core_plus_compensation
            )
            record[f"rgps_ressarcimentos_extraordinarios_{metric}"] = (
                rgps_extraordinary_refund
            )
            record[f"rgps_beneficios_ampliados_{metric}"] = rgps_broad
            record[f"rpps_uniao_civis_aposentadorias_pensoes_{metric}"] = rpps_civil
            record[f"pensoes_militares_mapeadas_{metric}"] = military_pensions
            record[f"encargos_previdenciarios_especiais_{metric}"] = special_obligations
            record[f"contribuicao_patronal_rpps_uniao_{metric}"] = (
                rpps_employer_contribution
            )
            record[f"componentes_beneficios_mapeados_{metric}"] = (
                mapped_benefit_components
            )
            record[f"componentes_totais_mapeados_{metric}"] = mapped_total
            record[f"outros_funcao_09_{metric}"] = residual

            record[f"percentual_rgps_nucleo_sobre_funcao_09_{suffix}"] = (
                calculate_percentage(
                    numerator=rgps_core,
                    denominator=function_total,
                )
            )
            record[f"percentual_componentes_mapeados_sobre_funcao_09_{suffix}"] = (
                calculate_percentage(
                    numerator=mapped_total,
                    denominator=function_total,
                )
            )

        records.append(record)

    result = pd.DataFrame(records)

    result["exercicio"] = pd.to_numeric(
        result["exercicio"],
        errors="coerce",
    ).astype("Int64")

    monetary_columns = [
        column
        for column in result.columns
        if ("_valor_" in column or column.startswith("funcao_09_valor_"))
    ]

    for column in monetary_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).round(2)

    percentage_columns = [
        column for column in result.columns if column.startswith("percentual_")
    ]

    for column in percentage_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).round(6)

    return result.sort_values("exercicio").reset_index(drop=True)


def build_previdencia_validation(
    previdencia: pd.DataFrame,
    by_subfunction: pd.DataFrame,
    by_action: pd.DataFrame,
) -> pd.DataFrame:
    if previdencia.empty:
        return pd.DataFrame(columns=VALIDATION_COLUMNS)

    years = sorted(
        int(year) for year in (previdencia["exercicio"].dropna().unique().tolist())
    )
    records: list[dict[str, Any]] = []

    for year in years:
        function_frame = previdencia.loc[previdencia["exercicio"].eq(year)]
        subfunction_frame = by_subfunction.loc[by_subfunction["exercicio"].eq(year)]
        action_frame = by_action.loc[by_action["exercicio"].eq(year)]

        record: dict[str, Any] = {
            "exercicio": year,
        }
        differences: list[float] = []

        for metric in EXECUTION_COLUMNS:
            short_name = metric.removeprefix("valor_")
            function_total = sum_with_min_count(function_frame[metric])
            subfunction_total = sum_with_min_count(subfunction_frame[metric])
            action_total = sum_with_min_count(action_frame[metric])

            subfunction_difference = calculate_difference(
                left=function_total,
                right=subfunction_total,
            )
            action_difference = calculate_difference(
                left=function_total,
                right=action_total,
            )

            record[f"funcao_09_{metric}"] = function_total
            record[f"subfuncoes_{metric}"] = subfunction_total
            record[f"acoes_{metric}"] = action_total
            record[f"diferenca_subfuncoes_{short_name}"] = subfunction_difference
            record[f"diferenca_acoes_{short_name}"] = action_difference

            for difference in [
                subfunction_difference,
                action_difference,
            ]:
                if difference is not None:
                    differences.append(abs(difference))

        if not differences:
            status = "dados_insuficientes"
        elif max(differences) <= 0.01:
            status = "validado"
        else:
            status = "divergencia"

        record["status_validacao"] = status
        records.append(record)

    result = pd.DataFrame(
        records,
        columns=VALIDATION_COLUMNS,
    )
    result["exercicio"] = pd.to_numeric(
        result["exercicio"],
        errors="coerce",
    ).astype("Int64")

    monetary_columns = [
        column
        for column in result.columns
        if column
        not in {
            "exercicio",
            "status_validacao",
        }
    ]

    for column in monetary_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).round(2)

    return result.sort_values("exercicio").reset_index(drop=True)


def aggregate_execution(
    dataframe: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    result = dataframe.groupby(
        group_columns,
        dropna=False,
        as_index=False,
    )[EXECUTION_COLUMNS].sum(min_count=1)

    for column in EXECUTION_COLUMNS:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).round(2)

    return result


def normalize_action_code(
    values: pd.Series,
) -> pd.Series:
    normalized = (
        values.astype("string")
        .str.strip()
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
        .str.upper()
    )

    numeric_mask = normalized.str.fullmatch(
        r"\d+",
        na=False,
    )
    normalized.loc[numeric_mask] = normalized.loc[numeric_mask].str.zfill(4)

    return normalized


def sum_action_codes(
    dataframe: pd.DataFrame,
    action_codes: set[str],
    metric: str,
) -> float:
    selected = dataframe.loc[
        dataframe["acao_codigo"].isin(action_codes),
        metric,
    ]

    if selected.empty:
        return 0.0

    numeric = pd.to_numeric(
        selected,
        errors="coerce",
    )
    total = numeric.sum(min_count=1)

    if pd.isna(total):
        return 0.0

    return float(total)


def sum_with_min_count(
    series: pd.Series,
) -> float | None:
    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )
    total = numeric.sum(min_count=1)

    if pd.isna(total):
        return None

    return float(total)


def calculate_difference(
    left: float | None,
    right: float | None,
) -> float | None:
    if left is None or right is None:
        return None

    return float(left - right)


def calculate_percentage(
    numerator: float | None,
    denominator: float | None,
) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None

    return float(numerator) / float(denominator) * 100
