"""
For SQL Server we use a special configuration:
- we use a generic 'SQLServerDB' config instance which instanciates the default provider
- we support two different connection modes: via sqsh (SqshSQLServerDB) or via sqlcmd (SqlcmdSQLServerDB)

To make sure that the config is properly implemented, the following unit tests are added.
"""
import functools

from mara_db import dbs


@functools.singledispatch
def check_dbconfig(db) -> str:
    """A test functiontools overloading"""
    raise Exception("Not expected to end up here in the test")

@check_dbconfig.register(dbs.SQLServerDB)
def __(db: dbs.SQLServerDB) -> str:
    return 'undefined'

@check_dbconfig.register(dbs.SqlcmdSQLServerDB)
def __(db: dbs.SqlcmdSQLServerDB) -> str:
    return 'sqlcmd'

@check_dbconfig.register(dbs.SqshSQLServerDB)
def __(db: dbs.SqshSQLServerDB) -> str:
    return 'sqsh'


def test_mssql_dbconfig():
    """Test the behavior of instancing SQLServerDB"""

    sqlcmd_db = dbs.SqlcmdSQLServerDB(host="localhost")
    sqsh_db = dbs.SqshSQLServerDB(host="localhost")
    default_db = dbs.SQLServerDB(host="localhost")

    # check if singledispatch uses the right class
    assert check_dbconfig(sqlcmd_db) == "sqlcmd"
    assert check_dbconfig(sqsh_db) == "sqsh"
    assert check_dbconfig(default_db) in ["sqsh", "sqlcmd"]

    # check if all db config instances are detected via 'isinstance(..., SQLServerDB)'
    assert isinstance(sqlcmd_db, dbs.SQLServerDB)
    assert isinstance(sqsh_db, dbs.SQLServerDB)
    assert isinstance(default_db, dbs.SQLServerDB)

    # check that we get 'SqlcmdSQLServerDB' or 'SqshSQLServerDB' when instantiating 'dbs.SQLServerDB(...)'
    assert isinstance(default_db, dbs.SqlcmdSQLServerDB) or isinstance(default_db, dbs.SqshSQLServerDB)
