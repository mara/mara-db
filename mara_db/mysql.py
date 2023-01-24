"""Easy access to MySQL databases via mysql-client"""

import contextlib
import typing
from warnings import warn

import mara_db.dbs


@contextlib.contextmanager
def mysql_cursor_context(db: typing.Union[str, mara_db.dbs.MysqlDB]) -> 'MySQLdb.cursors.Cursor':
    """Creates a context with a mysql-client cursor for a database alias or database"""
    warn('Function mysql_cursor_context(db) is deprecated. Please use db.cursor_context() instead.')

    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    assert (isinstance(db, mara_db.dbs.MysqlDB))

    return db.cursor_context()
