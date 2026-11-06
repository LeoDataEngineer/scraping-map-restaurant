"""Carga las 6 tablas analíticas del proyecto en Google BigQuery.

Lee los CSV generados por `src/etl/transform.py` en `data/processed/` y los reemplaza
en el dataset configurado (WRITE_TRUNCATE). 

Uso:
    python src/etl/load.py                       # carga las 6 tablas
    python src/etl/load.py --dry-run             # valida los CSV sin tocar BigQuery
    python src/etl/load.py --tables reviews themes
"""

import argparse
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Evitar errores de codificación con emojis en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CREDENTIALS_PATH = PROJECT_ROOT / "credentials" / "service_account.json"

# Configuración por defecto
PROJECT_ID = "midyear-lattice-513814-k4"
DATASET_ID = "proyecto_google_map"

# Las 6 tablas que produce transform.py, en orden de carga (dimensiones primero)
TABLES = [
    "restaurants",
    "reviews",
    "monthly_trend",
    "themes",
    "occupancy",
    "competitors",
]

# Añadir una columna de auditoría con la fecha/hora de carga
ADD_LOADED_AT = True
LOADED_AT_COLUMN = "loaded_at"


def read_table(table_name, directory=PROCESSED_DIR):
    """Lee un CSV de processed y devuelve un DataFrame listo para cargar."""
    csv_path = Path(directory) / f"{table_name}.csv"

    if not csv_path.exists():
        print(f"⚠️ No se encontró '{csv_path}'. Se omite la tabla '{table_name}'.")
        return None

    try:
        df = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError:
        print(f"⚠️ '{csv_path.name}' está vacío. Se omite.")
        return None

    if df.empty:
        print(f"⚠️ '{csv_path.name}' no tiene filas. Se omite.")
        return None

    if ADD_LOADED_AT:
        df[LOADED_AT_COLUMN] = datetime.now(timezone.utc).replace(tzinfo=None)

    return df


def table_summary(table_name, df):
    """Resumen legible de una tabla antes de cargarla."""
    rows, columns = df.shape
    restaurants = []
    if "restaurant_name" in df.columns:
        restaurants = sorted(str(r) for r in df["restaurant_name"].dropna().unique())

    lines = [f"📦 {table_name}: {rows:,} filas × {columns} columnas"]
    if restaurants:
        lines.append(f"   Restaurantes: {', '.join(restaurants)}")
    if table_name == "restaurants" and "generated_at" in df.columns:
        lines.append(f"   Generado: {df['generated_at'].iloc[0]}")
    return "\n".join(lines)


def get_client(project_id=PROJECT_ID):
    """Crea el cliente de BigQuery (importación y credenciales diferidas)."""
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"❌ No se encontró el archivo de credenciales '{CREDENTIALS_PATH}'.\n"
            "   Coloca tu service account en esa ruta o ejecuta 'python src/etl/load.py --dry-run'."
        )

    from google.cloud import bigquery
    from google.oauth2 import service_account

    credentials = service_account.Credentials.from_service_account_file(str(CREDENTIALS_PATH))
    return bigquery.Client(credentials=credentials, project=project_id)


def ensure_dataset(client, project_id, dataset_id):
    """Crea el dataset si no existe."""
    from google.api_core.exceptions import NotFound

    dataset_ref = f"{project_id}.{dataset_id}"
    try:
        client.get_dataset(dataset_ref)
    except NotFound:
        client.create_dataset(dataset_ref)
        print(f"🆕 Dataset creado: '{dataset_ref}'")


def load_table(client, table_name, df, project_id=PROJECT_ID, dataset_id=DATASET_ID):
    """Carga un DataFrame en BigQuery reemplazando la tabla destino."""
    from google.cloud import bigquery

    table_id = f"{project_id}.{dataset_id}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        allow_quoted_newlines=True,
        max_bad_records=0,
        encoding="UTF-8",
    )

    # CSV temporal para no modificar data/processed
    temp_file = tempfile.NamedTemporaryFile(
        "w", suffix=".csv", delete=False, encoding="utf-8", newline=""
    )
    temp_file.close()
    temp_path = Path(temp_file.name)

    try:
        df.to_csv(temp_path, index=False, encoding="utf-8")
        with open(temp_path, "rb") as source_file:
            job = client.load_table_from_file(source_file, table_id, job_config=job_config)
        job.result()
    finally:
        temp_path.unlink(missing_ok=True)

    print(f"✅ '{table_name}' cargada en '{table_id}' ({len(df):,} filas).")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Carga las 6 tablas de data/processed/ en BigQuery."
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        choices=TABLES,
        default=TABLES,
        metavar="TABLA",
        help=f"Subconjunto de tablas a cargar (por defecto: todas). Opciones: {', '.join(TABLES)}",
    )
    parser.add_argument("--project", default=PROJECT_ID, help="ID del proyecto de BigQuery.")
    parser.add_argument("--dataset", default=DATASET_ID, help="ID del dataset de BigQuery.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida los CSV y muestra el resumen sin conectarse a BigQuery.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    print("🚀 Fase de carga (Load) a Google BigQuery")
    print(f"📂 Origen: {PROCESSED_DIR}")
    print(f"🎯 Destino: {args.project}.{args.dataset}\n")

    frames = {}
    for table_name in args.tables:
        df = read_table(table_name)
        if df is None:
            continue
        frames[table_name] = df
        print(table_summary(table_name, df))

    if not frames:
        print("\n❌ No hay tablas para cargar. Ejecuta 'python src/etl/transform.py' primero.")
        return 1

    if args.dry_run:
        print("\n✅ Dry run correcto: las tablas se leyeron bien. No se contactó BigQuery.")
        print(f"   Tablas listas: {', '.join(frames)}")
        return 0

    try:
        client = get_client(args.project)
    except FileNotFoundError as error:
        print(f"\n{error}")
        return 1

    ensure_dataset(client, args.project, args.dataset)

    for table_name, df in frames.items():
        load_table(client, table_name, df, project_id=args.project, dataset_id=args.dataset)

    print("\n✨ Carga finalizada.")
    print(f"📊 Revisa las {len(frames)} tablas en: {args.project}.{args.dataset}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
