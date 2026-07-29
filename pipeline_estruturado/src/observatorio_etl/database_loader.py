from __future__ import annotations

import hashlib
import math
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID, uuid4

import pandas as pd
from psycopg import Connection, sql
from psycopg.types.json import Jsonb

from observatorio_etl.database import database_connection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_COLUMNS = ("carga_id", "carregado_em")


class DatabaseLoadError(RuntimeError):
    """Erro de validação ou carga no PostgreSQL."""


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    source_path: Path
    table_name: str

    @property
    def staging_table(self) -> str:
        return f"staging.{self.table_name}"

    @property
    def gold_table(self) -> str:
        return f"gold.{self.table_name}"


@dataclass(frozen=True)
class ColumnMeta:
    name: str
    data_type: str
    numeric_scale: int | None
    nullable: bool


@dataclass(frozen=True)
class PreparedDataset:
    config: DatasetConfig
    dataframe: pd.DataFrame
    columns: tuple[ColumnMeta, ...]
    sha256: str


DATASETS: tuple[DatasetConfig, ...] = (
    DatasetConfig(
        "rgps_fluxo_financeiro_ano",
        PROJECT_ROOT
        / "data/gold/ipea/rgps_fluxo_financeiro_por_ano.parquet",
        "rgps_fluxo_financeiro_ano",
    ),
    DatasetConfig(
        "siop_previdencia_componentes_ano",
        PROJECT_ROOT
        / "data/gold/siop/previdencia_federal_componentes_por_ano.parquet",
        "siop_previdencia_componentes_ano",
    ),
    DatasetConfig(
        "siop_previdencia_validacao_ano",
        PROJECT_ROOT
        / "data/gold/siop/previdencia_federal_validacao_por_ano.parquet",
        "siop_previdencia_validacao_ano",
    ),
    DatasetConfig(
        "comparacao_ipea_siop_previdencia_ano",
        PROJECT_ROOT
        / "data/gold/comparacoes/ipea_siop_previdencia_federal_por_ano.parquet",
        "comparacao_ipea_siop_previdencia_ano",
    ),
    DatasetConfig(
        "ibge_populacao_ano",
        PROJECT_ROOT
        / "data/gold/ibge/populacao_brasil_por_ano.parquet",
        "ibge_populacao_ano",
    ),
    DatasetConfig(
        "ibge_pib_nominal_ano",
        PROJECT_ROOT
        / "data/gold/ibge/pib_nominal_brasil_por_ano.parquet",
        "ibge_pib_nominal_ano",
    ),
    DatasetConfig(
        "ibge_ipca_ano",
        PROJECT_ROOT
        / "data/gold/ibge/ipca_brasil_por_ano.parquet",
        "ibge_ipca_ano",
    ),
    DatasetConfig(
        "pnad_estrutura_etaria_ano",
        PROJECT_ROOT
        / "data/gold/ibge/estrutura_etaria_brasil_por_ano.parquet",
        "pnad_estrutura_etaria_ano",
    ),
    DatasetConfig(
        "pnad_mercado_trabalho_ano",
        PROJECT_ROOT
        / "data/gold/ibge/mercado_trabalho_brasil_por_ano.parquet",
        "pnad_mercado_trabalho_ano",
    ),
    DatasetConfig(
        "pnad_contribuicao_previdenciaria_ano",
        PROJECT_ROOT
        / "data/gold/ibge/contribuicao_previdenciaria_brasil_por_ano.parquet",
        "pnad_contribuicao_previdenciaria_ano",
    ),
    DatasetConfig(
        "ibge_nucleo_anual",
        PROJECT_ROOT
        / "data/gold/ibge/nucleo_ibge_anual.parquet",
        "ibge_nucleo_anual",
    ),
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def git_revision() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None

    return result.stdout.strip() or None


def table_columns(
    connection: Connection[Any],
    table_name: str,
) -> tuple[ColumnMeta, ...]:
    query = """
        SELECT
            column_name,
            data_type,
            numeric_scale,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'gold'
          AND table_name = %s
        ORDER BY ordinal_position;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, (table_name,))
        rows = cursor.fetchall()

    if not rows:
        raise DatabaseLoadError(
            f"Tabela gold.{table_name} não encontrada. "
            "Execute as migrations antes da carga."
        )

    return tuple(
        ColumnMeta(
            name=row["column_name"],
            data_type=row["data_type"],
            numeric_scale=(
                int(row["numeric_scale"])
                if row["numeric_scale"] is not None
                else None
            ),
            nullable=row["is_nullable"] == "YES",
        )
        for row in rows
        if row["column_name"] not in METADATA_COLUMNS
    )


def validate_dataframe(
    config: DatasetConfig,
    dataframe: pd.DataFrame,
    columns: Sequence[ColumnMeta],
) -> None:
    if dataframe.empty:
        raise DatabaseLoadError(f"{config.name} não possui registros.")

    expected = [column.name for column in columns]
    received = list(dataframe.columns)

    if received != expected:
        missing = [name for name in expected if name not in received]
        extra = [name for name in received if name not in expected]

        raise DatabaseLoadError(
            f"Colunas incompatíveis em {config.name}. "
            f"Ausentes: {missing or 'nenhuma'}; "
            f"extras: {extra or 'nenhuma'}; "
            f"ordem esperada: {expected}."
        )

    if "exercicio" not in dataframe.columns:
        raise DatabaseLoadError(
            f"{config.name} não possui a coluna exercicio."
        )

    required_with_nulls = [
        column.name
        for column in columns
        if not column.nullable and dataframe[column.name].isna().any()
    ]

    if required_with_nulls:
        raise DatabaseLoadError(
            f"{config.name} possui nulos em colunas obrigatórias: "
            f"{', '.join(required_with_nulls)}."
        )

    years = pd.to_numeric(dataframe["exercicio"], errors="coerce")

    if years.isna().any():
        raise DatabaseLoadError(
            f"{config.name} possui exercício nulo ou não numérico."
        )

    if not years.map(math.isfinite).all():
        raise DatabaseLoadError(
            f"{config.name} possui exercício infinito."
        )

    if not years.map(lambda value: float(value).is_integer()).all():
        raise DatabaseLoadError(
            f"{config.name} possui exercício não inteiro."
        )

    normalized_years = years.astype("int64")

    if ((normalized_years < 1900) | (normalized_years > 2100)).any():
        raise DatabaseLoadError(
            f"{config.name} possui exercício fora de 1900 a 2100."
        )

    duplicate_mask = normalized_years.duplicated(keep=False)

    if duplicate_mask.any():
        duplicates = sorted(
            normalized_years.loc[duplicate_mask].unique().tolist()
        )
        raise DatabaseLoadError(
            f"{config.name} possui exercícios duplicados: {duplicates}."
        )


def prepare_dataset(
    connection: Connection[Any],
    config: DatasetConfig,
) -> PreparedDataset:
    if not config.source_path.is_file():
        raise DatabaseLoadError(
            f"Arquivo não encontrado: {config.source_path}"
        )

    columns = table_columns(connection, config.table_name)
    dataframe = pd.read_parquet(config.source_path)
    validate_dataframe(config, dataframe, columns)

    return PreparedDataset(
        config=config,
        dataframe=dataframe,
        columns=columns,
        sha256=file_sha256(config.source_path),
    )


def prepare_datasets(
    datasets: Sequence[DatasetConfig] = DATASETS,
) -> list[PreparedDataset]:
    with database_connection(autocommit=True) as connection:
        return [prepare_dataset(connection, config) for config in datasets]


def is_null(value: Any) -> bool:
    try:
        result = pd.isna(value)
    except (TypeError, ValueError):
        return False

    return bool(result)


def decimal_value(value: Any, scale: int) -> Decimal:
    try:
        decimal = Decimal(str(value))

        if not decimal.is_finite():
            raise InvalidOperation

        quantizer = Decimal(1).scaleb(-scale)

        with localcontext() as context:
            context.prec = max(
                38,
                len(decimal.as_tuple().digits) + abs(scale) + 4,
            )
            return decimal.quantize(quantizer)

    except (InvalidOperation, TypeError, ValueError) as error:
        raise DatabaseLoadError(
            f"Não foi possível converter {value!r} "
            f"para NUMERIC com escala {scale}."
        ) from error


def integer_value(value: Any, column_name: str) -> int:
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise DatabaseLoadError(
            f"Não foi possível converter {value!r} "
            f"para inteiro em {column_name}."
        ) from error

    if not decimal.is_finite() or decimal != decimal.to_integral_value():
        raise DatabaseLoadError(
            f"Valor não inteiro em {column_name}: {value!r}."
        )

    return int(decimal)


def timestamp_value(
    value: Any,
    column_name: str,
    with_timezone: bool,
) -> datetime:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as error:
        raise DatabaseLoadError(
            f"Timestamp inválido em {column_name}: {value!r}."
        ) from error

    if pd.isna(timestamp):
        raise DatabaseLoadError(
            f"Timestamp inválido em {column_name}: {value!r}."
        )

    if with_timezone:
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
    elif timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert("UTC").tz_localize(None)

    return timestamp.to_pydatetime()


def date_value(value: Any, column_name: str) -> date:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as error:
        raise DatabaseLoadError(
            f"Data inválida em {column_name}: {value!r}."
        ) from error

    if pd.isna(timestamp):
        raise DatabaseLoadError(
            f"Data inválida em {column_name}: {value!r}."
        )

    return timestamp.date()


def convert_value(value: Any, column: ColumnMeta) -> Any:
    if is_null(value):
        if column.nullable:
            return None

        raise DatabaseLoadError(
            f"A coluna obrigatória {column.name} recebeu valor nulo."
        )

    if column.data_type in {"smallint", "integer", "bigint"}:
        return integer_value(value, column.name)

    if column.data_type == "numeric":
        if column.numeric_scale is None:
            raise DatabaseLoadError(
                f"Escala não encontrada para {column.name}."
            )

        return decimal_value(value, column.numeric_scale)

    if column.data_type in {"real", "double precision"}:
        converted = float(value)

        if not math.isfinite(converted):
            raise DatabaseLoadError(
                f"Valor não finito em {column.name}: {value!r}."
            )

        return converted

    if column.data_type in {"text", "character varying", "character"}:
        return str(value)

    if column.data_type == "timestamp with time zone":
        return timestamp_value(value, column.name, with_timezone=True)

    if column.data_type == "timestamp without time zone":
        return timestamp_value(value, column.name, with_timezone=False)

    if column.data_type == "date":
        return date_value(value, column.name)

    if column.data_type == "boolean":
        if isinstance(value, bool):
            return value

        normalized = str(value).strip().lower()

        if normalized in {"true", "1", "sim", "yes"}:
            return True

        if normalized in {"false", "0", "não", "nao", "no"}:
            return False

        raise DatabaseLoadError(
            f"Booleano inválido em {column.name}: {value!r}."
        )

    raise DatabaseLoadError(
        f"Tipo não suportado: {column.data_type} em {column.name}."
    )


def dataframe_rows(
    prepared: PreparedDataset,
    load_id: UUID,
    loaded_at: datetime,
) -> list[tuple[Any, ...]]:
    rows: list[tuple[Any, ...]] = []

    for values in prepared.dataframe.itertuples(index=False, name=None):
        converted = tuple(
            convert_value(value, column)
            for value, column in zip(
                values,
                prepared.columns,
                strict=True,
            )
        )
        rows.append((*converted, load_id, loaded_at))

    return rows


def register_execution(
    prepared_datasets: Sequence[PreparedDataset],
    command: str,
) -> tuple[UUID, dict[str, UUID]]:
    execution_id = uuid4()
    load_ids = {
        item.config.name: uuid4()
        for item in prepared_datasets
    }

    execution_sql = """
        INSERT INTO controle.etl_execucao (
            execucao_id,
            tipo_execucao,
            comando,
            fontes_solicitadas,
            status,
            versao_codigo,
            detalhes
        ) VALUES (
            %s,
            %s,
            %s,
            %s,
            'iniciada',
            %s,
            %s
        );
    """

    load_sql = """
        INSERT INTO controle.etl_carga (
            carga_id,
            execucao_id,
            camada,
            dataset,
            tabela_destino,
            arquivo_origem,
            hash_arquivo_sha256,
            linhas_lidas,
            linhas_carregadas,
            linhas_rejeitadas,
            status,
            detalhes
        ) VALUES (
            %s,
            %s,
            'gold',
            %s,
            %s,
            %s,
            %s,
            %s,
            0,
            0,
            'iniciada',
            %s
        );
    """

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                execution_sql,
                (
                    execution_id,
                    "carga_gold_postgres",
                    command,
                    Jsonb(
                        [
                            item.config.name
                            for item in prepared_datasets
                        ]
                    ),
                    git_revision(),
                    Jsonb(
                        {
                            "estrategia": (
                                "substituicao_integral_atomica"
                            ),
                            "quantidade_datasets": len(
                                prepared_datasets
                            ),
                        }
                    ),
                ),
            )

            for item in prepared_datasets:
                cursor.execute(
                    load_sql,
                    (
                        load_ids[item.config.name],
                        execution_id,
                        item.config.name,
                        item.config.gold_table,
                        str(
                            item.config.source_path.relative_to(
                                PROJECT_ROOT
                            )
                        ),
                        item.sha256,
                        len(item.dataframe),
                        Jsonb(
                            {
                                "staging": (
                                    item.config.staging_table
                                )
                            }
                        ),
                    ),
                )

    return execution_id, load_ids


def insert_staging(
    connection: Connection[Any],
    prepared: PreparedDataset,
    load_id: UUID,
) -> datetime:
    loaded_at = datetime.now(timezone.utc)
    column_names = [
        column.name
        for column in prepared.columns
    ]
    all_columns = [*column_names, *METADATA_COLUMNS]
    placeholders = sql.SQL(", ").join(
        sql.Placeholder()
        for _ in all_columns
    )

    truncate_sql = sql.SQL(
        "TRUNCATE TABLE staging.{};"
    ).format(
        sql.Identifier(prepared.config.table_name)
    )

    insert_sql = sql.SQL(
        "INSERT INTO staging.{} ({}) VALUES ({});"
    ).format(
        sql.Identifier(prepared.config.table_name),
        sql.SQL(", ").join(
            sql.Identifier(name)
            for name in all_columns
        ),
        placeholders,
    )

    rows = dataframe_rows(
        prepared,
        load_id,
        loaded_at,
    )

    with connection.cursor() as cursor:
        cursor.execute(truncate_sql)
        cursor.executemany(insert_sql, rows)

    return loaded_at


def validate_table(
    connection: Connection[Any],
    schema: str,
    prepared: PreparedDataset,
    load_id: UUID,
) -> None:
    query = sql.SQL(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(DISTINCT exercicio) AS distintos,
            MIN(exercicio) AS primeiro,
            MAX(exercicio) AS ultimo,
            COUNT(*) FILTER (
                WHERE carga_id <> %s
            ) AS carga_incorreta
        FROM {}.{};
        """
    ).format(
        sql.Identifier(schema),
        sql.Identifier(prepared.config.table_name),
    )

    with connection.cursor() as cursor:
        cursor.execute(query, (load_id,))
        result = cursor.fetchone()

    expected_total = len(prepared.dataframe)
    expected_years = pd.to_numeric(
        prepared.dataframe["exercicio"],
        errors="raise",
    ).astype("int64")
    expected_first = int(expected_years.min())
    expected_last = int(expected_years.max())

    valid = result is not None and (
        result["total"] == expected_total
        and result["distintos"] == expected_total
        and result["primeiro"] == expected_first
        and result["ultimo"] == expected_last
        and result["carga_incorreta"] == 0
    )

    if not valid:
        raise DatabaseLoadError(
            f"Falha na validação de "
            f"{schema}.{prepared.config.table_name}: "
            f"{dict(result) if result is not None else None}."
        )


def replace_gold(
    connection: Connection[Any],
    prepared: PreparedDataset,
) -> None:
    all_columns = [
        *(column.name for column in prepared.columns),
        *METADATA_COLUMNS,
    ]
    identifiers = sql.SQL(", ").join(
        sql.Identifier(name)
        for name in all_columns
    )

    delete_sql = sql.SQL(
        "DELETE FROM gold.{};"
    ).format(
        sql.Identifier(prepared.config.table_name)
    )

    insert_sql = sql.SQL(
        """
        INSERT INTO gold.{} ({})
        SELECT {}
        FROM staging.{}
        ORDER BY exercicio;
        """
    ).format(
        sql.Identifier(prepared.config.table_name),
        identifiers,
        identifiers,
        sql.Identifier(prepared.config.table_name),
    )

    with connection.cursor() as cursor:
        cursor.execute(delete_sql)
        cursor.execute(insert_sql)


def finish_load(
    connection: Connection[Any],
    load_id: UUID,
    row_count: int,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE controle.etl_carga
            SET linhas_carregadas = %s,
                finalizado_em = CURRENT_TIMESTAMP,
                status = 'concluida',
                mensagem_erro = NULL
            WHERE carga_id = %s;
            """,
            (row_count, load_id),
        )


def finish_execution(
    connection: Connection[Any],
    execution_id: UUID,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE controle.etl_execucao
            SET finalizado_em = CURRENT_TIMESTAMP,
                status = 'concluida',
                mensagem_erro = NULL
            WHERE execucao_id = %s;
            """,
            (execution_id,),
        )


def fail_execution(
    execution_id: UUID,
    error: Exception,
) -> None:
    message = f"{type(error).__name__}: {error}"[:4000]

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE controle.etl_carga
                SET finalizado_em = CURRENT_TIMESTAMP,
                    status = 'erro',
                    mensagem_erro = %s
                WHERE execucao_id = %s
                  AND status = 'iniciada';
                """,
                (message, execution_id),
            )
            cursor.execute(
                """
                UPDATE controle.etl_execucao
                SET finalizado_em = CURRENT_TIMESTAMP,
                    status = 'erro',
                    mensagem_erro = %s
                WHERE execucao_id = %s;
                """,
                (message, execution_id),
            )


def load_gold_datasets(command: str) -> dict[str, Any]:
    prepared_datasets = prepare_datasets()
    execution_id, load_ids = register_execution(
        prepared_datasets,
        command,
    )
    summaries: list[dict[str, Any]] = []

    try:
        with database_connection() as connection:
            for prepared in prepared_datasets:
                load_id = load_ids[prepared.config.name]
                loaded_at = insert_staging(
                    connection,
                    prepared,
                    load_id,
                )
                validate_table(
                    connection,
                    "staging",
                    prepared,
                    load_id,
                )
                replace_gold(connection, prepared)
                validate_table(
                    connection,
                    "gold",
                    prepared,
                    load_id,
                )
                finish_load(
                    connection,
                    load_id,
                    len(prepared.dataframe),
                )

                years = pd.to_numeric(
                    prepared.dataframe["exercicio"],
                    errors="raise",
                ).astype("int64")

                summaries.append(
                    {
                        "dataset": prepared.config.name,
                        "tabela": prepared.config.gold_table,
                        "linhas": len(prepared.dataframe),
                        "primeiro_exercicio": int(years.min()),
                        "ultimo_exercicio": int(years.max()),
                        "sha256": prepared.sha256,
                        "carregado_em": loaded_at.isoformat(),
                    }
                )

            finish_execution(connection, execution_id)

    except Exception as error:
        fail_execution(execution_id, error)
        raise

    return {
        "execucao_id": str(execution_id),
        "status": "concluida",
        "quantidade_datasets": len(summaries),
        "total_linhas": sum(
            item["linhas"]
            for item in summaries
        ),
        "datasets": summaries,
    }
