"""Easy access to MySQL databases via mysql-client"""

import contextlib
import typing

import mara_db.dbs


@contextlib.contextmanager
def mysql_cursor_context(db: typing.Union[str, mara_db.dbs.MysqlDB]) -> 'MySQLdb.cursors.Cursor':
    """Creates a context with a mysql-client cursor for a database alias or database"""
    import MySQLdb.cursors # requires https://github.com/PyMySQL/mysqlclient-python

    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    assert (isinstance(db, mara_db.dbs.MysqlDB))

    cursor = None
    connection = MySQLdb.connect(
        host=db.host, user=db.user, passwd=db.password, db=db.database, port=db.port,
        cursorclass=MySQLdb.cursors.Cursor)
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
