"""Configuration of database connections"""
from mara_db import dbs
import typing


def databases() -> {str: dbs.DB}:
    """The list of database connections to use, by alias"""
    return {'mara': dbs.PostgreSQLDB(host='localhost', database='mara', user='root')}


def mara_db_alias() -> str:
    """The database alias for mara internal data"""
    return 'mara'


def default_timezone() -> str:
    """
    The default timezone to be used for database connections
    See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    """
    return 'Europe/Berlin'


def schema_ui_foreign_key_column_regex() -> typing.Pattern:
    """A regex that classifies a table column as being used in a foreign constraint (for coloring missing constraints)"""
    return r'.*_fk$'