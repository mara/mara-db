"""Configuration of database connections"""
import typing

from mara_db import dbs


def databases() -> {str: dbs.DB}:
    """The list of database connections to use, by alias"""
    return {'mara': dbs.PostgreSQLDB(host='localhost', database='mara', user='root')}


def default_timezone() -> str:
    """
    The default timezone to be used for database connections
    See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    """
    return 'Europe/Berlin'


def default_echo_queries() -> bool:
    """
    If queries should be printed on execution by default, if applicable
    """
    return True


def schema_ui_foreign_key_column_regex() -> typing.Pattern:
    """A regex that classifies a table column as being used in a foreign constraint (for coloring missing constraints)"""
    return r'.*_fk$'
