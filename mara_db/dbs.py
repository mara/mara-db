"""Management sessions and connections"""

from contextlib import contextmanager
from functools import lru_cache

from mara_db import config
from sqlalchemy import engine
from sqlalchemy import orm


@lru_cache(maxsize=None)
def engine(alias) -> engine.Engine:
    """Returns a database engine by alias"""
    databases = config.databases()
    if alias not in databases:
        raise KeyError('database alias "{}" not configured' % alias)
    return databases[alias]


@contextmanager
def session_context(alias: str) -> orm.Session:
    """Creates a context with a sql alchemy session for a database alias """
    session = orm.sessionmaker(bind=engine(alias))()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
