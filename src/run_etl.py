"""Orquestador del pipeline ETL.

Ejecuta en orden los tres scripts de src/etl/:
    1. extract.py     -> datos raw de Apify en data/raw/
    2. transform.py   -> 6 tablas de negocio en data/processed/
    3. load.py        -> carga las tablas en BigQuery (opcional)

Uso:
    python src/run_etl.py
    python src/run_etl.py --dry-run
    python src/run_etl.py --skip-extract
    python src/run_etl.py --skip-load
    python src/run_etl.py --skip-extract --tables reviews themes
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Evitar errores de codificación con emojis en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ETL_DIR = PROJECT_ROOT / "src" / "etl"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Ejecuta el pipeline ETL completo (extract -> transform -> load)."
    )
    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="Omite la extracción desde Apify.",
    )
    parser.add_argument(
        "--skip-transform",
        action="store_true",
        help="Omite la transformación y usa las tablas existentes en data/processed/.",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="Omite la carga a BigQuery.",
    )

    # Opciones que se pasan únicamente a load.py
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida la carga sin conectarse a BigQuery.",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=None,
        help="Subconjunto de tablas para load.py (ej.: --tables reviews themes).",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="ID del proyecto de BigQuery para load.py.",
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="ID del dataset de BigQuery para load.py.",
    )
    return parser.parse_args(argv)


def build_steps(args):
    """Devuelve la lista de pasos a ejecutar según los flags recibidos."""
    steps = []

    if not args.skip_extract:
        steps.append(("Extract", ETL_DIR / "extract.py", []))

    if not args.skip_transform:
        steps.append(("Transform", ETL_DIR / "transform.py", []))

    if not args.skip_load:
        load_args = []
        if args.dry_run:
            load_args.append("--dry-run")
        if args.tables:
            load_args.extend(["--tables", *args.tables])
        if args.project:
            load_args.extend(["--project", args.project])
        if args.dataset:
            load_args.extend(["--dataset", args.dataset])
        steps.append(("Load", ETL_DIR / "load.py", load_args))

    return steps


def run_step(name, script, extra_args):
    """Ejecuta un script ETL y devuelve su código de salida."""
    print(f"\n{'=' * 60}")
    print(f"▶️  {name}: {script.relative_to(PROJECT_ROOT)}")
    print(f"{'=' * 60}")

    if not script.exists():
        print(f"❌ No se encontró el script: {script}")
        return 1

    command = [sys.executable, str(script), *extra_args]
    print(f"$ {' '.join(command)}\n")

    started = time.perf_counter()
    try:
        completed = subprocess.run(command, cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print(f"\n⚠️  {name} interrumpido por el usuario.")
        return 130

    elapsed = time.perf_counter() - started
    if completed.returncode != 0:
        print(f"\n❌ {name} falló con código {completed.returncode} ({elapsed:.1f}s).")
        return completed.returncode

    print(f"\n✅ {name} completado en {elapsed:.1f}s.")
    return 0


def main(argv=None):
    args = parse_args(argv)
    steps = build_steps(args)

    if not steps:
        print("⚠️  No hay pasos para ejecutar: todos fueron omitidos.")
        return 0

    print("🚀 Orquestador ETL")
    print(f"📂 Proyecto: {PROJECT_ROOT}")
    print(f"🧩 Pasos: {' -> '.join(name for name, _, _ in steps)}")

    started = time.perf_counter()
    for name, script, extra_args in steps:
        code = run_step(name, script, extra_args)
        if code != 0:
            print("\n⛔ Pipeline detenido.")
            return code

    elapsed = time.perf_counter() - started
    print(f"\n{'=' * 60}")
    print(f"✨ Pipeline completado en {elapsed:.1f}s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
