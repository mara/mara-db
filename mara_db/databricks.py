"""Easy access to Databricks databases via databricks-sql-connector"""

import typing
from warnings import warn

import mara_db.dbs


def databricks_cursor_context(db: typing.Union[str, mara_db.dbs.DatabricksDB]) \
        -> 'databricks.sql.client.Cursor':
    warn('Function databricks_cursor_context(db) is deprecated. Please use mara_db.dbs.cursor_context(db) instead.',
         category=DeprecationWarning)

    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    assert (isinstance(db, mara_db.dbs.DatabricksDB))

    return mara_db.dbs.cursor_context(db)
