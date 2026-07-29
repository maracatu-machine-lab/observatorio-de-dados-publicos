from __future__ import annotations

import hashlib
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import psycopg

from observatorio_etl.database import (
    DatabaseConfigurationError,
    database_connection,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MIGRATIONS_DIR = PROJECT_ROOT / "database" / "migrations"


BOOTSTRAP_SQL = """
CREATE SCHEMA IF NOT EXISTS controle;

CREATE TABLE IF NOT EXISTS controle.migracao (
    migracao_id BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    nome_arquivo TEXT NOT NULL
        UNIQUE,

    checksum_sha256 TEXT NOT NULL,

    aplicado_em TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    duracao_ms BIGINT NOT NULL
        DEFAULT 0
);
"""


class MigrationError(RuntimeError):
    """Erro durante o gerenciamento das migrations."""


class MigrationChecksumError(MigrationError):
    """Uma migration aplicada foi alterada posteriormente."""


@dataclass(frozen=True)
class Migration:
    path: Path
    name: str
    content: str
    checksum: str


def calculate_checksum(content: str) -> str:
    """Calcula o SHA-256 do conteúdo de uma migration."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_migrations() -> list[Migration]:
    """Localiza e carrega as migrations em ordem alfabética."""
    if not MIGRATIONS_DIR.is_dir():
        raise MigrationError(
            f"O diretório de migrations não foi encontrado: {MIGRATIONS_DIR}"
        )

    paths = sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"))

    if not paths:
        raise MigrationError(f"Nenhuma migration foi encontrada em {MIGRATIONS_DIR}.")

    migrations: list[Migration] = []

    for path in paths:
        content = path.read_text(encoding="utf-8").strip()

        if not content:
            raise MigrationError(f"A migration {path.name} está vazia.")

        migrations.append(
            Migration(
                path=path,
                name=path.name,
                content=content,
                checksum=calculate_checksum(content),
            )
        )

    return migrations


def bootstrap_migration_control(
    connection: psycopg.Connection,
) -> None:
    """
    Cria a estrutura mínima usada para controlar migrations.

    Essa inicialização é necessária antes da primeira migration.
    """
    with connection.cursor() as cursor:
        cursor.execute(BOOTSTRAP_SQL)


def get_applied_migrations(
    connection: psycopg.Connection,
) -> dict[str, str]:
    """Retorna migration e checksum já registrados."""
    query = """
        SELECT
            nome_arquivo,
            checksum_sha256
        FROM controle.migracao
        ORDER BY nome_arquivo;
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    return {row["nome_arquivo"]: row["checksum_sha256"] for row in rows}


def register_migration(
    connection: psycopg.Connection,
    migration: Migration,
    duration_ms: int,
) -> None:
    """Registra uma migration concluída."""
    query = """
        INSERT INTO controle.migracao (
            nome_arquivo,
            checksum_sha256,
            duracao_ms
        )
        VALUES (
            %s,
            %s,
            %s
        );
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                migration.name,
                migration.checksum,
                duration_ms,
            ),
        )


def apply_migration(
    connection: psycopg.Connection,
    migration: Migration,
) -> int:
    """
    Executa uma migration em transação própria.

    Retorna a duração da execução em milissegundos.
    """
    started_at = time.perf_counter()

    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(migration.content)

        duration_ms = round((time.perf_counter() - started_at) * 1000)

        register_migration(
            connection,
            migration,
            duration_ms,
        )

    return duration_ms


def run_migrations() -> tuple[int, int]:
    """
    Executa as migrations ainda não aplicadas.

    Retorna:
    - quantidade aplicada;
    - quantidade ignorada por já estar aplicada.
    """
    migrations = load_migrations()

    applied_count = 0
    skipped_count = 0

    with database_connection(autocommit=True) as connection:
        bootstrap_migration_control(connection)

        applied = get_applied_migrations(connection)

        for migration in migrations:
            previous_checksum = applied.get(migration.name)

            if previous_checksum is not None:
                if previous_checksum != migration.checksum:
                    raise MigrationChecksumError(
                        "A migration já aplicada foi alterada: "
                        f"{migration.name}. "
                        "Não edite migrations executadas. "
                        "Crie uma nova migration."
                    )

                print(f"[IGNORADA] {migration.name} já foi aplicada.")

                skipped_count += 1
                continue

            print(f"[APLICANDO] {migration.name}")

            duration_ms = apply_migration(
                connection,
                migration,
            )

            print(f"[CONCLUÍDA] {migration.name} em {duration_ms} ms.")

            applied_count += 1

    return applied_count, skipped_count


def main() -> int:
    try:
        applied, skipped = run_migrations()

    except DatabaseConfigurationError as error:
        print(
            f"Erro de configuração: {error}",
            file=sys.stderr,
        )
        return 1

    except MigrationChecksumError as error:
        print(
            f"Erro de integridade: {error}",
            file=sys.stderr,
        )
        return 2

    except psycopg.Error as error:
        print(
            "Erro PostgreSQL durante as migrations.",
            file=sys.stderr,
        )
        print(
            f"Detalhe técnico: {error}",
            file=sys.stderr,
        )
        return 3

    except MigrationError as error:
        print(
            f"Erro de migration: {error}",
            file=sys.stderr,
        )
        return 4

    except Exception as error:
        print(
            f"Erro inesperado: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 5

    print()
    print("Migrations processadas.")
    print(f"Aplicadas: {applied}")
    print(f"Ignoradas: {skipped}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
