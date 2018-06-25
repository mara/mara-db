"""Configuration of database connections"""
import typing

from mara_config import declare_config
from mara_db import dbs


# The reference must be a string or this results in a import cycle :-(
@declare_config()
def databases() -> {str: 'mara_db.dbs.DB'}:
    """The list of database connections to use, by alias"""
    return {'mara': dbs.PostgreSQLDB(host='localhost', database='mara', user='root')}


@declare_config()
def default_timezone() -> str:
    """
    The default timezone to be used for database connections
    See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    """
    return 'Europe/Berlin'


@declare_config()
def schema_ui_foreign_key_column_regex() -> typing.Pattern:
    """A regex that classifies a table column as being used in a foreign constraint (for coloring missing constraints)"""
    return r'.*_fk$'
