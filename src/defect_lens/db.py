import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


def _open(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


@contextmanager
def connect(path: Path) -> Generator[sqlite3.Connection]:
    connection = _open(path)
    try:
        yield connection
    finally:
        connection.close()


def migrate(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            connection.executescript(
                (Path(__file__).parent / "migrations/001_initial.sql").read_text()
            )
        elif version != 1:
            raise ValueError("Unsupported database schema")


@contextmanager
def transaction(path: Path) -> Generator[sqlite3.Connection]:
    connection = _open(path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()
