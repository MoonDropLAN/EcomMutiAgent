from pathlib import Path
import sqlite3

from app.db.database import connect, init_db
from app.db.seed import seed_demo_data


def ensure_database_ready(database_path: Path) -> sqlite3.Connection:
    conn = connect(database_path)
    init_db(conn, Path("app/db/schema.sql"))
    seed_demo_data(conn)
    return conn