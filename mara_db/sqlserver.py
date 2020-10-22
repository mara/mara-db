"""Easy access to SQLServer databases via pyodbc-client"""

import contextlib
import typing

import mara_db.dbs


@contextlib.contextmanager
def sqlserver_cursor_context(db: typing.Union[str, mara_db.dbs.SQLServerDB]) -> 'pyodbc.Cursor':
    """Creates a context with a pyodbc-client cursor for a database alias or database"""
    import pyodbc # requires https://github.com/mkleehammer/pyodbc/wiki/Install

    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    assert (isinstance(db, mara_db.dbs.SQLServerDB))

    cursor = None

    server = db.host
    if db.port: # connecting via TCP/IP port
        server = f"{server},{db.port}"

    connection = pyodbc.connect(f"DRIVER={{{db.odbc_driver}}};SERVER={server};DATABASE={db.database};UID={db.user};PWD={db.password}")
    try:
        cursor = connection.cursor()
        yield cursor
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
    finally:
        cursor.close()
        connection.close()
