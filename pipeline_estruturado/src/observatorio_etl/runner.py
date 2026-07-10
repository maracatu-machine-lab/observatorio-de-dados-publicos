from pathlib import Path

import pandas as pd

from observatorio_etl.config import EtlConfig, SourceConfig
from observatorio_etl.ipeadata import (
    IpeaDataClient,
    ipea_to_long,
    ipea_values_to_dataframe,
)
from observatorio_etl.paths import ensure_dir
from observatorio_etl.sidra import (
    SidraClient,
    sidra_raw_to_dataframe,
    sidra_to_long,
)
from observatorio_etl.siop import (
    SiopClient,
    build_execucao_por_ano_table,
    prepare_siop_dataframe,
)
from observatorio_etl.storage import (
    write_dataframe,
    write_json,
)


class EtlRunner:
    def __init__(
        self,
        root: Path,
        config: EtlConfig,
    ):
        self.root = root
        self.config = config
        self.sidra = SidraClient()
        self.ipea = IpeaDataClient()
        self.siop = SiopClient()

    def run(self) -> dict[str, list[Path]]:
        outputs: dict[str, list[Path]] = {
            "bronze": [],
            "silver": [],
            "gold": [],
        }

        series_frames = []
        siop_frames = []
        catalog_records = []

        for source in self.config.sources:
            source_frame, source_outputs = self.run_source(source)

            outputs["bronze"].extend(source_outputs.get("bronze", []))
            outputs["silver"].extend(source_outputs.get("silver", []))

            if source_frame.empty:
                continue

            if source.type == "siop":
                siop_frames.append(source_frame)
                structure = "execucao_orcamentaria"
            else:
                series_frames.append(source_frame)
                structure = "serie_temporal"

            catalog_records.append(
                {
                    "dataset": source.name,
                    "tipo": source.type,
                    "fonte": source.source,
                    "tema": source.theme,
                    "estrutura": structure,
                    "linhas": len(source_frame),
                }
            )

        if series_frames:
            gold_frame = pd.concat(
                series_frames,
                ignore_index=True,
            )

            gold_path_csv = self.root / "data" / "gold" / "series_consolidadas.csv"

            gold_path_parquet = (
                self.root / "data" / "gold" / "series_consolidadas.parquet"
            )

            write_dataframe(
                gold_path_csv,
                gold_frame,
            )

            write_dataframe(
                gold_path_parquet,
                gold_frame,
            )

            outputs["gold"].extend(
                [
                    gold_path_csv,
                    gold_path_parquet,
                ]
            )

        if siop_frames:
            siop_gold_frame = pd.concat(
                siop_frames,
                ignore_index=True,
            )

            siop_gold_dir = ensure_dir(self.root / "data" / "gold" / "siop")

            siop_csv_path = write_dataframe(
                siop_gold_dir / "execucao_orcamentaria_consolidada.csv",
                siop_gold_frame,
            )

            siop_parquet_path = write_dataframe(
                siop_gold_dir / "execucao_orcamentaria_consolidada.parquet",
                siop_gold_frame,
            )

            execucao_por_ano = build_execucao_por_ano_table(siop_gold_frame)

            execucao_por_ano_csv_path = write_dataframe(
                siop_gold_dir / "execucao_por_ano.csv",
                execucao_por_ano,
            )

            execucao_por_ano_parquet_path = write_dataframe(
                siop_gold_dir / "execucao_por_ano.parquet",
                execucao_por_ano,
            )

            outputs["gold"].extend(
                [
                    siop_csv_path,
                    siop_parquet_path,
                    execucao_por_ano_csv_path,
                    execucao_por_ano_parquet_path,
                ]
            )

        catalog = pd.DataFrame(catalog_records)

        catalog_path = self.root / "data" / "gold" / "catalogo_series.csv"

        write_dataframe(
            catalog_path,
            catalog,
        )

        outputs["gold"].append(catalog_path)

        return outputs

    def run_source(
        self,
        source: SourceConfig,
    ) -> tuple[
        pd.DataFrame,
        dict[str, list[Path]],
    ]:
        if source.type == "sidra":
            return self.run_sidra_source(source)

        if source.type == "ipeadata":
            return self.run_ipeadata_source(source)

        if source.type == "siop":
            return self.run_siop_source(source)

        raise ValueError(f"Tipo de fonte não suportado: {source.type}")

    def run_sidra_source(
        self,
        source: SourceConfig,
    ) -> tuple[
        pd.DataFrame,
        dict[str, list[Path]],
    ]:
        params = source.params

        rows = self.sidra.fetch_table(
            table=str(params["table"]),
            variable=str(params["variable"]),
            period=str(params.get("period", "all")),
            territorial_level=str(params["territorial_level"]),
            localities=str(params.get("localities", "all")),
            decimals=str(params.get("decimals", "0")),
        )

        bronze_dir = ensure_dir(
            self.root / "data" / "bronze" / source.source / source.theme
        )

        silver_dir = ensure_dir(
            self.root / "data" / "silver" / source.source / source.theme
        )

        raw_json_path = write_json(
            bronze_dir / f"{source.name}.json",
            rows,
        )

        raw_csv_path = write_dataframe(
            bronze_dir / f"{source.name}.csv",
            sidra_raw_to_dataframe(rows),
        )

        long_frame = sidra_to_long(
            rows,
            source.name,
            source.source,
            source.theme,
        )

        silver_csv_path = write_dataframe(
            silver_dir / f"{source.name}.csv",
            long_frame,
        )

        silver_parquet_path = write_dataframe(
            silver_dir / f"{source.name}.parquet",
            long_frame,
        )

        return long_frame, {
            "bronze": [
                raw_json_path,
                raw_csv_path,
            ],
            "silver": [
                silver_csv_path,
                silver_parquet_path,
            ],
        }

    def run_ipeadata_source(
        self,
        source: SourceConfig,
    ) -> tuple[
        pd.DataFrame,
        dict[str, list[Path]],
    ]:
        series_code = str(source.params["series_code"])

        metadata = self.ipea.fetch_metadata(series_code)

        values = self.ipea.fetch_values(series_code)

        bronze_dir = ensure_dir(
            self.root / "data" / "bronze" / source.source / source.theme
        )

        silver_dir = ensure_dir(
            self.root / "data" / "silver" / source.source / source.theme
        )

        metadata_json_path = write_json(
            bronze_dir / f"{source.name}_metadata.json",
            metadata,
        )

        values_json_path = write_json(
            bronze_dir / f"{source.name}_values.json",
            values,
        )

        values_csv_path = write_dataframe(
            bronze_dir / f"{source.name}_values.csv",
            ipea_values_to_dataframe(values),
        )

        long_frame = ipea_to_long(
            values,
            metadata,
            source.name,
            source.source,
            source.theme,
            series_code,
        )

        silver_csv_path = write_dataframe(
            silver_dir / f"{source.name}.csv",
            long_frame,
        )

        silver_parquet_path = write_dataframe(
            silver_dir / f"{source.name}.parquet",
            long_frame,
        )

        return long_frame, {
            "bronze": [
                metadata_json_path,
                values_json_path,
                values_csv_path,
            ],
            "silver": [
                silver_csv_path,
                silver_parquet_path,
            ],
        }

    def run_siop_source(
        self,
        source: SourceConfig,
    ) -> tuple[
        pd.DataFrame,
        dict[str, list[Path]],
    ]:
        params = dict(source.params)
        exercicios = params.pop("exercicios", None)

        if exercicios is None:
            exercicio = params.pop("exercicio", None)

            if exercicio is None:
                raise ValueError(
                    "A fonte SIOP precisa informar 'exercicio' ou 'exercicios'."
                )

            exercicios = [exercicio]

        exercicios = sorted({int(exercicio) for exercicio in exercicios})

        bronze_dir = ensure_dir(
            self.root / "data" / "bronze" / source.source / source.theme
        )

        silver_dir = ensure_dir(
            self.root / "data" / "silver" / source.source / source.theme
        )

        frames = []

        source_outputs: dict[str, list[Path]] = {
            "bronze": [],
            "silver": [],
        }

        for exercicio in exercicios:
            year_params = dict(params)
            year_params["exercicio"] = exercicio

            raw_frame = self.siop.fetch_expenses(year_params)

            file_name = f"siop_execucao_orcamentaria_{exercicio}"

            request_json_path = write_json(
                bronze_dir / f"{file_name}_consulta.json",
                year_params,
            )

            raw_csv_path = write_dataframe(
                bronze_dir / f"{file_name}_bruto.csv",
                raw_frame,
            )

            silver_frame = prepare_siop_dataframe(
                raw_frame,
                dataset=file_name,
                fonte=source.source,
                tema=source.theme,
                exercicio=exercicio,
            )

            silver_csv_path = write_dataframe(
                silver_dir / f"{file_name}.csv",
                silver_frame,
            )

            silver_parquet_path = write_dataframe(
                silver_dir / f"{file_name}.parquet",
                silver_frame,
            )

            source_outputs["bronze"].extend(
                [
                    request_json_path,
                    raw_csv_path,
                ]
            )

            source_outputs["silver"].extend(
                [
                    silver_csv_path,
                    silver_parquet_path,
                ]
            )

            if not silver_frame.empty:
                frames.append(silver_frame)

        if not frames:
            return pd.DataFrame(), source_outputs

        return (
            pd.concat(
                frames,
                ignore_index=True,
            ),
            source_outputs,
        )
