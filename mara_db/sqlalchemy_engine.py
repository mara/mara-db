import functools

import sqlalchemy.engine
import sqlalchemy.sql.schema

import mara_db.dbs


@functools.singledispatch
def engine(db: object) -> sqlalchemy.engine.Engine:
    """
    Returns a sql alchemy engine for a configured database connection

    Args:
        db: The database to use (either an alias or a `dbs.DB` object

    Returns:
        The generated sqlalchemy engine

    Examples:
        >>> print(engine('mara'))
        Engine(postgresql+psycopg2://None@localhost/mara)
    """
    pass


@engine.register(str)
def __(alias: str, **_):
    return engine(mara_db.dbs.db(alias))


@engine.register(mara_db.dbs.DB)
def __(db, **_):
    raise NotImplementedError(f'Please implement function engine for {db.__class__.__name__}')


@engine.register(mara_db.dbs.PostgreSQLDB)
def __(db: mara_db.dbs.PostgreSQLDB):
    return sqlalchemy.create_engine(
        f'postgresql+psycopg2://{db.user}{":" + db.password if db.password else ""}@{db.host}'
        + f'{":" + str(db.port) if db.port else ""}/{db.database}')


@engine.register(mara_db.dbs.SQLiteDB)
def __(db: mara_db.dbs.SQLiteDB):
    return sqlalchemy.create_engine(f'sqlite:///{db.file_name}')
