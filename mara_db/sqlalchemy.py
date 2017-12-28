"""Management of sql alchemy sessions and connections"""

import contextlib
import functools

import psycopg2.extensions
import sqlalchemy
import sqlalchemy.engine
import sqlalchemy.orm
from mara_db import dbs


@functools.singledispatch
def engine(alias: str) -> sqlalchemy.engine.Engine:
    """Returns a database engine by alias"""
    return engine(dbs.db(alias))


@engine.register(dbs.DB)
def __(db, **_):
    raise NotImplementedError(f'Please implement function engine for {db.__class__.__name__}')


@engine.register(dbs.PostgreSQLDB)
def __(db: dbs.PostgreSQLDB):
    return sqlalchemy.create_engine(
        f'postgresql+psycopg2://{db.user}{":"+db.password if db.password else ""}@{db.host}/{db.database}')


@contextlib.contextmanager
def session_context(alias: str) -> sqlalchemy.orm.Session:
    """Creates a context with a sql alchemy session for a database alias """
    session = sqlalchemy.orm.sessionmaker(bind=engine(alias))()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


@contextlib.contextmanager
def postgres_cursor_context(alias: str) -> psycopg2.extensions.cursor:
    """Creates a context with a psycopg2 cursor for a database alias"""
    _engine = engine(alias)
    assert (_engine.dialect.name == 'postgresql')
    connection = _engine.raw_connection().connection  # type: psycopg2.extensions.connection
    cursor = connection.cursor()  # type: psycopg2.extensions.cursor
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()
