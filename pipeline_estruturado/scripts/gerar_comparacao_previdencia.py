from pathlib import Path
from typing import Any

import pandas as pd

from observatorio_etl.previdencia_comparacoes import (
    build_previdencia_federal_comparison,
)
from observatorio_etl.siop_previdencia_gold import (
    build_siop_previdencia_gold_outputs,
)
from observatorio_etl.storage import write_dataframe


ROOT = Path(".")
SIOP_SILVER_DIR = ROOT / "data" / "silver" / "siop" / "execucao_orcamentaria"
SIOP_GOLD_DIR = ROOT / "data" / "gold" / "siop"
IPEA_ANNUAL_PATH = (
    ROOT / "data" / "gold" / "ipea" / "rgps_fluxo_financeiro_por_ano.parquet"
)
COMPARISON_GOLD_DIR = ROOT / "data" / "gold" / "comparacoes"

ALERT_THRESHOLD_PERCENT = 10.0

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
    "status_periodo_referencia",
    "status_comparabilidade",
    "observacao",
]


def read_dataframe(parquet_path: Path) -> pd.DataFrame:
    """Lê um arquivo Parquet ou o CSV correspondente."""
    csv_path = parquet_path.with_suffix(".csv")

    if parquet_path.is_file():
        return pd.read_parquet(parquet_path)

    if csv_path.is_file():
        return pd.read_csv(csv_path, low_memory=False)

    raise FileNotFoundError(
        f"Nenhum arquivo encontrado em {parquet_path} ou {csv_path}."
    )


def load_siop_frames() -> dict[str, pd.DataFrame]:
    """Carrega os arquivos Silver anuais do SIOP."""
    frames: dict[str, pd.DataFrame] = {}

    for exercicio in range(2015, 2027):
        parquet_path = (
            SIOP_SILVER_DIR / f"siop_loa_completa_{exercicio}.parquet"
        )
        csv_path = parquet_path.with_suffix(".csv")

        if parquet_path.is_file():
            frame = pd.read_parquet(parquet_path)
        elif csv_path.is_file():
            frame = pd.read_csv(csv_path, low_memory=False)
        else:
            print(f"Arquivo Silver do SIOP não encontrado para {exercicio}.")
            continue

        frames[str(exercicio)] = frame
        print(f"SIOP {exercicio}: {len(frame):,} linhas carregadas.")

    return frames


def write_outputs(
    directory: Path,
    outputs: dict[str, pd.DataFrame],
) -> list[Path]:
    """Grava cada DataFrame em CSV e Parquet."""
    directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for filename, dataframe in outputs.items():
        csv_path = write_dataframe(
            directory / f"{filename}.csv",
            dataframe,
        )
        parquet_path = write_dataframe(
            directory / f"{filename}.parquet",
            dataframe,
        )

        paths.extend([csv_path, parquet_path])
        print(f"{filename}: {len(dataframe):,} linhas")

    return paths


def numeric_or_none(value: Any) -> float | None:
    """Converte um valor escalar em float, preservando ausências como None."""
    if value is None:
        return None

    converted = pd.to_numeric(value, errors="coerce")

    if pd.isna(converted):
        return None

    return float(converted)


def normalize_status(value: Any) -> str:
    """Normaliza textos usados nos campos de status."""
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip().casefold()


def build_multisource_consistency(
    comparison: pd.DataFrame,
    threshold_percent: float = ALERT_THRESHOLD_PERCENT,
) -> pd.DataFrame:
    """
    Avalia a consistência entre IPEAData e SIOP.

    A divergência percentual é calculada por:

        abs(valor_comparado - valor_referencia)
        ---------------------------------------- x 100
                 abs(valor_referencia)

    O alerta é gerado quando a divergência é estritamente maior
    que o limite definido. Períodos parciais, valores ausentes
    e referência igual a zero não geram alerta.
    """
    if threshold_percent < 0:
        raise ValueError("O limite percentual não pode ser negativo.")

    if comparison.empty:
        return pd.DataFrame(columns=CONSISTENCY_COLUMNS)

    reference_column = "ipea_beneficios_previdenciarios"
    compared_column = "siop_rgps_beneficios_com_compensacao_pago"

    required_columns = [
        "exercicio",
        reference_column,
        compared_column,
        "ipea_status_periodo",
        "status_comparabilidade",
    ]

    missing_columns = [
        column for column in required_columns if column not in comparison.columns
    ]

    if missing_columns:
        raise ValueError(
            "A comparação não possui as colunas necessárias para a análise de "
            f"consistência: {missing_columns}."
        )

    records: list[dict[str, Any]] = []

    for _, row in comparison.iterrows():
        exercicio = row["exercicio"]
        reference_value = numeric_or_none(row[reference_column])
        compared_value = numeric_or_none(row[compared_column])
        period_status = normalize_status(row["ipea_status_periodo"])
        comparability_status = normalize_status(row["status_comparabilidade"])

        absolute_difference: float | None = None
        divergence_percent: float | None = None
        alert = False

        if reference_value is None or compared_value is None:
            consistency_status = "dados_insuficientes"
            observation = (
                "Uma ou mais fontes não possuem valor para o exercício."
            )
        elif comparability_status == "dados_insuficientes":
            consistency_status = "dados_insuficientes"
            observation = (
                "O produto de comparação classificou o exercício como insuficiente."
            )
        elif period_status != "completo" or comparability_status == "periodo_parcial":
            consistency_status = "nao_avaliado_periodo_parcial"
            observation = (
                "O exercício não foi avaliado porque uma das fontes possui período "
                "parcial ou data de corte diferente."
            )
        elif reference_value == 0:
            consistency_status = "nao_avaliado_referencia_zero"
            observation = (
                "A divergência percentual não foi calculada porque o valor de "
                "referência é igual a zero."
            )
        else:
            absolute_difference = abs(compared_value - reference_value)
            divergence_percent = (
                absolute_difference / abs(reference_value) * 100
            )
            alert = divergence_percent > threshold_percent

            if alert:
                consistency_status = "alerta_divergencia"
                observation = (
                    "A divergência superou o limite definido e requer revisão."
                )
            else:
                consistency_status = "dentro_do_limite"
                observation = (
                    "A divergência permaneceu dentro do limite definido."
                )

        records.append(
            {
                "exercicio": exercicio,
                "indicador": "beneficios_previdenciarios_rgps",
                "fonte_referencia": "IPEAData",
                "fonte_comparada": "SIOP",
                "valor_referencia": reference_value,
                "valor_comparado": compared_value,
                "diferenca_absoluta": (
                    round(absolute_difference, 2)
                    if absolute_difference is not None
                    else None
                ),
                "divergencia_percentual": (
                    round(divergence_percent, 6)
                    if divergence_percent is not None
                    else None
                ),
                "limite_percentual": threshold_percent,
                "alerta": alert,
                "status_consistencia": consistency_status,
                "status_periodo_referencia": period_status,
                "status_comparabilidade": comparability_status,
                "observacao": observation,
            }
        )

    result = pd.DataFrame(records, columns=CONSISTENCY_COLUMNS)

    result["exercicio"] = pd.to_numeric(
        result["exercicio"],
        errors="coerce",
    ).astype("Int64")

    numeric_columns = [
        "valor_referencia",
        "valor_comparado",
        "diferenca_absoluta",
        "divergencia_percentual",
        "limite_percentual",
    ]

    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    result["alerta"] = result["alerta"].fillna(False).astype(bool)

    return result.sort_values("exercicio", na_position="last").reset_index(drop=True)


def print_component_validation(
    siop_outputs: dict[str, pd.DataFrame],
) -> None:
    """Exibe a validação interna dos componentes do SIOP."""
    print("\nValidação dos componentes:")

    validation = siop_outputs.get(
        "previdencia_federal_validacao_por_ano",
        pd.DataFrame(),
    )

    if validation.empty:
        print("O produto de validação dos componentes não foi gerado.")
        return

    print(
        validation[
            [
                "exercicio",
                "status_validacao",
            ]
        ].to_string(index=False)
    )


def print_comparison_summary(comparison: pd.DataFrame) -> None:
    """Exibe o resumo da comparação entre IPEAData e SIOP."""
    print("\nResumo da comparação:")

    display_columns = [
        "exercicio",
        "ipea_beneficios_previdenciarios",
        "siop_rgps_beneficios_com_compensacao_pago",
        "cobertura_siop_rgps_com_compensacao_pago_percentual",
        "status_comparabilidade",
    ]

    print(comparison[display_columns].to_string(index=False))


def main() -> None:
    siop_frames = load_siop_frames()

    if not siop_frames:
        raise RuntimeError("Nenhum arquivo Silver do SIOP foi encontrado.")

    siop_outputs = build_siop_previdencia_gold_outputs(siop_frames)

    if not siop_outputs:
        raise RuntimeError("Nenhum produto Gold do SIOP foi gerado.")

    write_outputs(
        SIOP_GOLD_DIR,
        siop_outputs,
    )

    components = siop_outputs.get(
        "previdencia_federal_componentes_por_ano",
        pd.DataFrame(),
    )

    if components.empty:
        raise RuntimeError("O produto de componentes do SIOP não foi gerado.")

    ipea_annual = read_dataframe(IPEA_ANNUAL_PATH)

    if ipea_annual.empty:
        raise RuntimeError("O produto anual do IPEAData está vazio.")

    comparison = build_previdencia_federal_comparison(
        ipea_annual=ipea_annual,
        siop_components=components,
    )

    if comparison.empty:
        raise RuntimeError("A comparação IPEAData versus SIOP não foi gerada.")

    consistency = build_multisource_consistency(
        comparison=comparison,
        threshold_percent=ALERT_THRESHOLD_PERCENT,
    )

    if consistency.empty:
        raise RuntimeError(
            "A análise de consistência entre as fontes não foi gerada."
        )

    comparison_outputs = {
        "ipea_siop_previdencia_federal_por_ano": comparison,
        "consistencia_multifonte_previdencia_por_ano": consistency,
    }

    write_outputs(
        COMPARISON_GOLD_DIR,
        comparison_outputs,
    )

    print_component_validation(siop_outputs)
    print_comparison_summary(comparison)

    alerts = consistency.loc[
        consistency["alerta"].eq(True)
    ]

    print("\nAnálise de consistência entre fontes:")
    print(
        consistency[
            [
                "exercicio",
                "fonte_referencia",
                "fonte_comparada",
                "divergencia_percentual",
                "status_consistencia",
            ]
        ].to_string(index=False)
    )

    if alerts.empty:
        print(
            "\nNenhuma divergência superior a 10% "
            "foi identificada."
        )
    else:
        print(
            f"\nALERTA: {len(alerts)} exercício(s) "
            "apresentaram divergência superior a 10%."
        )

        print(
            alerts[
                [
                    "exercicio",
                    "fonte_referencia",
                    "fonte_comparada",
                    "divergencia_percentual",
                ]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()
