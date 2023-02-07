"""Easy access to SQLServer databases via pyodbc-client"""

import contextlib
import typing
from warnings import warn

import mara_db.dbs


@contextlib.contextmanager
def sqlserver_cursor_context(db: typing.Union[str, mara_db.dbs.SQLServerDB]) -> 'pyodbc.Cursor':
    """Creates a context with a pyodbc-client cursor for a database alias or database"""
    warn('Function sqlserver_cursor_context(db) is deprecated. Please use db.cursor_context() instead.')

    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    assert (isinstance(db, mara_db.dbs.SQLServerDB))

    return mara_db.dbs.cursor_context(db)
