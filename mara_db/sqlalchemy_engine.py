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
def __(db: mara_db.dbs.DB, **_):
    return sqlalchemy.create_engine(db.sqlalchemy_url)


@engine.register(mara_db.dbs.BigQueryDB)
def __(db: mara_db.dbs.BigQueryDB):
    # creates bigquery dialect
    url = db.sqlalchemy_url

    return sqlalchemy.create_engine(url,
                                    credentials_path=db.service_account_json_file_name,
                                    location=db.location)
