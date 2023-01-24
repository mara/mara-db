"""Easy access to postgres databases via psycopg2"""

import contextlib
import typing

import mara_db.dbs


@contextlib.contextmanager
def postgres_cursor_context(db: typing.Union[str, mara_db.dbs.PostgreSQLDB]) -> 'psycopg2.extensions.cursor':
    """Creates a context with a psycopg2 cursor for a database alias"""
    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    assert (isinstance(db, mara_db.dbs.PostgreSQLDB))

    return db.cursor_context()
