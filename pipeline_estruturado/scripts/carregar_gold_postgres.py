from __future__ import annotations

import shlex
import sys

import psycopg

from observatorio_etl.database import DatabaseConfigurationError
from observatorio_etl.database_loader import (
    DATASETS,
    DatabaseLoadError,
    load_gold_datasets,
)


def main() -> int:
    print("Iniciando a carga dos produtos Gold no PostgreSQL.")
    print(
        "Estratégia: substituição integral e atômica de "
        f"{len(DATASETS)} datasets."
    )
    print()

    try:
        summary = load_gold_datasets(
            command=shlex.join(sys.argv)
        )
    except DatabaseConfigurationError as error:
        print(
            f"Erro de configuração: {error}",
            file=sys.stderr,
        )
        return 1
    except DatabaseLoadError as error:
        print(
            f"Erro de carga: {error}",
            file=sys.stderr,
        )
        return 2
    except psycopg.Error as error:
        print(
            "Erro PostgreSQL durante a carga.",
            file=sys.stderr,
        )
        print(
            f"Detalhe técnico: {error}",
            file=sys.stderr,
        )
        return 3
    except Exception as error:
        print(
            "Erro inesperado: "
            f"{type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 4

    print("Carga concluída com sucesso.")
    print(f"Execução: {summary['execucao_id']}")
    print()

    for dataset in summary["datasets"]:
        print(
            f"- {dataset['dataset']}: "
            f"{dataset['linhas']} linhas, "
            f"exercícios "
            f"{dataset['primeiro_exercicio']} a "
            f"{dataset['ultimo_exercicio']}"
        )
        print(f"  Destino: {dataset['tabela']}")
        print(f"  SHA-256: {dataset['sha256']}")

    print()
    print(
        f"Total: {summary['quantidade_datasets']} datasets, "
        f"{summary['total_linhas']} linhas."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
