import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

import pandas as pd


GOLD_START_YEAR = 2015
GOLD_END_YEAR = 2026


def build_ibge_gold_outputs(
    frames: dict[str, pd.DataFrame],
    start_year: int = GOLD_START_YEAR,
    end_year: int = GOLD_END_YEAR,
) -> dict[str, pd.DataFrame]:
    population = build_population_annual(
        frames.get("populacao_estimada", pd.DataFrame()),
        start_year,
        end_year,
    )
    gdp = build_nominal_gdp_annual(
        frames.get("pib_nominal", pd.DataFrame()),
        start_year,
        end_year,
    )
    ipca = build_ipca_annual(
        frames.get("ipca", pd.DataFrame()),
        start_year,
        end_year,
    )
    age_structure = build_age_structure_annual(
        frames.get("estrutura_etaria", pd.DataFrame()),
        start_year,
        end_year,
    )
    labor = build_labor_market_annual(
        condition_frame=frames.get("condicao_trabalho", pd.DataFrame()),
        unemployment_frame=frames.get("taxa_desocupacao", pd.DataFrame()),
        informal_people_frame=frames.get(
            "informalidade_quantidade",
            pd.DataFrame(),
        ),
        informality_rate_frame=frames.get(
            "taxa_informalidade",
            pd.DataFrame(),
        ),
        start_year=start_year,
        end_year=end_year,
    )
    contribution = build_previdencia_contribution_annual(
        contributors_frame=frames.get(
            "contribuintes_previdencia_quantidade",
            pd.DataFrame(),
        ),
        percentage_frame=frames.get(
            "contribuintes_previdencia_percentual",
            pd.DataFrame(),
        ),
        start_year=start_year,
        end_year=end_year,
    )
    nucleus = build_ibge_nucleus(
        population=population,
        gdp=gdp,
        ipca=ipca,
        age_structure=age_structure,
        labor=labor,
        contribution=contribution,
        start_year=start_year,
        end_year=end_year,
    )

    return {
        "populacao_brasil_por_ano": population,
        "pib_nominal_brasil_por_ano": gdp,
        "ipca_brasil_por_ano": ipca,
        "estrutura_etaria_brasil_por_ano": age_structure,
        "mercado_trabalho_brasil_por_ano": labor,
        "contribuicao_previdenciaria_brasil_por_ano": contribution,
        "nucleo_ibge_anual": nucleus,
    }


def build_population_annual(
    dataframe: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    columns = [
        "fonte",
        "tema",
        "dataset",
        "exercicio",
        "populacao",
        "unidade_original",
        "status_periodo",
        "coletado_em",
    ]

    selected = prepare_year_frame(dataframe, start_year, end_year)
    selected = select_rows(
        selected,
        include_any=[
            "populacao residente estimada",
            "populacao estimada",
        ],
        exclude_any=["percentual", "taxa", "variacao"],
    )

    records = []
    for year, group in selected.groupby("exercicio", dropna=True):
        value, unit = first_value_and_unit(group)
        population = convert_people_value(value, unit)
        records.append(
            {
                "fonte": "ibge",
                "tema": "populacao",
                "dataset": "ibge_populacao_brasil_por_ano",
                "exercicio": int(year),
                "populacao": round_optional(population, 0),
                "unidade_original": unit,
                "status_periodo": value_status(population),
                "coletado_em": latest_collection_time(group),
            }
        )

    return finalize_frame(records, columns)


def build_nominal_gdp_annual(
    dataframe: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    columns = [
        "fonte",
        "tema",
        "dataset",
        "exercicio",
        "pib_nominal",
        "valor_original",
        "unidade_original",
        "multiplicador_para_reais",
        "status_periodo",
        "coletado_em",
    ]

    selected = prepare_year_frame(
        dataframe,
        start_year,
        end_year,
    )

    selected_by_code = pd.DataFrame(columns=selected.columns)

    if "variavel_codigo" in selected.columns:
        variable_codes = (
            selected["variavel_codigo"]
            .astype("string")
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )

        selected_by_code = selected.loc[variable_codes.eq("9808")].copy()

    if not selected_by_code.empty:
        selected = selected_by_code
    else:
        selected = select_rows(
            selected,
            include_any=[
                "pib valores correntes",
                "produto interno bruto a precos correntes",
                "produto interno bruto em valores correntes",
            ],
            exclude_any=[
                "per capita",
                "deflator",
                "variacao",
                "indice",
                "volume",
            ],
        )

    records = []

    for year, group in selected.groupby(
        "exercicio",
        dropna=True,
    ):
        original_value, unit = first_value_and_unit(group)
        multiplier = monetary_multiplier(unit)

        nominal_gdp = (
            original_value * multiplier
            if original_value is not None and multiplier is not None
            else None
        )

        records.append(
            {
                "fonte": "ibge",
                "tema": "pib",
                "dataset": "ibge_pib_nominal_brasil_por_ano",
                "exercicio": int(year),
                "pib_nominal": round_optional(
                    nominal_gdp,
                    2,
                ),
                "valor_original": original_value,
                "unidade_original": unit,
                "multiplicador_para_reais": multiplier,
                "status_periodo": value_status(nominal_gdp),
                "coletado_em": latest_collection_time(group),
            }
        )

    return finalize_frame(records, columns)


def build_ipca_annual(
    dataframe: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    columns = [
        "fonte",
        "tema",
        "dataset",
        "exercicio",
        "ipca_numero_indice_medio",
        "ipca_numero_indice_fim_periodo",
        "ipca_variacao_acumulada_ano",
        "meses_disponiveis",
        "ultimo_mes_disponivel",
        "status_periodo",
        "coletado_em",
    ]

    selected = prepare_year_frame(dataframe, start_year, end_year)
    index_rows = select_rows(
        selected,
        include_any=["numero indice"],
        exclude_any=["peso"],
    )
    accumulated_rows = select_rows(
        selected,
        include_any=["variacao acumulada no ano", "acumulada no ano"],
        exclude_any=["12 meses", "peso"],
    )

    years = sorted(
        int(year)
        for year in selected.get("exercicio", pd.Series(dtype="Int64"))
        .dropna()
        .unique()
        .tolist()
    )
    records = []

    for year in years:
        year_index = index_rows.loc[index_rows["exercicio"].eq(year)].copy()
        year_accumulated = accumulated_rows.loc[
            accumulated_rows["exercicio"].eq(year)
        ].copy()
        combined = pd.concat(
            [year_index, year_accumulated],
            ignore_index=True,
        )
        available_months = sorted(
            {
                int(month)
                for month in combined.get(
                    "mes",
                    pd.Series(dtype="float64"),
                )
                .dropna()
                .tolist()
                if 1 <= int(month) <= 12
            }
        )
        last_month = max(available_months) if available_months else None
        status = (
            "completo"
            if len(available_months) == 12 and last_month == 12
            else "parcial"
            if available_months
            else "indisponivel"
        )

        records.append(
            {
                "fonte": "ibge",
                "tema": "inflacao",
                "dataset": "ibge_ipca_brasil_por_ano",
                "exercicio": year,
                "ipca_numero_indice_medio": round_optional(
                    numeric_mean(year_index.get("valor")),
                    6,
                ),
                "ipca_numero_indice_fim_periodo": round_optional(
                    last_month_value(year_index),
                    6,
                ),
                "ipca_variacao_acumulada_ano": round_optional(
                    last_month_value(year_accumulated),
                    4,
                ),
                "meses_disponiveis": len(available_months),
                "ultimo_mes_disponivel": last_month,
                "status_periodo": status,
                "coletado_em": latest_collection_time(combined),
            }
        )

    return finalize_frame(records, columns)


def build_age_structure_annual(
    dataframe: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    columns = [
        "fonte",
        "tema",
        "dataset",
        "exercicio",
        "populacao_pnad",
        "populacao_60_mais",
        "percentual_60_mais",
        "unidade_original",
        "status_periodo",
        "coletado_em",
    ]

    selected = prepare_year_frame(dataframe, start_year, end_year)
    selected = filter_total_sex(selected)
    age_column = find_dimension_name_column(selected, "idade")
    records = []

    for year, group in selected.groupby("exercicio", dropna=True):
        total_value = extract_age_total(group, age_column)
        older_value = extract_age_60_plus(group, age_column)
        unit = first_text_value(group.get("unidade"))
        total_population = convert_people_value(total_value, unit)
        older_population = convert_people_value(older_value, unit)
        older_percentage = safe_percentage(
            older_population,
            total_population,
        )
        status = combined_status([total_population, older_population, older_percentage])

        records.append(
            {
                "fonte": "ibge",
                "tema": "demografia",
                "dataset": "pnad_estrutura_etaria_brasil_por_ano",
                "exercicio": int(year),
                "populacao_pnad": round_optional(total_population, 0),
                "populacao_60_mais": round_optional(older_population, 0),
                "percentual_60_mais": round_optional(older_percentage, 4),
                "unidade_original": unit,
                "status_periodo": status,
                "coletado_em": latest_collection_time(group),
            }
        )

    return finalize_frame(records, columns)


def build_labor_market_annual(
    condition_frame: pd.DataFrame,
    unemployment_frame: pd.DataFrame,
    informal_people_frame: pd.DataFrame,
    informality_rate_frame: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    columns = [
        "fonte",
        "tema",
        "dataset",
        "exercicio",
        "populacao_14_mais",
        "forca_de_trabalho",
        "populacao_ocupada",
        "populacao_desocupada",
        "taxa_desocupacao",
        "pessoas_informais",
        "taxa_informalidade",
        "status_periodo",
        "coletado_em",
    ]

    condition = prepare_year_frame(
        condition_frame,
        start_year,
        end_year,
    )
    unemployment = prepare_year_frame(
        unemployment_frame,
        start_year,
        end_year,
    )
    informal_people = prepare_year_frame(
        informal_people_frame,
        start_year,
        end_year,
    )
    informality_rate = prepare_year_frame(
        informality_rate_frame,
        start_year,
        end_year,
    )

    condition_category_column = (
        "condicao_em_relacao_a_forca_de_trabalho_e_condicao_de_ocupacao_codigo"
    )

    def condition_value(
        dataframe: pd.DataFrame,
        category_code: str,
        include_any: list[str],
        exclude_any: list[str] | None = None,
    ) -> float | None:
        if dataframe.empty:
            return None

        selected = dataframe.copy()

        if "variavel_codigo" in selected.columns:
            variable_codes = (
                selected["variavel_codigo"]
                .astype("string")
                .str.strip()
                .str.replace(r"\.0$", "", regex=True)
            )

            selected = selected.loc[variable_codes.eq("1641")].copy()

        if selected.empty:
            return None

        if condition_category_column in selected.columns:
            category_codes = (
                selected[condition_category_column]
                .astype("string")
                .str.strip()
                .str.replace(r"\.0$", "", regex=True)
            )

            selected_by_code = selected.loc[
                category_codes.eq(str(category_code))
            ].copy()

            if not selected_by_code.empty:
                selected = selected_by_code
            else:
                selected = select_rows(
                    selected,
                    include_any=include_any,
                    exclude_any=exclude_any,
                )
        else:
            selected = select_rows(
                selected,
                include_any=include_any,
                exclude_any=exclude_any,
            )

        value, unit = first_value_and_unit(selected)
        return convert_people_value(value, unit)

    years = sorted(
        set(extract_available_years(condition))
        | set(extract_available_years(unemployment))
        | set(extract_available_years(informal_people))
        | set(extract_available_years(informality_rate))
    )

    records = []

    for year in years:
        condition_year = condition.loc[condition["exercicio"].eq(year)].copy()

        unemployment_year = unemployment.loc[unemployment["exercicio"].eq(year)].copy()

        informal_year = informal_people.loc[
            informal_people["exercicio"].eq(year)
        ].copy()

        informality_year = informality_rate.loc[
            informality_rate["exercicio"].eq(year)
        ].copy()

        population_14 = condition_value(
            dataframe=condition_year,
            category_code="32385",
            include_any=["total"],
            exclude_any=[
                "forca de trabalho",
                "ocupada",
                "desocupada",
            ],
        )

        labor_force = condition_value(
            dataframe=condition_year,
            category_code="32386",
            include_any=["forca de trabalho"],
            exclude_any=[
                "fora da forca de trabalho",
                "ocupada",
                "desocupada",
            ],
        )

        occupied = condition_value(
            dataframe=condition_year,
            category_code="32387",
            include_any=[
                "forca de trabalho ocupada",
                "ocupada",
            ],
            exclude_any=["desocupada"],
        )

        unemployed = condition_value(
            dataframe=condition_year,
            category_code="32446",
            include_any=[
                "forca de trabalho desocupada",
                "desocupada",
            ],
        )

        unemployment_rate = first_numeric_value(unemployment_year.get("valor"))

        informal_selected = informal_year.copy()

        if not informal_selected.empty:
            if "variavel_codigo" in informal_selected.columns:
                variable_codes = (
                    informal_selected["variavel_codigo"]
                    .astype("string")
                    .str.strip()
                    .str.replace(r"\.0$", "", regex=True)
                )

                selected_by_variable = informal_selected.loc[
                    variable_codes.eq("4090")
                ].copy()

                if not selected_by_variable.empty:
                    informal_selected = selected_by_variable

            category_column = "situacao_de_informalidade_codigo"
            selected_by_category = pd.DataFrame(columns=informal_selected.columns)

            if category_column in informal_selected.columns:
                category_codes = (
                    informal_selected[category_column]
                    .astype("string")
                    .str.strip()
                    .str.replace(r"\.0$", "", regex=True)
                )

                selected_by_category = informal_selected.loc[
                    category_codes.eq("57303")
                ].copy()

            if not selected_by_category.empty:
                informal_selected = selected_by_category
            else:
                informal_selected = select_rows(
                    informal_selected,
                    include_any=["informais"],
                    exclude_any=[
                        "total",
                        "coeficiente de variacao",
                    ],
                )

        informal_value, informal_unit = first_value_and_unit(informal_selected)
        informal_count = convert_people_value(
            informal_value,
            informal_unit,
        )

        informality_selected = informality_year.copy()

        if not informality_selected.empty:
            selected_by_variable = pd.DataFrame(columns=informality_selected.columns)

            if "variavel_codigo" in informality_selected.columns:
                variable_codes = (
                    informality_selected["variavel_codigo"]
                    .astype("string")
                    .str.strip()
                    .str.replace(r"\.0$", "", regex=True)
                )

                selected_by_variable = informality_selected.loc[
                    variable_codes.eq("12466")
                ].copy()

            if not selected_by_variable.empty:
                informality_selected = selected_by_variable
            else:
                informality_selected = select_rows(
                    informality_selected,
                    include_any=["taxa de informalidade"],
                    exclude_any=["coeficiente de variacao"],
                )

        informality = first_numeric_value(informality_selected.get("valor"))

        values = [
            population_14,
            labor_force,
            occupied,
            unemployed,
            unemployment_rate,
            informal_count,
            informality,
        ]

        combined = pd.concat(
            [
                condition_year,
                unemployment_year,
                informal_year,
                informality_year,
            ],
            ignore_index=True,
        )

        records.append(
            {
                "fonte": "ibge",
                "tema": "mercado_trabalho",
                "dataset": "pnad_mercado_trabalho_brasil_por_ano",
                "exercicio": year,
                "populacao_14_mais": round_optional(
                    population_14,
                    0,
                ),
                "forca_de_trabalho": round_optional(
                    labor_force,
                    0,
                ),
                "populacao_ocupada": round_optional(
                    occupied,
                    0,
                ),
                "populacao_desocupada": round_optional(
                    unemployed,
                    0,
                ),
                "taxa_desocupacao": round_optional(
                    unemployment_rate,
                    4,
                ),
                "pessoas_informais": round_optional(
                    informal_count,
                    0,
                ),
                "taxa_informalidade": round_optional(
                    informality,
                    4,
                ),
                "status_periodo": combined_status(values),
                "coletado_em": latest_collection_time(combined),
            }
        )

    return finalize_frame(records, columns)


def build_previdencia_contribution_annual(
    contributors_frame: pd.DataFrame,
    percentage_frame: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    columns = [
        "fonte",
        "tema",
        "dataset",
        "exercicio",
        "pessoas_ocupadas_contribuintes_previdencia",
        "percentual_ocupados_contribuintes_previdencia",
        "status_periodo",
        "coletado_em",
    ]

    contributors = prepare_year_frame(
        contributors_frame,
        start_year,
        end_year,
    )
    percentage = prepare_year_frame(
        percentage_frame,
        start_year,
        end_year,
    )
    years = sorted(
        set(extract_available_years(contributors))
        | set(extract_available_years(percentage))
    )
    records = []

    for year in years:
        contributors_year = contributors.loc[contributors["exercicio"].eq(year)].copy()
        percentage_year = percentage.loc[percentage["exercicio"].eq(year)].copy()
        contributor_count = extract_measure(
            contributors_year,
            include_any=[
                "contribuintes",
                "contribuiam",
                "contribuia",
                "contribuicao para instituto de previdencia",
            ],
            exclude_any=["nao", "percentual", "taxa", "total"],
            converter=convert_people_value,
        )
        contributor_percentage = first_numeric_value(percentage_year.get("valor"))
        combined = pd.concat(
            [contributors_year, percentage_year],
            ignore_index=True,
        )

        records.append(
            {
                "fonte": "ibge",
                "tema": "contribuicao_previdenciaria",
                "dataset": "pnad_contribuicao_previdenciaria_brasil_por_ano",
                "exercicio": year,
                "pessoas_ocupadas_contribuintes_previdencia": round_optional(
                    contributor_count,
                    0,
                ),
                "percentual_ocupados_contribuintes_previdencia": round_optional(
                    contributor_percentage,
                    4,
                ),
                "status_periodo": combined_status(
                    [contributor_count, contributor_percentage]
                ),
                "coletado_em": latest_collection_time(combined),
            }
        )

    return finalize_frame(records, columns)


def build_ibge_nucleus(
    population: pd.DataFrame,
    gdp: pd.DataFrame,
    ipca: pd.DataFrame,
    age_structure: pd.DataFrame,
    labor: pd.DataFrame,
    contribution: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    nucleus = pd.DataFrame({"exercicio": list(range(start_year, end_year + 1))})
    nucleus = merge_indicator(
        nucleus,
        population,
        ["populacao", "status_periodo", "coletado_em"],
        "populacao",
    )
    nucleus = merge_indicator(
        nucleus,
        gdp,
        ["pib_nominal", "status_periodo", "coletado_em"],
        "pib",
    )
    nucleus = merge_indicator(
        nucleus,
        ipca,
        [
            "ipca_numero_indice_medio",
            "ipca_numero_indice_fim_periodo",
            "ipca_variacao_acumulada_ano",
            "meses_disponiveis",
            "ultimo_mes_disponivel",
            "status_periodo",
            "coletado_em",
        ],
        "ipca",
    )
    nucleus = merge_indicator(
        nucleus,
        age_structure,
        [
            "populacao_pnad",
            "populacao_60_mais",
            "percentual_60_mais",
            "status_periodo",
            "coletado_em",
        ],
        "estrutura_etaria",
    )
    nucleus = merge_indicator(
        nucleus,
        labor,
        [
            "populacao_14_mais",
            "forca_de_trabalho",
            "populacao_ocupada",
            "populacao_desocupada",
            "taxa_desocupacao",
            "pessoas_informais",
            "taxa_informalidade",
            "status_periodo",
            "coletado_em",
        ],
        "mercado_trabalho",
    )
    nucleus = merge_indicator(
        nucleus,
        contribution,
        [
            "pessoas_ocupadas_contribuintes_previdencia",
            "percentual_ocupados_contribuintes_previdencia",
            "status_periodo",
            "coletado_em",
        ],
        "contribuicao_previdenciaria",
    )

    status_columns = [
        "status_populacao",
        "status_pib",
        "status_ipca",
        "status_estrutura_etaria",
        "status_mercado_trabalho",
        "status_contribuicao_previdenciaria",
    ]
    for column in status_columns:
        if column not in nucleus.columns:
            nucleus[column] = "indisponivel"
        nucleus[column] = nucleus[column].fillna("indisponivel")

    collection_columns = [
        column for column in nucleus.columns if column.startswith("coletado_em_")
    ]
    if collection_columns:
        nucleus["coletado_em"] = nucleus[collection_columns].apply(
            latest_text_across_row,
            axis=1,
        )
        nucleus = nucleus.drop(columns=collection_columns)
    else:
        nucleus["coletado_em"] = datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        )

    preferred_columns = [
        "exercicio",
        "populacao",
        "pib_nominal",
        "ipca_numero_indice_medio",
        "ipca_numero_indice_fim_periodo",
        "ipca_variacao_acumulada_ano",
        "meses_disponiveis",
        "ultimo_mes_disponivel",
        "populacao_pnad",
        "populacao_60_mais",
        "percentual_60_mais",
        "populacao_14_mais",
        "forca_de_trabalho",
        "populacao_ocupada",
        "populacao_desocupada",
        "taxa_desocupacao",
        "pessoas_informais",
        "taxa_informalidade",
        "pessoas_ocupadas_contribuintes_previdencia",
        "percentual_ocupados_contribuintes_previdencia",
        "status_populacao",
        "status_pib",
        "status_ipca",
        "status_estrutura_etaria",
        "status_mercado_trabalho",
        "status_contribuicao_previdenciaria",
        "coletado_em",
    ]

    for column in preferred_columns:
        if column not in nucleus.columns:
            nucleus[column] = pd.NA

    return nucleus[preferred_columns].sort_values("exercicio").reset_index(drop=True)


def prepare_year_frame(
    dataframe: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    required_columns = [
        "exercicio",
        "mes",
        "valor",
        "unidade",
        "variavel_nome",
        "coletado_em",
    ]

    if dataframe.empty:
        columns = list(
            dict.fromkeys(
                [
                    *dataframe.columns,
                    *required_columns,
                ]
            )
        )
        return pd.DataFrame(columns=columns)

    result = dataframe.copy()

    for column in required_columns:
        if column not in result.columns:
            result[column] = pd.NA

    result["exercicio"] = pd.to_numeric(
        result["exercicio"],
        errors="coerce",
    ).astype("Int64")

    return result.loc[
        result["exercicio"].between(
            start_year,
            end_year,
            inclusive="both",
        )
    ].copy()


def row_search_text(dataframe: pd.DataFrame) -> pd.Series:
    if dataframe.empty:
        return pd.Series(dtype="string", index=dataframe.index)

    searchable_columns = [
        column
        for column in dataframe.columns
        if column.endswith("_nome") or column in {"variavel_nome", "unidade"}
    ]
    if not searchable_columns:
        return pd.Series("", index=dataframe.index, dtype="string")

    return (
        dataframe[searchable_columns]
        .fillna("")
        .astype("string")
        .agg(
            " | ".join,
            axis=1,
        )
        .map(normalize_text)
    )


def select_rows(
    dataframe: pd.DataFrame,
    include_any: list[str],
    exclude_any: list[str] | None = None,
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe.copy()

    text = row_search_text(dataframe)
    include_patterns = [normalize_text(value) for value in include_any]
    exclude_patterns = [normalize_text(value) for value in (exclude_any or [])]
    include_mask = text.map(
        lambda value: any(pattern in value for pattern in include_patterns)
    )
    exclude_mask = text.map(
        lambda value: any(pattern in value for pattern in exclude_patterns)
    )
    return dataframe.loc[include_mask & ~exclude_mask].copy()


def extract_measure(
    dataframe: pd.DataFrame,
    include_any: list[str],
    exclude_any: list[str] | None = None,
    converter: Any = None,
) -> float | None:
    selected = select_rows(
        dataframe,
        include_any=include_any,
        exclude_any=exclude_any,
    )
    if selected.empty:
        return None

    value, unit = first_value_and_unit(selected)
    if converter:
        return converter(value, unit)
    return value


def filter_total_sex(dataframe: pd.DataFrame) -> pd.DataFrame:
    sex_column = find_dimension_name_column(dataframe, "sexo")
    if sex_column is None:
        return dataframe.copy()

    normalized = dataframe[sex_column].map(normalize_text)
    total_mask = normalized.isin({"total", "ambos os sexos"})
    if total_mask.any():
        return dataframe.loc[total_mask].copy()
    return dataframe.copy()


def find_dimension_name_column(
    dataframe: pd.DataFrame,
    term: str,
) -> str | None:
    normalized_term = normalize_text(term).replace(" ", "_")
    candidates = [
        column
        for column in dataframe.columns
        if column.endswith("_nome")
        and normalized_term in normalize_text(column).replace(" ", "_")
    ]
    return candidates[0] if candidates else None


def extract_age_total(
    dataframe: pd.DataFrame,
    age_column: str | None,
) -> float | None:
    if age_column is None:
        return first_numeric_value(dataframe.get("valor"))

    normalized = dataframe[age_column].map(normalize_text)
    mask = normalized.isin({"total", "todas as idades"})
    selected = dataframe.loc[mask]
    return first_numeric_value(selected.get("valor"))


def extract_age_60_plus(
    dataframe: pd.DataFrame,
    age_column: str | None,
) -> float | None:
    if age_column is None:
        return None

    normalized = dataframe[age_column].map(normalize_text)
    aggregate_mask = normalized.map(
        lambda value: (
            "60 anos ou mais" in value
            or "60 anos e mais" in value
            or value == "60 ou mais"
        )
    )
    aggregate = dataframe.loc[aggregate_mask]
    aggregate_value = first_numeric_value(aggregate.get("valor"))
    if aggregate_value is not None:
        return aggregate_value

    detailed_mask = normalized.map(is_disjoint_60_plus_age_group)
    detailed = dataframe.loc[detailed_mask].copy()
    values = pd.to_numeric(detailed.get("valor"), errors="coerce").dropna()
    return float(values.sum()) if not values.empty else None


def is_disjoint_60_plus_age_group(value: str) -> bool:
    if not value or "total" in value:
        return False

    interval = re.search(r"(\d+)\s*a\s*(\d+)", value)
    if interval:
        return int(interval.group(1)) >= 60

    single = re.fullmatch(r"(\d+)\s*anos?", value)
    if single:
        return int(single.group(1)) >= 60

    open_group = re.search(r"(\d+)\s*anos?\s*(?:ou|e)\s*mais", value)
    if open_group:
        return int(open_group.group(1)) >= 60

    return False


def first_value_and_unit(
    dataframe: pd.DataFrame,
) -> tuple[float | None, str | None]:
    value = first_numeric_value(dataframe.get("valor"))
    unit = first_text_value(dataframe.get("unidade"))
    return value, unit


def first_numeric_value(series: pd.Series | None) -> float | None:
    if series is None:
        return None
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.iloc[0]) if not values.empty else None


def numeric_mean(series: pd.Series | None) -> float | None:
    if series is None:
        return None
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.mean()) if not values.empty else None


def first_text_value(series: pd.Series | None) -> str | None:
    if series is None:
        return None
    values = series.dropna().astype("string").str.strip()
    values = values.loc[values.ne("")]
    return str(values.iloc[0]) if not values.empty else None


def last_month_value(dataframe: pd.DataFrame) -> float | None:
    if dataframe.empty:
        return None

    result = dataframe.copy()
    result["mes"] = pd.to_numeric(result.get("mes"), errors="coerce")
    result["valor"] = pd.to_numeric(result.get("valor"), errors="coerce")
    result = result.dropna(subset=["valor"])

    if result.empty:
        return None

    with_month = result.dropna(subset=["mes"]).sort_values("mes")
    if not with_month.empty:
        return float(with_month.iloc[-1]["valor"])
    return float(result.iloc[-1]["valor"])


def monetary_multiplier(unit: str | None) -> float | None:
    normalized = normalize_text(unit)
    if not normalized:
        return None
    if "bilhoes de reais" in normalized or "bilhao de reais" in normalized:
        return 1_000_000_000.0
    if "milhoes de reais" in normalized or "milhao de reais" in normalized:
        return 1_000_000.0
    if "mil reais" in normalized:
        return 1_000.0
    if "reais" in normalized or normalized == "r":
        return 1.0
    return None


def convert_people_value(
    value: float | None,
    unit: str | None,
) -> float | None:
    if value is None:
        return None

    normalized = normalize_text(unit)
    if "milhoes de pessoas" in normalized or "milhao de pessoas" in normalized:
        return value * 1_000_000.0
    if "mil pessoas" in normalized:
        return value * 1_000.0
    return value


def safe_percentage(
    numerator: float | None,
    denominator: float | None,
) -> float | None:
    if numerator is None or denominator in {None, 0}:
        return None
    return numerator / denominator * 100.0


def combined_status(values: list[float | None]) -> str:
    available = sum(value is not None for value in values)
    if available == len(values) and values:
        return "completo"
    if available > 0:
        return "parcial"
    return "indisponivel"


def value_status(value: float | None) -> str:
    return "completo" if value is not None else "indisponivel"


def extract_available_years(dataframe: pd.DataFrame) -> list[int]:
    if dataframe.empty or "exercicio" not in dataframe.columns:
        return []
    return [int(value) for value in dataframe["exercicio"].dropna().unique().tolist()]


def latest_collection_time(dataframe: pd.DataFrame) -> str | None:
    if dataframe.empty or "coletado_em" not in dataframe.columns:
        return None
    values = dataframe["coletado_em"].dropna().astype("string")
    return str(values.max()) if not values.empty else None


def latest_text_across_row(row: pd.Series) -> str | None:
    values = [str(value) for value in row.dropna().tolist() if str(value).strip()]
    return max(values) if values else None


def merge_indicator(
    base: pd.DataFrame,
    indicator: pd.DataFrame,
    columns: list[str],
    suffix: str,
) -> pd.DataFrame:
    available = [column for column in columns if column in indicator.columns]
    if indicator.empty or not available:
        return base

    selected = indicator[["exercicio", *available]].copy()
    selected = selected.rename(
        columns={
            "status_periodo": f"status_{suffix}",
            "coletado_em": f"coletado_em_{suffix}",
        }
    )
    return base.merge(selected, on="exercicio", how="left")


def finalize_frame(
    records: list[dict[str, Any]],
    columns: list[str],
) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=columns)

    dataframe = pd.DataFrame(records)
    dataframe["exercicio"] = pd.to_numeric(
        dataframe["exercicio"],
        errors="coerce",
    ).astype("Int64")
    return dataframe[columns].sort_values("exercicio").reset_index(drop=True)


def round_optional(value: float | None, digits: int) -> float | None:
    return round(value, digits) if value is not None else None


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(
        character for character in text if not unicodedata.combining(character)
    )
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()
