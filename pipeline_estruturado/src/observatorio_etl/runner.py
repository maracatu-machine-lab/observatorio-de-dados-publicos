from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from observatorio_etl.config import EtlConfig, SourceConfig
from observatorio_etl.ibge import build_ibge_gold_outputs
from observatorio_etl.ipea_gold import build_ipea_gold_outputs
from observatorio_etl.ipea_previdencia_gold import (
    build_ipea_previdencia_gold_outputs,
)
from observatorio_etl.ipeadata import (
    IpeaDataClient,
    ipea_to_long,
    ipea_values_to_dataframe,
)
from observatorio_etl.paths import ensure_dir
from observatorio_etl.previdencia_comparacoes import (
    build_previdencia_federal_comparison,
)
from observatorio_etl.sidra import (
    SidraClient,
    sidra_raw_to_dataframe,
    sidra_to_long,
)
from observatorio_etl.siop import (
    SiopClient,
    build_previdencia_publica_row,
    build_total_loa_row,
    prepare_siop_dataframe,
    validate_complete_loa_params,
)
from observatorio_etl.siop_previdencia_gold import (
    build_siop_previdencia_gold_outputs,
)
from observatorio_etl.storage import write_dataframe, write_json


class EtlRunner:
    def __init__(self, root: Path, config: EtlConfig):
        self.root = root
        self.config = config
        self.sidra = SidraClient()
        self.ipea = IpeaDataClient()
        self.siop = SiopClient()

    def run(
        self,
        source_names: set[str] | None = None,
    ) -> dict[str, list[Path]]:
        outputs: dict[str, list[Path]] = {
            "bronze": [],
            "silver": [],
            "gold": [],
        }
        series_frames: list[pd.DataFrame] = []
        siop_total_frames: list[pd.DataFrame] = []
        siop_previdencia_frames: list[pd.DataFrame] = []
        catalog_records: list[dict[str, object]] = []
        ibge_gold_requested = False
        ipea_gold_requested = False
        ipea_previdencia_requested = False
        siop_detail_gold_requested = False

        selected_sources = [
            source
            for source in self.config.sources
            if source_names is None or source.name in source_names
        ]

        for source in selected_sources:
            source_frame, source_outputs = self.run_source(source)
            outputs["bronze"].extend(source_outputs.get("bronze", []))
            outputs["silver"].extend(source_outputs.get("silver", []))

            if source.params.get("gold_builder"):
                ibge_gold_requested = True

            if source.type == "ipeadata":
                ipea_gold_requested = True

                if source.theme == "previdencia_rgps":
                    ipea_previdencia_requested = True

            if source.type == "siop":
                siop_detail_gold_requested = True

            if source_frame.empty:
                catalog_records.append(
                    self.build_catalog_record(
                        source=source,
                        structure=self.source_structure(source),
                        rows=0,
                    )
                )
                continue

            if source.type == "siop":
                total_frame = source_frame.loc[
                    source_frame["recorte"].eq("loa_total")
                ].drop(columns=["recorte"])

                previdencia_frame = source_frame.loc[
                    source_frame["recorte"].eq("previdencia_publica")
                ].drop(columns=["recorte"])

                siop_total_frames.append(total_frame)
                siop_previdencia_frames.append(previdencia_frame)
            else:
                series_frames.append(source_frame)

            catalog_records.append(
                self.build_catalog_record(
                    source=source,
                    structure=self.source_structure(source),
                    rows=len(source_frame),
                )
            )

        if series_frames and source_names is None:
            outputs["gold"].extend(self.write_consolidated_series(series_frames))

        if siop_total_frames and siop_previdencia_frames:
            outputs["gold"].extend(
                self.write_siop_gold(
                    siop_total_frames,
                    siop_previdencia_frames,
                )
            )

        if siop_detail_gold_requested:
            outputs["gold"].extend(self.write_siop_previdencia_detail_gold())

        if ibge_gold_requested:
            outputs["gold"].extend(self.write_ibge_gold())

        if ipea_gold_requested:
            outputs["gold"].extend(self.write_ipea_gold())

        if siop_detail_gold_requested and ipea_previdencia_requested:
            outputs["gold"].extend(self.write_previdencia_comparison())

        catalog_path = self.write_catalog(catalog_records)
        outputs["gold"].append(catalog_path)

        return outputs

    def run_source(
        self,
        source: SourceConfig,
    ) -> tuple[pd.DataFrame, dict[str, list[Path]]]:
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
    ) -> tuple[pd.DataFrame, dict[str, list[Path]]]:
        params = dict(source.params)
        table = str(params["table"])
        variable = params["variable"]
        period = params.get("period", "all")
        territorial_level = str(params["territorial_level"])
        localities = params.get("localities", "all")
        decimals = params.get("decimals")
        requested_classifications = params.get("classifications")
        periodicity = params.get("periodicity")
        fetch_metadata = bool(
            params.get("fetch_metadata", False) or requested_classifications == "all"
        )

        metadata = self.sidra.fetch_metadata(table) if fetch_metadata else None
        classifications = self.sidra.resolve_classifications(
            metadata=metadata,
            requested=requested_classifications,
        )
        query_description = self.sidra.build_query_description(
            table=table,
            variable=variable,
            period=period,
            territorial_level=territorial_level,
            localities=localities,
            decimals=str(decimals) if decimals is not None else None,
            classifications=classifications,
        )
        rows = self.sidra.fetch_table(
            table=table,
            variable=variable,
            period=period,
            territorial_level=territorial_level,
            localities=localities,
            decimals=str(decimals) if decimals is not None else None,
            classifications=classifications,
        )

        bronze_dir = ensure_dir(
            self.root / "data" / "bronze" / source.source / source.theme
        )
        silver_dir = ensure_dir(
            self.root / "data" / "silver" / source.source / source.theme
        )

        query_json_path = write_json(
            bronze_dir / f"{source.name}_consulta.json",
            query_description,
        )
        raw_json_path = write_json(
            bronze_dir / f"{source.name}_bruto.json",
            rows,
        )
        raw_csv_path = write_dataframe(
            bronze_dir / f"{source.name}_bruto.csv",
            sidra_raw_to_dataframe(rows),
        )

        bronze_paths = [
            query_json_path,
            raw_json_path,
            raw_csv_path,
        ]

        if metadata is not None:
            metadata_json_path = write_json(
                bronze_dir / f"{source.name}_metadados.json",
                metadata,
            )
            bronze_paths.insert(1, metadata_json_path)

        long_frame = sidra_to_long(
            rows=rows,
            dataset=source.name,
            fonte=source.source,
            tema=source.theme,
            periodicidade=str(periodicity) if periodicity else None,
            table=table,
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
            "bronze": bronze_paths,
            "silver": [silver_csv_path, silver_parquet_path],
        }

    def run_ipeadata_source(
        self,
        source: SourceConfig,
    ) -> tuple[pd.DataFrame, dict[str, list[Path]]]:
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
    ) -> tuple[pd.DataFrame, dict[str, list[Path]]]:
        params = dict(source.params)
        exercicios = params.pop("exercicios", None)

        if exercicios is None:
            exercicio = params.pop("exercicio", None)

            if exercicio is None:
                raise ValueError(
                    "A fonte SIOP precisa informar 'exercicio' ou 'exercicios'."
                )

            exercicios = [exercicio]

        validate_complete_loa_params(params)
        exercicios = sorted({int(exercicio) for exercicio in exercicios})

        bronze_dir = ensure_dir(
            self.root / "data" / "bronze" / source.source / source.theme
        )
        silver_dir = ensure_dir(
            self.root / "data" / "silver" / source.source / source.theme
        )

        summary_frames: list[pd.DataFrame] = []
        source_outputs: dict[str, list[Path]] = {
            "bronze": [],
            "silver": [],
        }

        for exercicio in exercicios:
            year_params = dict(params)
            year_params["exercicio"] = exercicio
            collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

            raw_frame = self.siop.fetch_expenses(year_params)
            file_name = f"siop_loa_completa_{exercicio}"

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
                coletado_em=collected_at,
            )
            silver_csv_path = write_dataframe(
                silver_dir / f"{file_name}.csv",
                silver_frame,
            )
            silver_parquet_path = write_dataframe(
                silver_dir / f"{file_name}.parquet",
                silver_frame,
            )

            total_row = build_total_loa_row(
                dataframe=silver_frame,
                fonte=source.source,
                exercicio=exercicio,
                coletado_em=collected_at,
            )
            total_row.insert(0, "recorte", "loa_total")

            previdencia_row = build_previdencia_publica_row(
                dataframe=silver_frame,
                fonte=source.source,
                exercicio=exercicio,
                coletado_em=collected_at,
            )
            previdencia_row.insert(
                0,
                "recorte",
                "previdencia_publica",
            )

            summary_frames.extend([total_row, previdencia_row])
            source_outputs["bronze"].extend([request_json_path, raw_csv_path])
            source_outputs["silver"].extend([silver_csv_path, silver_parquet_path])

        if not summary_frames:
            return pd.DataFrame(), source_outputs

        return (
            pd.concat(summary_frames, ignore_index=True),
            source_outputs,
        )

    def write_consolidated_series(
        self,
        frames: list[pd.DataFrame],
    ) -> list[Path]:
        gold_frame = pd.concat(
            frames,
            ignore_index=True,
        )

        object_columns = gold_frame.select_dtypes(
            include=["object"],
        ).columns

        for column in object_columns:
            gold_frame[column] = gold_frame[column].astype(
                "string",
            )

        csv_path = self.root / "data" / "gold" / "series_consolidadas.csv"
        parquet_path = self.root / "data" / "gold" / "series_consolidadas.parquet"

        write_dataframe(
            csv_path,
            gold_frame,
        )
        write_dataframe(
            parquet_path,
            gold_frame,
        )

        return [
            csv_path,
            parquet_path,
        ]

    def write_siop_gold(
        self,
        total_frames: list[pd.DataFrame],
        previdencia_frames: list[pd.DataFrame],
    ) -> list[Path]:
        gold_dir = ensure_dir(self.root / "data" / "gold" / "siop")
        total_gold = (
            pd.concat(total_frames, ignore_index=True)
            .sort_values("exercicio")
            .reset_index(drop=True)
        )
        previdencia_gold = (
            pd.concat(previdencia_frames, ignore_index=True)
            .sort_values("exercicio")
            .reset_index(drop=True)
        )
        total_path = write_dataframe(
            gold_dir / "loa_total_por_ano.csv",
            total_gold,
        )
        previdencia_path = write_dataframe(
            gold_dir / "loa_previdencia_publica_por_ano.csv",
            previdencia_gold,
        )
        return [total_path, previdencia_path]

    def write_siop_previdencia_detail_gold(self) -> list[Path]:
        frames: dict[str, pd.DataFrame] = {}

        for source in self.config.sources:
            if source.type != "siop":
                continue

            exercicios = source.params.get("exercicios")

            if exercicios is None:
                exercicio = source.params.get("exercicio")
                exercicios = [exercicio] if exercicio is not None else []

            for exercicio in sorted(
                {int(value) for value in exercicios if value is not None}
            ):
                silver_path = (
                    self.root
                    / "data"
                    / "silver"
                    / source.source
                    / source.theme
                    / f"siop_loa_completa_{exercicio}.parquet"
                )
                csv_path = silver_path.with_suffix(".csv")

                if silver_path.exists():
                    frame = pd.read_parquet(silver_path)
                elif csv_path.exists():
                    frame = pd.read_csv(
                        csv_path,
                        low_memory=False,
                    )
                else:
                    continue

                frames[f"{source.name}_{exercicio}"] = frame

        if not frames:
            return []

        gold_outputs = build_siop_previdencia_gold_outputs(frames)
        gold_dir = ensure_dir(self.root / "data" / "gold" / "siop")
        paths: list[Path] = []

        for filename, dataframe in gold_outputs.items():
            csv_path = write_dataframe(
                gold_dir / f"{filename}.csv",
                dataframe,
            )
            parquet_path = write_dataframe(
                gold_dir / f"{filename}.parquet",
                dataframe,
            )
            paths.extend(
                [
                    csv_path,
                    parquet_path,
                ]
            )

        return paths

    def write_ibge_gold(self) -> list[Path]:
        frames: dict[str, pd.DataFrame] = {}
        start_years: list[int] = []
        end_years: list[int] = []

        for source in self.config.sources:
            builder = source.params.get("gold_builder")

            if not builder:
                continue

            silver_path = (
                self.root
                / "data"
                / "silver"
                / source.source
                / source.theme
                / f"{source.name}.parquet"
            )
            csv_path = silver_path.with_suffix(".csv")

            if silver_path.exists():
                frame = pd.read_parquet(silver_path)
            elif csv_path.exists():
                frame = pd.read_csv(csv_path)
            else:
                continue

            frames[str(builder)] = frame
            start_years.append(int(source.params.get("gold_start_year", 2015)))
            end_years.append(int(source.params.get("gold_end_year", 2026)))

        if not frames:
            return []

        start_year = min(start_years) if start_years else 2015
        end_year = max(end_years) if end_years else 2026
        gold_outputs = build_ibge_gold_outputs(
            frames=frames,
            start_year=start_year,
            end_year=end_year,
        )
        gold_dir = ensure_dir(self.root / "data" / "gold" / "ibge")
        paths: list[Path] = []

        for filename, dataframe in gold_outputs.items():
            csv_path = write_dataframe(
                gold_dir / f"{filename}.csv",
                dataframe,
            )
            parquet_path = write_dataframe(
                gold_dir / f"{filename}.parquet",
                dataframe,
            )
            paths.extend([csv_path, parquet_path])

        return paths

    def write_ipea_gold(self) -> list[Path]:
        frames: dict[str, pd.DataFrame] = {}

        for source in self.config.sources:
            if source.type != "ipeadata":
                continue

            silver_path = (
                self.root
                / "data"
                / "silver"
                / source.source
                / source.theme
                / f"{source.name}.parquet"
            )
            csv_path = silver_path.with_suffix(".csv")

            if silver_path.exists():
                frame = pd.read_parquet(silver_path)
            elif csv_path.exists():
                frame = pd.read_csv(csv_path)
            else:
                continue

            frames[source.name] = frame

        if not frames:
            return []

        gold_outputs = build_ipea_gold_outputs(frames)
        previdencia_outputs = build_ipea_previdencia_gold_outputs(frames)
        gold_outputs.update(previdencia_outputs)

        gold_dir = ensure_dir(self.root / "data" / "gold" / "ipea")
        paths: list[Path] = []

        for filename, dataframe in gold_outputs.items():
            csv_path = write_dataframe(
                gold_dir / f"{filename}.csv",
                dataframe,
            )
            parquet_path = write_dataframe(
                gold_dir / f"{filename}.parquet",
                dataframe,
            )
            paths.extend([csv_path, parquet_path])

        return paths

    def write_previdencia_comparison(
        self,
    ) -> list[Path]:
        ipea_path = (
            self.root
            / "data"
            / "gold"
            / "ipea"
            / "rgps_fluxo_financeiro_por_ano.parquet"
        )
        ipea_csv_path = ipea_path.with_suffix(".csv")
        siop_path = (
            self.root
            / "data"
            / "gold"
            / "siop"
            / "previdencia_federal_componentes_por_ano.parquet"
        )
        siop_csv_path = siop_path.with_suffix(".csv")

        if ipea_path.exists():
            ipea_frame = pd.read_parquet(ipea_path)
        elif ipea_csv_path.exists():
            ipea_frame = pd.read_csv(
                ipea_csv_path,
                low_memory=False,
            )
        else:
            return []

        if siop_path.exists():
            siop_frame = pd.read_parquet(siop_path)
        elif siop_csv_path.exists():
            siop_frame = pd.read_csv(
                siop_csv_path,
                low_memory=False,
            )
        else:
            return []

        comparison = build_previdencia_federal_comparison(
            ipea_annual=ipea_frame,
            siop_components=siop_frame,
        )

        if comparison.empty:
            return []

        gold_dir = ensure_dir(self.root / "data" / "gold" / "comparacoes")
        csv_path = write_dataframe(
            gold_dir / "ipea_siop_previdencia_federal_por_ano.csv",
            comparison,
        )
        parquet_path = write_dataframe(
            gold_dir / "ipea_siop_previdencia_federal_por_ano.parquet",
            comparison,
        )

        return [
            csv_path,
            parquet_path,
        ]

    def write_catalog(
        self,
        records: list[dict[str, object]],
    ) -> Path:
        catalog_path = self.root / "data" / "gold" / "catalogo_series.csv"
        new_catalog = pd.DataFrame(records)

        if catalog_path.exists():
            current_catalog = pd.read_csv(catalog_path)
            catalog = pd.concat(
                [current_catalog, new_catalog],
                ignore_index=True,
            )
            catalog = catalog.drop_duplicates(
                subset=["dataset"],
                keep="last",
            )
        else:
            catalog = new_catalog

        if not catalog.empty and "dataset" in catalog.columns:
            catalog = catalog.sort_values("dataset").reset_index(drop=True)

        return write_dataframe(catalog_path, catalog)

    def build_catalog_record(
        self,
        source: SourceConfig,
        structure: str,
        rows: int,
    ) -> dict[str, object]:
        return {
            "dataset": source.name,
            "tipo": source.type,
            "fonte": source.source,
            "tema": source.theme,
            "estrutura": structure,
            "linhas": rows,
            "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    def source_structure(self, source: SourceConfig) -> str:
        if source.type == "siop":
            return "resumo_execucao_orcamentaria"

        if source.params.get("gold_builder"):
            return "indicador_ibge"

        return "serie_temporal"
