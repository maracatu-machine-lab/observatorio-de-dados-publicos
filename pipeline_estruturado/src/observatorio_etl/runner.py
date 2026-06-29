from pathlib import Path

import pandas as pd

from observatorio_etl.config import EtlConfig, SourceConfig
from observatorio_etl.ipeadata import IpeaDataClient, ipea_to_long, ipea_values_to_dataframe
from observatorio_etl.paths import ensure_dir
from observatorio_etl.sidra import SidraClient, sidra_raw_to_dataframe, sidra_to_long
from observatorio_etl.storage import write_dataframe, write_json


class EtlRunner:
    def __init__(self, root: Path, config: EtlConfig):
        self.root = root
        self.config = config
        self.sidra = SidraClient()
        self.ipea = IpeaDataClient()

    def run(self) -> dict[str, list[Path]]:
        outputs: dict[str, list[Path]] = {"bronze": [], "silver": [], "gold": []}
        silver_frames = []
        catalog_records = []

        for source in self.config.sources:
            long_frame, source_outputs = self.run_source(source)
            outputs["bronze"].extend(source_outputs.get("bronze", []))
            outputs["silver"].extend(source_outputs.get("silver", []))

            if not long_frame.empty:
                silver_frames.append(long_frame)
                catalog_records.append(
                    {
                        "dataset": source.name,
                        "tipo": source.type,
                        "fonte": source.source,
                        "tema": source.theme,
                        "linhas": len(long_frame),
                    }
                )

        if silver_frames:
            gold_frame = pd.concat(silver_frames, ignore_index=True)
            gold_path_csv = self.root / "data" / "gold" / "series_consolidadas.csv"
            gold_path_parquet = self.root / "data" / "gold" / "series_consolidadas.parquet"
            write_dataframe(gold_path_csv, gold_frame)
            write_dataframe(gold_path_parquet, gold_frame)
            outputs["gold"].extend([gold_path_csv, gold_path_parquet])

        catalog = pd.DataFrame(catalog_records)
        catalog_path = self.root / "data" / "gold" / "catalogo_series.csv"
        write_dataframe(catalog_path, catalog)
        outputs["gold"].append(catalog_path)

        return outputs

    def run_source(self, source: SourceConfig) -> tuple[pd.DataFrame, dict[str, list[Path]]]:
        if source.type == "sidra":
            return self.run_sidra_source(source)
        if source.type == "ipeadata":
            return self.run_ipeadata_source(source)
        raise ValueError(f"Tipo de fonte não suportado: {source.type}")

    def run_sidra_source(self, source: SourceConfig) -> tuple[pd.DataFrame, dict[str, list[Path]]]:
        params = source.params
        rows = self.sidra.fetch_table(
            table=str(params["table"]),
            variable=str(params["variable"]),
            period=str(params.get("period", "all")),
            territorial_level=str(params["territorial_level"]),
            localities=str(params.get("localities", "all")),
            decimals=str(params.get("decimals", "0")),
        )

        bronze_dir = ensure_dir(self.root / "data" / "bronze" / source.source / source.theme)
        silver_dir = ensure_dir(self.root / "data" / "silver" / source.source / source.theme)

        raw_json_path = write_json(bronze_dir / f"{source.name}.json", rows)
        raw_csv_path = write_dataframe(bronze_dir / f"{source.name}.csv", sidra_raw_to_dataframe(rows))

        long_frame = sidra_to_long(rows, source.name, source.source, source.theme)
        silver_csv_path = write_dataframe(silver_dir / f"{source.name}.csv", long_frame)
        silver_parquet_path = write_dataframe(silver_dir / f"{source.name}.parquet", long_frame)

        return long_frame, {"bronze": [raw_json_path, raw_csv_path], "silver": [silver_csv_path, silver_parquet_path]}

    def run_ipeadata_source(self, source: SourceConfig) -> tuple[pd.DataFrame, dict[str, list[Path]]]:
        series_code = str(source.params["series_code"])
        metadata = self.ipea.fetch_metadata(series_code)
        values = self.ipea.fetch_values(series_code)

        bronze_dir = ensure_dir(self.root / "data" / "bronze" / source.source / source.theme)
        silver_dir = ensure_dir(self.root / "data" / "silver" / source.source / source.theme)

        metadata_json_path = write_json(bronze_dir / f"{source.name}_metadata.json", metadata)
        values_json_path = write_json(bronze_dir / f"{source.name}_values.json", values)
        values_csv_path = write_dataframe(bronze_dir / f"{source.name}_values.csv", ipea_values_to_dataframe(values))

        long_frame = ipea_to_long(values, metadata, source.name, source.source, source.theme, series_code)
        silver_csv_path = write_dataframe(silver_dir / f"{source.name}.csv", long_frame)
        silver_parquet_path = write_dataframe(silver_dir / f"{source.name}.parquet", long_frame)

        return long_frame, {"bronze": [metadata_json_path, values_json_path, values_csv_path], "silver": [silver_csv_path, silver_parquet_path]}
