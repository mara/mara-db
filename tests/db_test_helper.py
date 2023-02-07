import sqlalchemy
from mara_db import dbs


def db_is_responsive(db: dbs.DB) -> bool:
    """Returns True when the DB is available on the given port, otherwise False"""
    engine = sqlalchemy.create_engine(db.sqlalchemy_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            return True
    except:
        return False


def db_replace_placeholders(db: dbs.DB, docker_ip: str, docker_port: int) -> dbs.DB:
    """Replaces the internal placeholders with the docker ip and docker port"""
    if db.host == 'DOCKER_IP':
        db.host = docker_ip
    if db.port == -1:
        db.port = docker_port
    return db


"""
Basic tests which can be used for different DB engines.
"""

def _test_sqlalchemy(db: dbs.DB):
    """
    A simple test to check if the SQLAlchemy connection works
    """
    from mara_db.sqlalchemy_engine import engine
    from sqlalchemy import select

    eng = engine(db)

    with eng.connect() as conn:
        # run a SELECT 1.   use a core select() so that
        # the SELECT of a scalar value without a table is
        # appropriately formatted for the backend
        assert conn.scalar(select(1)) == 1

def _test_connect(db: dbs.DB):
    connection = dbs.connect(db)
    cursor = connection.cursor()
    try:
        cursor.execute('SELECT 1')
        row = cursor.fetchone()
        assert row[0] == 1
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()

def _test_cursor_context(db: dbs.DB):
    with dbs.cursor_context(db) as cursor:
        cursor.execute('SELECT 1')
        row = cursor.fetchone()
        assert row[0] == 1
