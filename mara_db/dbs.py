"""Abstract definition of database connections"""

import functools
import pathlib

from mara_db import config


@functools.lru_cache(maxsize=None)
def db(alias):
    """Returns a database configuration by alias"""
    databases = config.databases()
    if alias not in databases:
        raise KeyError(f'database alias "{alias}" not configured')
    return databases[alias]


class DB:
    """Generic database connection definition"""

    def __repr__(self) -> str:
        return (f'<{self.__class__.__name__}: '
                + ', '.join([f'{var}={"*****" if var =="password" else getattr(self,var)}'
                             for var in vars(self) if getattr(self, var)])
                + '>')


class PostgreSQLDB(DB):
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None):
        self.host = host
        self.database = database
        self.port = port
        self.user = user
        self.password = password


class RedshiftDB(PostgreSQLDB):
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None):
        super(RedshiftDB, self).__init__(host, port, database, user, password)


class MysqlDB(DB):
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None, ssl: bool = None, charset: str = None):
        self.host = host
        self.database = database
        self.port = port
        self.user = user
        self.password = password
        self.ssl = ssl
        self.charset = charset


class SQLServerDB(DB):
    def __init__(self, host: str = None, database: str = None, user: str = None, password: str = None):
        self.host = host
        self.database = database
        self.user = user
        self.password = password


class OracleDB(DB):
    def __init__(self, host: str = None, port: int = 0, endpoint: str = None, user: str = None, password: str = None):
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.user = user
        self.password = password


class SQLiteDB(DB):
    def __init__(self, file_name: pathlib.Path) -> None:
        self.file_name = file_name
