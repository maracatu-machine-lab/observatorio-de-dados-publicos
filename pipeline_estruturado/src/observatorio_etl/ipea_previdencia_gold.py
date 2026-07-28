from typing import Any

import pandas as pd


ARRECADACAO_DATASET = "ipea_rgps_arrecadacao_liquida_mensal"
BENEFICIOS_DATASET = "ipea_rgps_beneficios_previdenciarios_mensal"
RESULTADO_DATASET = "ipea_rgps_resultado_primario_mensal"

ARRECADACAO_SERIES_CODE = "MPAS12_ARRLIQ12"
BENEFICIOS_SERIES_CODE = "MPAS12_BENPREV12"
RESULTADO_SERIES_CODE = "MPAS12_RESPRGPS12"


def build_ipea_previdencia_gold_outputs(
    frames: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    arrecadacao = find_series_frame(
        frames=frames,
        dataset_name=ARRECADACAO_DATASET,
        series_code=ARRECADACAO_SERIES_CODE,
    )
    beneficios = find_series_frame(
        frames=frames,
        dataset_name=BENEFICIOS_DATASET,
        series_code=BENEFICIOS_SERIES_CODE,
    )
    resultado = find_series_frame(
        frames=frames,
        dataset_name=RESULTADO_DATASET,
        series_code=RESULTADO_SERIES_CODE,
    )

    if arrecadacao.empty and beneficios.empty and resultado.empty:
        return {}

    monthly = build_rgps_monthly(
        arrecadacao=arrecadacao,
        beneficios=beneficios,
        resultado=resultado,
    )
    annual = build_rgps_annual(monthly)

    return {
        "rgps_fluxo_financeiro_por_mes": monthly,
        "rgps_fluxo_financeiro_por_ano": annual,
    }


def build_rgps_monthly(
    arrecadacao: pd.DataFrame,
    beneficios: pd.DataFrame,
    resultado: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "periodo",
        "exercicio",
        "mes",
        "arrecadacao_liquida",
        "beneficios_previdenciarios",
        "resultado_primario_oficial",
        "resultado_primario_calculado",
        "diferenca_resultado",
        "diferenca_relativa_percentual",
        "unidade",
        "status_periodo",
        "status_conciliacao",
    ]

    prepared_frames = [
        prepare_monthly_series(
            arrecadacao,
            value_name="arrecadacao_liquida",
        ),
        prepare_monthly_series(
            beneficios,
            value_name="beneficios_previdenciarios",
        ),
        prepare_monthly_series(
            resultado,
            value_name="resultado_primario_oficial",
        ),
    ]

    non_empty = [frame for frame in prepared_frames if not frame.empty]

    if not non_empty:
        return pd.DataFrame(columns=columns)

    first_period = min(frame["_periodo"].min() for frame in non_empty)
    last_period = max(frame["_periodo"].max() for frame in non_empty)

    base = pd.DataFrame(
        {
            "_periodo": pd.period_range(
                first_period,
                last_period,
                freq="M",
            )
        }
    )

    result = base

    for frame in prepared_frames:
        if frame.empty:
            continue

        result = result.merge(
            frame,
            on="_periodo",
            how="left",
        )

    for column in [
        "arrecadacao_liquida",
        "beneficios_previdenciarios",
        "resultado_primario_oficial",
    ]:
        if column not in result.columns:
            result[column] = pd.NA

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result["resultado_primario_calculado"] = (
        result["arrecadacao_liquida"] - result["beneficios_previdenciarios"]
    )
    result["diferenca_resultado"] = (
        result["resultado_primario_oficial"] - result["resultado_primario_calculado"]
    )
    result["diferenca_relativa_percentual"] = result.apply(
        lambda row: calculate_relative_difference(
            difference=row["diferenca_resultado"],
            reference=row["resultado_primario_oficial"],
        ),
        axis=1,
    )

    required_values = result[
        [
            "arrecadacao_liquida",
            "beneficios_previdenciarios",
            "resultado_primario_oficial",
        ]
    ]
    result["status_periodo"] = required_values.apply(
        classify_month_status,
        axis=1,
    )
    result["status_conciliacao"] = result.apply(
        classify_reconciliation,
        axis=1,
    )

    result["periodo"] = result["_periodo"].astype("string")
    result["exercicio"] = result["_periodo"].dt.year.astype("Int64")
    result["mes"] = result["_periodo"].dt.month.astype("Int64")
    result["unidade"] = "R$"

    monetary_columns = [
        "arrecadacao_liquida",
        "beneficios_previdenciarios",
        "resultado_primario_oficial",
        "resultado_primario_calculado",
        "diferenca_resultado",
    ]

    for column in monetary_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).round(2)

    result["diferenca_relativa_percentual"] = pd.to_numeric(
        result["diferenca_relativa_percentual"],
        errors="coerce",
    ).round(6)

    return result[columns].reset_index(drop=True)


def build_rgps_annual(
    monthly: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "exercicio",
        "arrecadacao_liquida",
        "beneficios_previdenciarios",
        "resultado_primario_oficial",
        "resultado_primario_calculado",
        "diferenca_resultado",
        "diferenca_relativa_percentual",
        "meses_arrecadacao_disponiveis",
        "meses_beneficios_disponiveis",
        "meses_resultado_disponiveis",
        "meses_comuns_disponiveis",
        "primeiro_mes_disponivel",
        "ultimo_mes_disponivel",
        "unidade",
        "status_periodo",
        "status_conciliacao",
    ]

    if monthly.empty:
        return pd.DataFrame(columns=columns)

    records: list[dict[str, Any]] = []

    for year, year_frame in monthly.groupby("exercicio", dropna=True):
        year_frame = year_frame.sort_values("mes").copy()

        arrecadacao_count = int(year_frame["arrecadacao_liquida"].notna().sum())
        beneficios_count = int(year_frame["beneficios_previdenciarios"].notna().sum())
        resultado_count = int(year_frame["resultado_primario_oficial"].notna().sum())
        common_mask = (
            year_frame[
                [
                    "arrecadacao_liquida",
                    "beneficios_previdenciarios",
                    "resultado_primario_oficial",
                ]
            ]
            .notna()
            .all(axis=1)
        )
        common_count = int(common_mask.sum())

        any_mask = (
            year_frame[
                [
                    "arrecadacao_liquida",
                    "beneficios_previdenciarios",
                    "resultado_primario_oficial",
                ]
            ]
            .notna()
            .any(axis=1)
        )
        available_months = year_frame.loc[any_mask, "mes"].dropna().astype(int).tolist()

        arrecadacao_total = sum_with_min_count(year_frame["arrecadacao_liquida"])
        beneficios_total = sum_with_min_count(year_frame["beneficios_previdenciarios"])
        resultado_oficial_total = sum_with_min_count(
            year_frame["resultado_primario_oficial"]
        )

        if arrecadacao_total is None or beneficios_total is None:
            resultado_calculado = None
        else:
            resultado_calculado = arrecadacao_total - beneficios_total

        if resultado_oficial_total is None or resultado_calculado is None:
            difference = None
        else:
            difference = resultado_oficial_total - resultado_calculado

        records.append(
            {
                "exercicio": int(year),
                "arrecadacao_liquida": arrecadacao_total,
                "beneficios_previdenciarios": beneficios_total,
                "resultado_primario_oficial": resultado_oficial_total,
                "resultado_primario_calculado": resultado_calculado,
                "diferenca_resultado": difference,
                "diferenca_relativa_percentual": (
                    calculate_relative_difference(
                        difference=difference,
                        reference=resultado_oficial_total,
                    )
                ),
                "meses_arrecadacao_disponiveis": arrecadacao_count,
                "meses_beneficios_disponiveis": beneficios_count,
                "meses_resultado_disponiveis": resultado_count,
                "meses_comuns_disponiveis": common_count,
                "primeiro_mes_disponivel": (
                    min(available_months) if available_months else None
                ),
                "ultimo_mes_disponivel": (
                    max(available_months) if available_months else None
                ),
                "unidade": "R$",
                "status_periodo": classify_annual_status(
                    arrecadacao_count=arrecadacao_count,
                    beneficios_count=beneficios_count,
                    resultado_count=resultado_count,
                    common_count=common_count,
                ),
                "status_conciliacao": classify_reconciliation_values(
                    official=resultado_oficial_total,
                    calculated=resultado_calculado,
                    difference=difference,
                ),
            }
        )

    result = pd.DataFrame(records, columns=columns)

    integer_columns = [
        "exercicio",
        "meses_arrecadacao_disponiveis",
        "meses_beneficios_disponiveis",
        "meses_resultado_disponiveis",
        "meses_comuns_disponiveis",
        "primeiro_mes_disponivel",
        "ultimo_mes_disponivel",
    ]

    for column in integer_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).astype("Int64")

    monetary_columns = [
        "arrecadacao_liquida",
        "beneficios_previdenciarios",
        "resultado_primario_oficial",
        "resultado_primario_calculado",
        "diferenca_resultado",
    ]

    for column in monetary_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        ).round(2)

    result["diferenca_relativa_percentual"] = pd.to_numeric(
        result["diferenca_relativa_percentual"],
        errors="coerce",
    ).round(6)

    return result.sort_values("exercicio").reset_index(drop=True)


def prepare_monthly_series(
    dataframe: pd.DataFrame,
    value_name: str,
) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame(
            columns=[
                "_periodo",
                value_name,
            ]
        )

    prepared = dataframe.copy()
    index = prepared.index

    dates = pd.to_datetime(
        get_series(
            prepared,
            "periodo_codigo",
            index=index,
        ),
        errors="coerce",
        utc=True,
    )

    years = pd.to_numeric(
        get_series(
            prepared,
            "exercicio",
            index=index,
        ),
        errors="coerce",
    ).fillna(dates.dt.year)
    months = pd.to_numeric(
        get_series(
            prepared,
            "mes",
            index=index,
        ),
        errors="coerce",
    ).fillna(dates.dt.month)

    prepared["_exercicio"] = years
    prepared["_mes"] = months
    prepared["_valor"] = pd.to_numeric(
        get_series(
            prepared,
            "valor",
            index=index,
        ),
        errors="coerce",
    )
    prepared["_fator"] = pd.to_numeric(
        get_series(
            prepared,
            "fator_multiplicador",
            index=index,
        ),
        errors="coerce",
    ).fillna(1.0)
    prepared["_valor_reais"] = prepared["_valor"] * prepared["_fator"]
    prepared["_coletado_em"] = pd.to_datetime(
        get_series(
            prepared,
            "coletado_em",
            index=index,
        ),
        errors="coerce",
        utc=True,
    )

    valid = prepared.loc[
        prepared["_exercicio"].notna()
        & prepared["_mes"].between(1, 12, inclusive="both")
    ].copy()

    if valid.empty:
        return pd.DataFrame(
            columns=[
                "_periodo",
                value_name,
            ]
        )

    valid["_exercicio"] = valid["_exercicio"].astype(int)
    valid["_mes"] = valid["_mes"].astype(int)
    valid["_periodo"] = pd.PeriodIndex(
        (
            valid["_exercicio"].astype("string")
            + "-"
            + valid["_mes"].astype("string").str.zfill(2)
        ),
        freq="M",
    )

    valid = (
        valid.sort_values(
            [
                "_periodo",
                "_coletado_em",
            ],
            na_position="first",
        )
        .drop_duplicates(
            subset=["_periodo"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    result = valid[
        [
            "_periodo",
            "_valor_reais",
        ]
    ].rename(
        columns={
            "_valor_reais": value_name,
        }
    )

    return result


def find_series_frame(
    frames: dict[str, pd.DataFrame],
    dataset_name: str,
    series_code: str,
) -> pd.DataFrame:
    direct = frames.get(dataset_name)

    if direct is not None and not direct.empty:
        return direct.copy()

    matching_frames: list[pd.DataFrame] = []

    for frame in frames.values():
        if frame.empty or "codigo_serie" not in frame.columns:
            continue

        mask = frame["codigo_serie"].astype("string").eq(series_code)

        if mask.any():
            matching_frames.append(frame.loc[mask].copy())

    if not matching_frames:
        return pd.DataFrame()

    return pd.concat(
        matching_frames,
        ignore_index=True,
    )


def get_series(
    dataframe: pd.DataFrame,
    column: str,
    index: pd.Index,
) -> pd.Series:
    if column in dataframe.columns:
        return dataframe[column]

    return pd.Series(
        pd.NA,
        index=index,
        dtype="object",
    )


def sum_with_min_count(series: pd.Series) -> float | None:
    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )
    total = numeric.sum(min_count=1)

    if pd.isna(total):
        return None

    return float(total)


def calculate_relative_difference(
    difference: Any,
    reference: Any,
) -> float | None:
    if difference is None or reference is None:
        return None

    if pd.isna(difference) or pd.isna(reference):
        return None

    reference_value = float(reference)

    if reference_value == 0:
        return None

    return abs(float(difference)) / abs(reference_value) * 100


def classify_month_status(row: pd.Series) -> str:
    available = row.notna().sum()

    if available == 3:
        return "completo"

    if available > 0:
        return "parcial"

    return "indisponivel"


def classify_annual_status(
    arrecadacao_count: int,
    beneficios_count: int,
    resultado_count: int,
    common_count: int,
) -> str:
    counts = [
        arrecadacao_count,
        beneficios_count,
        resultado_count,
    ]

    if counts == [12, 12, 12] and common_count == 12:
        return "completo"

    if max(counts) > 0:
        return "parcial"

    return "indisponivel"


def classify_reconciliation(row: pd.Series) -> str:
    return classify_reconciliation_values(
        official=row.get("resultado_primario_oficial"),
        calculated=row.get("resultado_primario_calculado"),
        difference=row.get("diferenca_resultado"),
    )


def classify_reconciliation_values(
    official: Any,
    calculated: Any,
    difference: Any,
) -> str:
    values = [
        official,
        calculated,
        difference,
    ]

    if any(value is None or pd.isna(value) for value in values):
        return "dados_insuficientes"

    if abs(float(difference)) <= 1.0:
        return "identidade_exata"

    return "diferenca_observada"
