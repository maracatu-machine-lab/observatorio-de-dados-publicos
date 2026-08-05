from typing import Any

import pandas as pd


COMPARISON_COLUMNS = [
    "exercicio",
    "ipea_arrecadacao_liquida",
    "ipea_beneficios_previdenciarios",
    "ipea_resultado_primario_oficial",
    "ipea_resultado_primario_calculado",
    "ipea_diferenca_resultado",
    "ipea_status_periodo",
    "siop_rgps_beneficios_nucleo_empenhado",
    "siop_rgps_beneficios_nucleo_liquidado",
    "siop_rgps_beneficios_nucleo_pago",
    "siop_rgps_compensacao_previdenciaria_empenhado",
    "siop_rgps_compensacao_previdenciaria_liquidado",
    "siop_rgps_compensacao_previdenciaria_pago",
    "siop_rgps_beneficios_com_compensacao_empenhado",
    "siop_rgps_beneficios_com_compensacao_liquidado",
    "siop_rgps_beneficios_com_compensacao_pago",
    "siop_rgps_ressarcimentos_extraordinarios_empenhado",
    "siop_rgps_ressarcimentos_extraordinarios_liquidado",
    "siop_rgps_ressarcimentos_extraordinarios_pago",
    "siop_rgps_beneficios_ampliados_empenhado",
    "siop_rgps_beneficios_ampliados_liquidado",
    "siop_rgps_beneficios_ampliados_pago",
    "siop_rpps_uniao_civis_aposentadorias_pensoes_pago",
    "siop_pensoes_militares_mapeadas_pago",
    "siop_encargos_previdenciarios_especiais_pago",
    "siop_funcao_09_pago",
    "siop_outros_funcao_09_pago",
    "diferenca_siop_rgps_nucleo_pago_menos_ipea",
    "cobertura_siop_rgps_nucleo_pago_percentual",
    "diferenca_siop_rgps_com_compensacao_pago_menos_ipea",
    "cobertura_siop_rgps_com_compensacao_pago_percentual",
    "diferenca_siop_rgps_ampliado_pago_menos_ipea",
    "cobertura_siop_rgps_ampliado_pago_percentual",
    "diferenca_siop_rgps_com_compensacao_liquidado_menos_ipea",
    "cobertura_siop_rgps_com_compensacao_liquidado_percentual",
    "diferenca_siop_rgps_com_compensacao_empenhado_menos_ipea",
    "cobertura_siop_rgps_com_compensacao_empenhado_percentual",
    "diferenca_funcao_09_pago_menos_ipea",
    "relacao_funcao_09_pago_sobre_ipea_percentual",
    "estagio_comparacao_principal",
    "escopo_siop_comparacao_principal",
    "status_comparabilidade",
    "observacao_metodologica",
]

CONSISTENCY_COLUMNS = [
    "exercicio",
    "indicador",
    "fonte_referencia",
    "fonte_comparada",
    "valor_referencia",
    "valor_comparado",
    "diferenca_absoluta",
    "divergencia_percentual",
    "limite_percentual",
    "alerta",
    "status_consistencia",
    "observacao",
]


CONSISTENCY_RULES = (
    {
        "indicador": "beneficios_previdenciarios_rgps",
        "fonte_referencia": "IPEAData",
        "fonte_comparada": "SIOP",
        "coluna_referencia": "ipea_beneficios_previdenciarios",
        "coluna_comparada": ("siop_rgps_beneficios_com_compensacao_pago"),
    },
)


def numeric_or_none(value: Any) -> float | None:
    """Converte um valor numérico e preserva ausências."""
    converted = pd.to_numeric(
        value,
        errors="coerce",
    )

    if pd.isna(converted):
        return None

    return float(converted)


def build_multisource_consistency(
    comparison: pd.DataFrame,
    threshold_percent: float = 10.0,
) -> pd.DataFrame:
    """
    Avalia a consistência entre fontes comparáveis.

    A divergência é calculada em relação à fonte de referência.
    O alerta não é gerado para períodos parciais, dados ausentes
    ou referência igual a zero.
    """
    if threshold_percent < 0:
        raise ValueError("O limite percentual não pode ser negativo.")

    if comparison.empty:
        return pd.DataFrame(columns=CONSISTENCY_COLUMNS)

    records: list[dict[str, Any]] = []

    for rule in CONSISTENCY_RULES:
        for _, row in comparison.iterrows():
            reference = numeric_or_none(row.get(rule["coluna_referencia"]))
            compared = numeric_or_none(row.get(rule["coluna_comparada"]))

            period_status = str(row.get("ipea_status_periodo", "")).strip().casefold()

            comparability_status = (
                str(row.get("status_comparabilidade", "")).strip().casefold()
            )

            difference = None
            divergence = None
            alert = False

            if reference is None or compared is None:
                status = "dados_insuficientes"
                observation = "Uma ou mais fontes não possuem valor para o exercício."

            elif (
                period_status != "completo" or comparability_status == "periodo_parcial"
            ):
                status = "nao_avaliado_periodo_parcial"
                observation = (
                    "O exercício possui período incompleto "
                    "ou datas de corte não comparáveis."
                )

            elif reference == 0:
                status = "nao_avaliado_referencia_zero"
                observation = (
                    "A divergência relativa não pode ser "
                    "calculada porque a referência é zero."
                )

            else:
                difference = compared - reference
                divergence = abs(difference) / abs(reference) * 100
                alert = divergence > threshold_percent

                if alert:
                    status = "alerta_divergencia"
                    observation = (
                        "Divergência superior ao limite definido para revisão."
                    )
                else:
                    status = "dentro_do_limite"
                    observation = "Divergência dentro do limite definido."

            records.append(
                {
                    "exercicio": row.get("exercicio"),
                    "indicador": rule["indicador"],
                    "fonte_referencia": (rule["fonte_referencia"]),
                    "fonte_comparada": (rule["fonte_comparada"]),
                    "valor_referencia": reference,
                    "valor_comparado": compared,
                    "diferenca_absoluta": (
                        round(difference, 2) if difference is not None else None
                    ),
                    "divergencia_percentual": (
                        round(divergence, 6) if divergence is not None else None
                    ),
                    "limite_percentual": (threshold_percent),
                    "alerta": alert,
                    "status_consistencia": status,
                    "observacao": observation,
                }
            )

    result = pd.DataFrame(
        records,
        columns=CONSISTENCY_COLUMNS,
    )

    result["exercicio"] = pd.to_numeric(
        result["exercicio"],
        errors="coerce",
    ).astype("Int64")

    return result.sort_values(
        [
            "indicador",
            "fonte_referencia",
            "fonte_comparada",
            "exercicio",
        ]
    ).reset_index(drop=True)


def build_previdencia_federal_comparison(
    ipea_annual: pd.DataFrame,
    siop_components: pd.DataFrame,
) -> pd.DataFrame:
    if siop_components.empty:
        return pd.DataFrame(columns=COMPARISON_COLUMNS)

    siop = prepare_siop_components(siop_components)
    ipea = prepare_ipea_annual(ipea_annual)

    result = siop.merge(
        ipea,
        on="exercicio",
        how="left",
    )

    result = calculate_comparison_fields(result)

    for column in COMPARISON_COLUMNS:
        if column not in result.columns:
            result[column] = pd.NA

    result["exercicio"] = pd.to_numeric(
        result["exercicio"],
        errors="coerce",
    ).astype("Int64")

    monetary_columns = [
        column
        for column in COMPARISON_COLUMNS
        if (
            column.startswith("ipea_")
            and column
            not in {
                "ipea_status_periodo",
            }
        )
        or column.startswith("siop_")
        or column.startswith("diferenca_")
    ]

    monetary_columns = [
        column for column in monetary_columns if not column.endswith("_percentual")
    ]

    for column in monetary_columns:
        if column not in result.columns:
            continue

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).round(2)

    percentage_columns = [
        column for column in COMPARISON_COLUMNS if column.endswith("_percentual")
    ]

    for column in percentage_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).round(6)

    return result[COMPARISON_COLUMNS].sort_values("exercicio").reset_index(drop=True)


def prepare_ipea_annual(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "exercicio",
        "ipea_arrecadacao_liquida",
        "ipea_beneficios_previdenciarios",
        "ipea_resultado_primario_oficial",
        "ipea_resultado_primario_calculado",
        "ipea_diferenca_resultado",
        "ipea_status_periodo",
    ]

    if dataframe.empty:
        return pd.DataFrame(columns=columns)

    prepared = dataframe.copy()

    rename_map = {
        "arrecadacao_liquida": ("ipea_arrecadacao_liquida"),
        "beneficios_previdenciarios": ("ipea_beneficios_previdenciarios"),
        "resultado_primario_oficial": ("ipea_resultado_primario_oficial"),
        "resultado_primario_calculado": ("ipea_resultado_primario_calculado"),
        "diferenca_resultado": ("ipea_diferenca_resultado"),
        "status_periodo": ("ipea_status_periodo"),
    }

    prepared = prepared.rename(columns=rename_map)

    for column in columns:
        if column not in prepared.columns:
            prepared[column] = pd.NA

    prepared["exercicio"] = pd.to_numeric(
        prepared["exercicio"],
        errors="coerce",
    ).astype("Int64")

    prepared = (
        prepared[columns]
        .dropna(subset=["exercicio"])
        .sort_values("exercicio")
        .drop_duplicates(
            subset=["exercicio"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    return prepared


def prepare_siop_components(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame()

    prepared = dataframe.copy()

    rename_map: dict[str, str] = {
        "funcao_09_valor_pago": ("siop_funcao_09_pago"),
        "outros_funcao_09_valor_pago": ("siop_outros_funcao_09_pago"),
        "rpps_uniao_civis_aposentadorias_pensoes_valor_pago": (
            "siop_rpps_uniao_civis_aposentadorias_pensoes_pago"
        ),
        "pensoes_militares_mapeadas_valor_pago": (
            "siop_pensoes_militares_mapeadas_pago"
        ),
        "encargos_previdenciarios_especiais_valor_pago": (
            "siop_encargos_previdenciarios_especiais_pago"
        ),
    }

    components = [
        (
            "rgps_beneficios_nucleo",
            "siop_rgps_beneficios_nucleo",
        ),
        (
            "rgps_compensacao_previdenciaria",
            "siop_rgps_compensacao_previdenciaria",
        ),
        (
            "rgps_beneficios_com_compensacao",
            "siop_rgps_beneficios_com_compensacao",
        ),
        (
            "rgps_ressarcimentos_extraordinarios",
            "siop_rgps_ressarcimentos_extraordinarios",
        ),
        (
            "rgps_beneficios_ampliados",
            "siop_rgps_beneficios_ampliados",
        ),
    ]

    for source_prefix, target_prefix in components:
        for stage in [
            "empenhado",
            "liquidado",
            "pago",
        ]:
            rename_map[f"{source_prefix}_valor_{stage}"] = f"{target_prefix}_{stage}"

    prepared = prepared.rename(columns=rename_map)

    prepared["exercicio"] = pd.to_numeric(
        prepared["exercicio"],
        errors="coerce",
    ).astype("Int64")

    return (
        prepared.dropna(subset=["exercicio"])
        .sort_values("exercicio")
        .drop_duplicates(
            subset=["exercicio"],
            keep="last",
        )
        .reset_index(drop=True)
    )


def calculate_comparison_fields(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    result = dataframe.copy()

    reference = pd.to_numeric(
        get_series(
            result,
            "ipea_beneficios_previdenciarios",
        ),
        errors="coerce",
    )

    comparisons = [
        (
            "siop_rgps_beneficios_nucleo_pago",
            "diferenca_siop_rgps_nucleo_pago_menos_ipea",
            "cobertura_siop_rgps_nucleo_pago_percentual",
        ),
        (
            "siop_rgps_beneficios_com_compensacao_pago",
            "diferenca_siop_rgps_com_compensacao_pago_menos_ipea",
            "cobertura_siop_rgps_com_compensacao_pago_percentual",
        ),
        (
            "siop_rgps_beneficios_ampliados_pago",
            "diferenca_siop_rgps_ampliado_pago_menos_ipea",
            "cobertura_siop_rgps_ampliado_pago_percentual",
        ),
        (
            "siop_rgps_beneficios_com_compensacao_liquidado",
            "diferenca_siop_rgps_com_compensacao_liquidado_menos_ipea",
            "cobertura_siop_rgps_com_compensacao_liquidado_percentual",
        ),
        (
            "siop_rgps_beneficios_com_compensacao_empenhado",
            "diferenca_siop_rgps_com_compensacao_empenhado_menos_ipea",
            "cobertura_siop_rgps_com_compensacao_empenhado_percentual",
        ),
        (
            "siop_funcao_09_pago",
            "diferenca_funcao_09_pago_menos_ipea",
            "relacao_funcao_09_pago_sobre_ipea_percentual",
        ),
    ]

    for (
        siop_column,
        difference_column,
        coverage_column,
    ) in comparisons:
        siop_values = pd.to_numeric(
            get_series(
                result,
                siop_column,
            ),
            errors="coerce",
        )
        result[difference_column] = siop_values - reference
        result[coverage_column] = (
            siop_values
            / reference.replace(
                0,
                pd.NA,
            )
            * 100
        )

    result["estagio_comparacao_principal"] = "valor_pago"
    result["escopo_siop_comparacao_principal"] = (
        "beneficios_rgps_nucleo_mais_compensacao"
    )
    result["status_comparabilidade"] = result.apply(
        classify_comparability,
        axis=1,
    )
    result["observacao_metodologica"] = result.apply(
        build_methodological_note,
        axis=1,
    )

    return result


def classify_comparability(
    row: pd.Series,
) -> str:
    ipea_value = row.get("ipea_beneficios_previdenciarios")
    siop_value = row.get("siop_rgps_beneficios_com_compensacao_pago")
    ipea_status = (
        str(
            row.get(
                "ipea_status_periodo",
                "",
            )
        )
        .strip()
        .casefold()
    )

    if (
        ipea_value is None
        or siop_value is None
        or pd.isna(ipea_value)
        or pd.isna(siop_value)
    ):
        return "dados_insuficientes"

    if ipea_status == "parcial":
        return "periodo_parcial"

    return "parcialmente_comparavel"


def build_methodological_note(
    row: pd.Series,
) -> str:
    status = row.get("status_comparabilidade")

    if status == "dados_insuficientes":
        return "Uma ou mais fontes não possuem valor para o exercício."

    if status == "periodo_parcial":
        return (
            "O IPEAData possui menos de doze meses "
            "no exercício. O SIOP é anual e pode ter "
            "data de corte diferente, portanto a "
            "diferença não deve ser interpretada "
            "como divergência contábil."
        )

    return (
        "Comparação parcial entre o fluxo de caixa "
        "do RGPS no IPEAData e a execução "
        "orçamentária federal do SIOP. O IPEAData "
        "inclui benefícios urbanos e rurais, "
        "sentenças judiciais, compensação "
        "previdenciária e ajustes de agentes "
        "pagadores. O SIOP pode não refletir esses "
        "componentes no mesmo estágio ou exercício, "
        "inclusive por efeitos de restos a pagar."
    )


def get_series(
    dataframe: pd.DataFrame,
    column: str,
) -> pd.Series:
    if column in dataframe.columns:
        return dataframe[column]

    return pd.Series(
        pd.NA,
        index=dataframe.index,
        dtype="object",
    )
