"""Configuration of database connections"""

from sqlalchemy import engine
import typing


def databases() -> typing.Dict[str, engine.Engine]:
    """The list of database connections to use, by alias"""
    return {'mara': engine.create_engine('postgresql+psycopg2://root@localhost/mara')}


def mara_db_alias() -> str:
    """The database alias for mara internal data"""
    return 'mara'
