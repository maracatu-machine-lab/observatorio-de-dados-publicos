from typing import Any

import pandas as pd


IPCA_SERIES_CODE = "PRECOS12_IPCA12"
REAL_GDP_SERIES_CODE = "PAN4_PIBPMG4"


def build_ipea_gold_outputs(
    frames: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}

    ipca_frame = find_series_frame(
        frames=frames,
        series_code=IPCA_SERIES_CODE,
        dataset_name="ipea_ipca_indice_mensal",
    )
    if not ipca_frame.empty:
        outputs["ipca_brasil_por_ano"] = build_ipea_ipca_annual(ipca_frame)

    real_gdp_frame = find_series_frame(
        frames=frames,
        series_code=REAL_GDP_SERIES_CODE,
        dataset_name="ipea_pib_real_trimestral",
    )
    if not real_gdp_frame.empty:
        outputs["pib_real_variacao_interanual_trimestral"] = (
            build_ipea_real_gdp_quarterly(real_gdp_frame)
        )

    return outputs


def build_ipea_ipca_annual(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "exercicio",
        "ipca_indice_medio",
        "ipca_indice_fim_periodo",
        "ipca_variacao_acumulada_calculada",
        "meses_disponiveis",
        "status_periodo",
    ]
    prepared = prepare_series_frame(dataframe)

    valid = prepared.loc[
        prepared["_exercicio"].notna()
        & prepared["_mes"].notna()
        & prepared["_valor"].notna()
    ].copy()

    if valid.empty:
        return pd.DataFrame(columns=columns)

    valid["_exercicio"] = valid["_exercicio"].astype(int)
    valid["_mes"] = valid["_mes"].astype(int)
    valid = (
        valid.sort_values(
            [
                "_exercicio",
                "_mes",
                "_data",
                "_coletado_em",
            ],
            na_position="first",
        )
        .drop_duplicates(
            subset=[
                "_exercicio",
                "_mes",
            ],
            keep="last",
        )
        .reset_index(drop=True)
    )

    first_year = int(valid["_exercicio"].min())
    last_year = int(valid["_exercicio"].max())
    december_values = (
        valid.loc[
            valid["_mes"].eq(12),
            [
                "_exercicio",
                "_valor",
            ],
        ]
        .set_index("_exercicio")["_valor"]
        .to_dict()
    )

    records: list[dict[str, Any]] = []

    for year in range(first_year, last_year + 1):
        year_frame = valid.loc[valid["_exercicio"].eq(year)].sort_values(
            [
                "_mes",
                "_data",
            ]
        )

        available_months = sorted(
            {int(value) for value in year_frame["_mes"].dropna().tolist()}
        )
        month_count = len(available_months)

        if year_frame.empty:
            mean_index = None
            end_index = None
            accumulated_variation = None
            status = "indisponivel"
        else:
            mean_index = optional_float(year_frame["_valor"].mean())
            end_index = optional_float(year_frame.iloc[-1]["_valor"])
            previous_december = optional_float(december_values.get(year - 1))
            accumulated_variation = calculate_percentage_change(
                current=end_index,
                previous=previous_december,
            )

            if available_months == list(range(1, 13)):
                status = "completo"
            else:
                status = "parcial"

        records.append(
            {
                "exercicio": year,
                "ipca_indice_medio": mean_index,
                "ipca_indice_fim_periodo": end_index,
                "ipca_variacao_acumulada_calculada": (accumulated_variation),
                "meses_disponiveis": month_count,
                "status_periodo": status,
            }
        )

    result = pd.DataFrame(records, columns=columns)
    result["exercicio"] = pd.to_numeric(
        result["exercicio"],
        errors="coerce",
    ).astype("Int64")
    result["meses_disponiveis"] = pd.to_numeric(
        result["meses_disponiveis"],
        errors="coerce",
    ).astype("Int64")

    return result


def build_ipea_real_gdp_quarterly(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "exercicio",
        "trimestre",
        "periodo",
        "taxa_variacao_pib_real_interanual",
        "unidade",
        "status_periodo",
    ]
    prepared = prepare_series_frame(dataframe)

    valid_periods = prepared.loc[
        prepared["_exercicio"].notna() & prepared["_trimestre"].notna()
    ].copy()

    if valid_periods.empty:
        return pd.DataFrame(columns=columns)

    valid_periods["_exercicio"] = valid_periods["_exercicio"].astype(int)
    valid_periods["_trimestre"] = valid_periods["_trimestre"].astype(int)
    valid_periods["_periodo_trimestral"] = pd.PeriodIndex(
        (
            valid_periods["_exercicio"].astype("string")
            + "Q"
            + valid_periods["_trimestre"].astype("string")
        ),
        freq="Q",
    )
    valid_periods = (
        valid_periods.sort_values(
            [
                "_periodo_trimestral",
                "_data",
                "_coletado_em",
            ],
            na_position="first",
        )
        .drop_duplicates(
            subset=["_periodo_trimestral"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    first_period = valid_periods["_periodo_trimestral"].min()
    last_period = valid_periods["_periodo_trimestral"].max()
    expected_periods = pd.period_range(
        first_period,
        last_period,
        freq="Q",
    )

    base = pd.DataFrame(
        {
            "_periodo_trimestral": expected_periods,
        }
    )
    selected = valid_periods[
        [
            "_periodo_trimestral",
            "_valor",
            "_unidade",
        ]
    ].copy()
    result = base.merge(
        selected,
        on="_periodo_trimestral",
        how="left",
    )

    unit = first_non_empty(valid_periods["_unidade"])
    result["_unidade"] = result["_unidade"].fillna(unit)
    result["exercicio"] = result["_periodo_trimestral"].dt.year.astype("Int64")
    result["trimestre"] = result["_periodo_trimestral"].dt.quarter.astype("Int64")
    result["periodo"] = (
        result["exercicio"].astype("string")
        + "T"
        + result["trimestre"].astype("string")
    )
    result["taxa_variacao_pib_real_interanual"] = result["_valor"]
    result["unidade"] = result["_unidade"]
    result["status_periodo"] = result["taxa_variacao_pib_real_interanual"].apply(
        lambda value: "completo" if not pd.isna(value) else "indisponivel"
    )

    return result[columns].reset_index(drop=True)


def find_series_frame(
    frames: dict[str, pd.DataFrame],
    series_code: str,
    dataset_name: str,
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


def prepare_series_frame(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    prepared = dataframe.copy()
    index = prepared.index

    period_values = get_series(
        prepared,
        "periodo_codigo",
        index=index,
    )
    prepared["_data"] = pd.to_datetime(
        period_values,
        errors="coerce",
        utc=True,
    )

    year_values = pd.to_numeric(
        get_series(
            prepared,
            "exercicio",
            index=index,
        ),
        errors="coerce",
    )
    month_values = pd.to_numeric(
        get_series(
            prepared,
            "mes",
            index=index,
        ),
        errors="coerce",
    )
    quarter_values = pd.to_numeric(
        get_series(
            prepared,
            "trimestre",
            index=index,
        ),
        errors="coerce",
    )

    prepared["_exercicio"] = year_values.fillna(prepared["_data"].dt.year)
    prepared["_mes"] = month_values.fillna(prepared["_data"].dt.month)
    prepared["_trimestre"] = quarter_values.fillna(prepared["_data"].dt.quarter)

    numeric_values = pd.to_numeric(
        get_series(
            prepared,
            "valor",
            index=index,
        ),
        errors="coerce",
    )
    original_values = pd.to_numeric(
        get_series(
            prepared,
            "valor_original",
            index=index,
        ),
        errors="coerce",
    )
    prepared["_valor"] = numeric_values.fillna(original_values)
    prepared["_unidade"] = get_series(
        prepared,
        "unidade",
        index=index,
    )
    prepared["_coletado_em"] = pd.to_datetime(
        get_series(
            prepared,
            "coletado_em",
            index=index,
        ),
        errors="coerce",
        utc=True,
    )

    return prepared


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


def calculate_percentage_change(
    current: float | None,
    previous: float | None,
) -> float | None:
    if current is None or previous is None or previous == 0:
        return None

    return (current / previous - 1) * 100


def optional_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None

    return float(value)


def first_non_empty(series: pd.Series) -> Any:
    for value in series.tolist():
        if value is None or pd.isna(value):
            continue

        if str(value).strip():
            return value

    return None
