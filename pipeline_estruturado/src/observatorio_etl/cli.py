import argparse
from pathlib import Path

from observatorio_etl.config import load_config
from observatorio_etl.runner import EtlRunner


def main() -> None:
    parser = argparse.ArgumentParser(prog="observatorio-etl")
    parser.add_argument("command", choices=["run", "list-sources"])
    parser.add_argument("--root", default=".")
    parser.add_argument("--config", default="config/sources.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_path = root / args.config
    config = load_config(config_path)

    if args.command == "list-sources":
        for source in config.sources:
            print(f"{source.name} | {source.type} | {source.source}/{source.theme}")
        return

    runner = EtlRunner(root, config)
    outputs = runner.run()
    for layer, paths in outputs.items():
        print(f"{layer}: {len(paths)} arquivo(s)")
        for path in paths:
            print(path.relative_to(root))
