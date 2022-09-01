"""Easy access to Databricks databases via databricks-sql-connector"""

import contextlib
import typing

import mara_db.dbs


@contextlib.contextmanager
def databricks_cursor_context(db: typing.Union[str, mara_db.dbs.DatabricksDB]) \
        -> 'databricks.sql.client.Cursor':
    from databricks_dbapi import odbc

    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    assert (isinstance(db, mara_db.dbs.DatabricksDB))

    connection = odbc.connect(
        host=db.host,
        http_path=db.http_path,
        token=db.access_token,
        driver_path=db.odbc_driver_path)

    cursor = connection.cursor()  # type: databricks.sql.client.Cursor
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.close()
        raise e
