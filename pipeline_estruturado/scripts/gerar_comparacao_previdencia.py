from pathlib import Path

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


def read_dataframe(
    parquet_path: Path,
) -> pd.DataFrame:
    csv_path = parquet_path.with_suffix(".csv")

    if parquet_path.exists():
        return pd.read_parquet(parquet_path)

    if csv_path.exists():
        return pd.read_csv(
            csv_path,
            low_memory=False,
        )

    raise FileNotFoundError(
        f"Nenhum arquivo encontrado em {parquet_path} ou {csv_path}."
    )


def load_siop_frames() -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}

    for exercicio in range(
        2015,
        2027,
    ):
        parquet_path = SIOP_SILVER_DIR / f"siop_loa_completa_{exercicio}.parquet"
        csv_path = parquet_path.with_suffix(".csv")

        if parquet_path.exists():
            frame = pd.read_parquet(parquet_path)
        elif csv_path.exists():
            frame = pd.read_csv(
                csv_path,
                low_memory=False,
            )
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
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )
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
        paths.extend(
            [
                csv_path,
                parquet_path,
            ]
        )

        print(f"{filename}: {len(dataframe):,} linhas")

    return paths


def main() -> None:
    siop_frames = load_siop_frames()

    if not siop_frames:
        raise RuntimeError("Nenhum arquivo Silver do SIOP foi encontrado.")

    siop_outputs = build_siop_previdencia_gold_outputs(siop_frames)
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
    comparison = build_previdencia_federal_comparison(
        ipea_annual=ipea_annual,
        siop_components=components,
    )

    if comparison.empty:
        raise RuntimeError("A comparação IPEAData versus SIOP não foi gerada.")

    comparison_outputs = {"ipea_siop_previdencia_federal_por_ano": (comparison)}
    write_outputs(
        COMPARISON_GOLD_DIR,
        comparison_outputs,
    )

    print("\nValidação dos componentes:")
    validation = siop_outputs.get(
        "previdencia_federal_validacao_por_ano",
        pd.DataFrame(),
    )

    if not validation.empty:
        print(
            validation[
                [
                    "exercicio",
                    "status_validacao",
                ]
            ].to_string(index=False)
        )

    print("\nResumo da comparação:")
    display_columns = [
        "exercicio",
        "ipea_beneficios_previdenciarios",
        "siop_rgps_beneficios_com_compensacao_pago",
        "cobertura_siop_rgps_com_compensacao_pago_percentual",
        "status_comparabilidade",
    ]
    print(comparison[display_columns].to_string(index=False))


if __name__ == "__main__":
    main()
