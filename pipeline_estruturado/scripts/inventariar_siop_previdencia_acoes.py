from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/gold/siop/previdencia_federal_por_acao_ano.csv")
OUTPUT_DIR = Path("outputs")

OUTPUT_INVENTARIO = OUTPUT_DIR / "siop_previdencia_acoes_inventario.csv"
OUTPUT_POR_ANO = OUTPUT_DIR / "siop_previdencia_acoes_por_ano.csv"
OUTPUT_NOMES_DIVERGENTES = OUTPUT_DIR / "siop_previdencia_acoes_nomes_divergentes.csv"

REQUIRED_COLUMNS = {
    "exercicio",
    "subfuncao_codigo",
    "subfuncao_nome",
    "acao_codigo",
    "acao_nome",
    "valor_empenhado",
    "valor_liquidado",
    "valor_pago",
}


def join_unique(values: pd.Series) -> str:
    unique_values = sorted(
        {str(value).strip() for value in values.dropna().tolist() if str(value).strip()}
    )
    return " | ".join(unique_values)


def format_years(values: pd.Series) -> str:
    years = sorted(
        {
            int(value)
            for value in pd.to_numeric(
                values,
                errors="coerce",
            )
            .dropna()
            .tolist()
        }
    )
    return ",".join(str(year) for year in years)


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_PATH}")

    dataframe = pd.read_csv(
        INPUT_PATH,
        dtype={
            "subfuncao_codigo": "string",
            "acao_codigo": "string",
        },
        low_memory=False,
    )

    missing_columns = REQUIRED_COLUMNS - set(dataframe.columns)

    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))
        raise ValueError(
            "O arquivo não possui todas as colunas necessárias. "
            f"Colunas ausentes: {missing_text}"
        )

    dataframe["exercicio"] = pd.to_numeric(
        dataframe["exercicio"],
        errors="coerce",
    ).astype("Int64")

    for column in [
        "valor_empenhado",
        "valor_liquidado",
        "valor_pago",
    ]:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    dataframe["subfuncao_codigo"] = (
        dataframe["subfuncao_codigo"]
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(3)
    )
    dataframe["acao_codigo"] = (
        dataframe["acao_codigo"]
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.upper()
    )

    annual_totals = (
        dataframe.groupby(
            "exercicio",
            dropna=False,
        )[
            [
                "valor_empenhado",
                "valor_liquidado",
                "valor_pago",
            ]
        ]
        .sum(min_count=1)
        .rename(
            columns={
                "valor_empenhado": "funcao_09_valor_empenhado",
                "valor_liquidado": "funcao_09_valor_liquidado",
                "valor_pago": "funcao_09_valor_pago",
            }
        )
        .reset_index()
    )

    by_year = dataframe.merge(
        annual_totals,
        on="exercicio",
        how="left",
    )

    by_year["percentual_funcao_09_pago"] = (
        by_year["valor_pago"] / by_year["funcao_09_valor_pago"] * 100
    )

    by_year = by_year.sort_values(
        [
            "exercicio",
            "valor_pago",
            "subfuncao_codigo",
            "acao_codigo",
        ],
        ascending=[
            True,
            False,
            True,
            True,
        ],
        na_position="last",
    ).reset_index(drop=True)

    inventory = (
        dataframe.groupby(
            [
                "subfuncao_codigo",
                "acao_codigo",
            ],
            dropna=False,
        )
        .agg(
            subfuncao_nomes=(
                "subfuncao_nome",
                join_unique,
            ),
            acao_nomes=(
                "acao_nome",
                join_unique,
            ),
            primeiro_exercicio=(
                "exercicio",
                "min",
            ),
            ultimo_exercicio=(
                "exercicio",
                "max",
            ),
            exercicios_disponiveis=(
                "exercicio",
                format_years,
            ),
            quantidade_exercicios=(
                "exercicio",
                lambda values: (
                    pd.to_numeric(
                        values,
                        errors="coerce",
                    )
                    .dropna()
                    .nunique()
                ),
            ),
            total_valor_empenhado=(
                "valor_empenhado",
                lambda values: pd.to_numeric(
                    values,
                    errors="coerce",
                ).sum(min_count=1),
            ),
            total_valor_liquidado=(
                "valor_liquidado",
                lambda values: pd.to_numeric(
                    values,
                    errors="coerce",
                ).sum(min_count=1),
            ),
            total_valor_pago=(
                "valor_pago",
                lambda values: pd.to_numeric(
                    values,
                    errors="coerce",
                ).sum(min_count=1),
            ),
        )
        .reset_index()
    )

    inventory["primeiro_exercicio"] = pd.to_numeric(
        inventory["primeiro_exercicio"],
        errors="coerce",
    ).astype("Int64")
    inventory["ultimo_exercicio"] = pd.to_numeric(
        inventory["ultimo_exercicio"],
        errors="coerce",
    ).astype("Int64")
    inventory["quantidade_exercicios"] = pd.to_numeric(
        inventory["quantidade_exercicios"],
        errors="coerce",
    ).astype("Int64")

    total_paid_all_years = inventory["total_valor_pago"].sum(min_count=1)
    inventory["percentual_total_pago_periodo"] = (
        inventory["total_valor_pago"] / total_paid_all_years * 100
    )

    inventory = inventory.sort_values(
        [
            "total_valor_pago",
            "subfuncao_codigo",
            "acao_codigo",
        ],
        ascending=[
            False,
            True,
            True,
        ],
        na_position="last",
    ).reset_index(drop=True)

    code_name_counts = (
        dataframe.groupby(
            "acao_codigo",
            dropna=False,
        )
        .agg(
            quantidade_nomes=(
                "acao_nome",
                lambda values: values.dropna().astype(str).nunique(),
            ),
            nomes=(
                "acao_nome",
                join_unique,
            ),
            quantidade_subfuncoes=(
                "subfuncao_codigo",
                lambda values: values.dropna().astype(str).nunique(),
            ),
            subfuncoes=(
                "subfuncao_codigo",
                join_unique,
            ),
            primeiro_exercicio=(
                "exercicio",
                "min",
            ),
            ultimo_exercicio=(
                "exercicio",
                "max",
            ),
        )
        .reset_index()
    )

    divergent_names = code_name_counts.loc[
        (code_name_counts["quantidade_nomes"] > 1)
        | (code_name_counts["quantidade_subfuncoes"] > 1)
    ].copy()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    inventory.to_csv(
        OUTPUT_INVENTARIO,
        index=False,
        encoding="utf-8",
    )
    by_year.to_csv(
        OUTPUT_POR_ANO,
        index=False,
        encoding="utf-8",
    )
    divergent_names.to_csv(
        OUTPUT_NOMES_DIVERGENTES,
        index=False,
        encoding="utf-8",
    )

    print("\nInventário concluído.")
    print(f"Ações distintas: {len(inventory):,}")
    print(f"Códigos com nomes ou subfunções divergentes: {len(divergent_names):,}")

    print("\nArquivos gerados:")
    print(OUTPUT_INVENTARIO)
    print(OUTPUT_POR_ANO)
    print(OUTPUT_NOMES_DIVERGENTES)

    print("\n20 maiores ações por valor pago no período:")
    display_columns = [
        "subfuncao_codigo",
        "subfuncao_nomes",
        "acao_codigo",
        "acao_nomes",
        "primeiro_exercicio",
        "ultimo_exercicio",
        "quantidade_exercicios",
        "total_valor_pago",
        "percentual_total_pago_periodo",
    ]
    print(inventory[display_columns].head(20).to_string(index=False))

    latest_year = int(
        pd.to_numeric(
            by_year["exercicio"],
            errors="coerce",
        ).max()
    )
    latest = by_year.loc[by_year["exercicio"].eq(latest_year)]

    print(f"\n20 maiores ações em {latest_year}:")
    latest_columns = [
        "exercicio",
        "subfuncao_codigo",
        "subfuncao_nome",
        "acao_codigo",
        "acao_nome",
        "valor_pago",
        "percentual_funcao_09_pago",
    ]
    print(latest[latest_columns].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
