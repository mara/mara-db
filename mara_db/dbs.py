"""Abstract definition of database connections"""

import functools

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

    def copy_to_stdout_format(self) -> dict:
        """Dict with the formatting options to which the copy_to_stdout_command adheres

        The formatting options must be the valid value for the implementation
        of copy_to_stdout_command for this type of DB.

        The dict must contain the following keys and the values should be
        list of possible values for that option.

        csv_format: [False, True] -> whether the DB can output CSV
        skip_header: [False, True] -> whether this DB can skip outputting headers
        delimiter_char: [str] -> possible delimiter chars. List all of [',', ';','|'] which apply
        quote_char: [str] -> possible quote chars. List all of ['\'', '"'] which apply
        null_value_string: [str] -> possible NULL value representations. List all of ['NULL', ''] which apply

        """
        raise NotImplementedError()

    def possible_copy_from_stdin_formats(self) -> dict:
        """Dict with possible (CSV) formatting options to be passed to copy_from_stdin_command

        The formatting options must be valid values for the implementation
        of copy_to_stdout_command for this type of DB.

        The dict must contain the following keys and the values should be
        list of possible values for that option. The default value should be first, so that
        is chosen on the input side

        csv_format: [False, True] -> whether the DB can output CSV
        skip_header: [False, True] -> whether this DB can skip outputting headers
        delimiter_char: [str] -> possible delimiter chars. List all of [',', ';','|','\t'] which apply
        quote_char: [str] -> possible quote chars. List all of ['\'', '"'] which apply
        null_value_string: [str] -> possible NULL value representations. List all of ['NULL', '', '\\N'] which apply
        timezone: [True, False]-> whether or not a Timezone can be set

        """
        raise NotImplementedError()

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

    def copy_to_stdout_format(self) -> dict:
        """Dict with formatting options for the output of the copy_to_stdout_command"""
        return {
            'csv_format': [True],
            'skip_header': [False],
            'delimiter_char' : ['\t'],
            'quote_char' : ['"'],
            'null_value_string': ['\\N']
        }

    def possible_copy_from_stdin_formats(self) -> dict:
        """Dict with possible formatting options to be passed to copy_from_stdin_command"""
        return {
            'csv_format': [True, False],
            'skip_header': [True, False],
            'delimiter_char': [',', ';', '|','\t'],
            'quote_char': ['\'', '"'],
            'null_value_string': ['NULL', '', '\\N']
        }


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

    def copy_to_stdout_format(self) -> dict:
        """Dict with formatting options for the output of the copy_to_stdout_command"""
        return {
            'csv_format': [False],
            'skip_header': [False],
            'delimiter_char': ['\t'],
            'quote_char': ['"'],
            'null_value_string': ['NULL']
        }


class SQLServerDB(DB):
    def __init__(self, host: str = None, database: str = None, user: str = None, password: str = None):
        self.host = host
        self.database = database
        self.user = user
        self.password = password

    def copy_to_stdout_format(self) -> dict:
        """Dict with formatting options for the output of the copy_to_stdout_command"""
        return {
            'csv_format': [True],
            'skip_header': [True],
            'delimiter_char': [','],
            'quote_char': ['"'],
            'null_value_string': ['']
        }
