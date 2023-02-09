"""Easy access to postgres databases via psycopg2"""

import typing
from warnings import warn

import mara_db.dbs


def postgres_cursor_context(db: typing.Union[str, mara_db.dbs.PostgreSQLDB]) -> 'psycopg2.extensions.cursor':
    """Creates a context with a psycopg2 cursor for a database alias"""
    warn('Function postgres_cursor_context(db) is deprecated. Please use mara_db.dbs.cursor_context(db) instead.')

    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    assert (isinstance(db, mara_db.dbs.PostgreSQLDB))

    return mara_db.dbs.cursor_context(db)
