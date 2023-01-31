"""Easy access to postgres databases via psycopg2"""

import contextlib
import typing
from warnings import warn

import mara_db.dbs


@contextlib.contextmanager
def postgres_cursor_context(db: typing.Union[str, mara_db.dbs.PostgreSQLDB]) -> 'psycopg2.extensions.cursor':
    """Creates a context with a psycopg2 cursor for a database alias"""
    warn('Function databricks_cursor_context(db) is deprecated. Please use db.cursor_context() instead.')

    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    assert (isinstance(db, mara_db.dbs.PostgreSQLDB))

    return db.cursor_context()
