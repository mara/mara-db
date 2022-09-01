import pytest

def test_my():
    import mara_db.dbs

    db = mara_db.dbs.SqlcmdSQLServerDB(host='ABC123', user='A', password="a", trust_server_certificate=True)

    odbc = db.sqlalchemy_url

    print(odbc)

    assert False
