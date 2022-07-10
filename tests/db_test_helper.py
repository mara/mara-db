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

def _test_sqlalchemy(db):
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
        assert conn.scalar(select([1])) == 1
