from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Any

from observatorio_etl.config import load_config
from observatorio_etl.database_loader import load_gold_datasets
from observatorio_etl.runner import EtlRunner


def print_pipeline_outputs(
    outputs: dict[str, list[Path]],
    root: Path,
) -> None:
    """Apresenta os arquivos produzidos pelo pipeline."""
    for layer, paths in outputs.items():
        print(f"{layer}: {len(paths)} arquivo(s)")

        for path in paths:
            try:
                displayed_path = path.relative_to(root)
            except ValueError:
                displayed_path = path

            print(displayed_path)


def print_database_summary(
    summary: dict[str, Any],
) -> None:
    """Apresenta o resumo da carga PostgreSQL."""
    print()
    print("Carga PostgreSQL concluída.")
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


def load_postgres() -> None:
    """Carrega no PostgreSQL os produtos Gold existentes."""
    summary = load_gold_datasets(command=shlex.join(sys.argv))

    print_database_summary(summary)


def main() -> None:
    parser = argparse.ArgumentParser(prog="observatorio-etl")

    parser.add_argument(
        "command",
        choices=[
            "run",
            "list-sources",
            "load-gold-postgres",
        ],
    )

    parser.add_argument(
        "--root",
        default=".",
    )

    parser.add_argument(
        "--config",
        default="config/sources.json",
    )

    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help=("Nome de uma fonte para executar. Pode ser repetido."),
    )

    parser.add_argument(
        "--load-postgres",
        action="store_true",
        help=(
            "Carrega os produtos Gold no PostgreSQL "
            "após uma execução completa do pipeline."
        ),
    )

    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "load-gold-postgres":
        if args.sources:
            parser.error("--source não pode ser usado com load-gold-postgres.")

        if args.load_postgres:
            parser.error("--load-postgres não deve ser usado com load-gold-postgres.")

        load_postgres()
        return

    config_path = root / args.config
    config = load_config(config_path)

    if args.command == "list-sources":
        if args.load_postgres:
            parser.error("--load-postgres só pode ser usado com o comando run.")

        for source in config.sources:
            print(f"{source.name} | {source.type} | {source.source}/{source.theme}")

        return

    selected_sources = set(args.sources) if args.sources else None

    if args.load_postgres and selected_sources:
        parser.error(
            "--load-postgres exige uma execução completa. "
            "Não use --source nessa operação."
        )

    if selected_sources:
        available_sources = {source.name for source in config.sources}

        unknown_sources = sorted(selected_sources - available_sources)

        if unknown_sources:
            unknown_text = ", ".join(unknown_sources)

            raise ValueError(f"Fontes não cadastradas: {unknown_text}")

    runner = EtlRunner(root, config)

    outputs = runner.run(source_names=selected_sources)

    print_pipeline_outputs(
        outputs=outputs,
        root=root,
    )

    if args.load_postgres:
        load_postgres()
