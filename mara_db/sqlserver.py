"""Easy access to SQLServer databases via pyodbc-client"""

import contextlib
import typing

import mara_db.dbs


@contextlib.contextmanager
def sqlserver_cursor_context(db: typing.Union[str, mara_db.dbs.SQLServerDB]) -> 'pyodbc.Cursor':
    """Creates a context with a pyodbc-client cursor for a database alias or database"""
    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    assert (isinstance(db, mara_db.dbs.SQLServerDB))

    return db.cursor_context()
