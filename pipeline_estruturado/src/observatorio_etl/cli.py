import argparse
from pathlib import Path

from observatorio_etl.config import load_config
from observatorio_etl.runner import EtlRunner


def main() -> None:
    parser = argparse.ArgumentParser(prog="observatorio-etl")
    parser.add_argument("command", choices=["run", "list-sources"])
    parser.add_argument("--root", default=".")
    parser.add_argument("--config", default="config/sources.json")
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="Nome de uma fonte para executar. Pode ser repetido.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_path = root / args.config
    config = load_config(config_path)

    if args.command == "list-sources":
        for source in config.sources:
            print(f"{source.name} | {source.type} | {source.source}/{source.theme}")
        return

    selected_sources = set(args.sources) if args.sources else None

    if selected_sources:
        available_sources = {source.name for source in config.sources}
        unknown_sources = sorted(selected_sources - available_sources)

        if unknown_sources:
            unknown_text = ", ".join(unknown_sources)
            raise ValueError(f"Fontes não cadastradas: {unknown_text}")

    runner = EtlRunner(root, config)
    outputs = runner.run(source_names=selected_sources)

    for layer, paths in outputs.items():
        print(f"{layer}: {len(paths)} arquivo(s)")
        for path in paths:
            print(path.relative_to(root))
