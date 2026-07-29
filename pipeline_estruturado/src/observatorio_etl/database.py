from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import psycopg
from dotenv import load_dotenv
from psycopg import Connection
from psycopg.rows import dict_row


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class DatabaseConfigurationError(RuntimeError):
    """Erro na configuração da conexão com o PostgreSQL."""


def get_database_url() -> str:
    """
    Carrega e valida a variável DATABASE_URL.

    Variáveis definidas diretamente no ambiente têm prioridade
    sobre o conteúdo do arquivo .env.
    """
    load_dotenv(
        dotenv_path=ENV_FILE,
        override=False,
    )

    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        raise DatabaseConfigurationError(
            "A variável DATABASE_URL não foi encontrada. "
            f"Verifique o arquivo {ENV_FILE}."
        )

    if not database_url.startswith(("postgresql://", "postgres://")):
        raise DatabaseConfigurationError(
            "DATABASE_URL deve começar com postgresql:// ou postgres://."
        )

    return database_url


@contextmanager
def database_connection(
    *,
    autocommit: bool = False,
) -> Iterator[Connection[Any]]:
    """
    Abre uma conexão com o PostgreSQL.

    Quando autocommit é falso:
    - executa commit ao final;
    - executa rollback em caso de erro;
    - fecha a conexão em qualquer situação.
    """
    connection = psycopg.connect(
        get_database_url(),
        autocommit=autocommit,
        connect_timeout=20,
        application_name="observatorio_etl",
        row_factory=dict_row,
    )

    try:
        yield connection

        if not autocommit:
            connection.commit()

    except Exception:
        if not autocommit:
            connection.rollback()

        raise

    finally:
        connection.close()


def test_database_connection() -> dict[str, Any]:
    """
    Testa a conexão e retorna informações não sensíveis.
    """
    query = """
        SELECT
            current_database() AS banco,
            current_user AS usuario,
            current_schema() AS schema_atual,
            current_setting(
                'server_version'
            ) AS versao_postgresql,
            current_setting(
                'TimeZone'
            ) AS fuso_horario,
            current_timestamp AS testado_em;
    """

    with database_connection(autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()

    if result is None:
        raise RuntimeError(
            "A conexão foi aberta, mas o PostgreSQL "
            "não retornou as informações esperadas."
        )

    return dict(result)
