from __future__ import annotations

import sys
from typing import Any

import psycopg

from observatorio_etl.database import (
    DatabaseConfigurationError,
    test_database_connection,
)


def print_connection_info(
    info: dict[str, Any],
) -> None:
    """Apresenta informações não sensíveis da conexão."""
    print("Conexão com o PostgreSQL validada.")
    print()
    print(f"Banco:             {info['banco']}")
    print(f"Usuário:           {info['usuario']}")
    print(f"Schema atual:      {info['schema_atual']}")
    print(f"Versão PostgreSQL: {info['versao_postgresql']}")
    print(f"Fuso horário:      {info['fuso_horario']}")
    print(f"Testado em:        {info['testado_em']}")


def main() -> int:
    try:
        info = test_database_connection()

    except DatabaseConfigurationError as error:
        print(
            f"Erro de configuração: {error}",
            file=sys.stderr,
        )
        return 1

    except psycopg.OperationalError as error:
        print(
            "Não foi possível conectar ao PostgreSQL do Supabase.",
            file=sys.stderr,
        )
        print(
            f"Detalhe técnico: {error}",
            file=sys.stderr,
        )
        return 2

    except Exception as error:
        print(
            f"Erro inesperado durante o teste: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 3

    print_connection_info(info)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
