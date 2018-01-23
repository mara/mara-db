"""Management of sql alchemy sessions and connections"""

import contextlib
import functools

import psycopg2.extensions
import psycopg2
import sqlalchemy
import sqlalchemy.engine
import sqlalchemy.orm
from mara_db import dbs


@functools.singledispatch
def engine(db: object) -> sqlalchemy.engine.Engine:
    """
    Returns a sql alchemy engine for a configured database connection

    Args:
        db: The database to use (either an alias or a `dbs.DB` object

    Returns:
        The generated sqlalchemy engine

    Examples:
        >>>> print(mara_db.sqlalchemy.engine('mara'))
        Engine(postgresql+psycopg2://None@localhost/mara)
    """
    pass

@engine.register(str)
def __(alias:str, **_):
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
    """
    Creates a context that automatically commits or rollbacks an alchemy session
    """
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
    db = dbs.db(alias)
    assert(isinstance(db,dbs.PostgreSQLDB))
    connection = psycopg2.connect(dbname=db.database, user=db.user, password=db.password,
                                  host=db.host, port=db.port) # type: psycopg2.extensions.connection
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


