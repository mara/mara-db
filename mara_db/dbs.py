"""Management sessions and connections"""

import contextlib
import functools

import psycopg2.extensions
import sqlalchemy.engine
import sqlalchemy.engine.url
import sqlalchemy.orm
from mara_db import config
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.engine.default import DefaultDialect


def engine(alias: str) -> sqlalchemy.engine.Engine:
    """Returns a database engine by alias"""
    database_urls = config.database_urls()
    if alias not in database_urls:
        raise KeyError(f'database alias "{alias}" not configured')
    return sqlalchemy.engine.create_engine(database_urls[alias])


@contextlib.contextmanager
def session_context(alias: str) -> sqlalchemy.orm.Session:
    """Creates a context with a sql alchemy session for a database alias """
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
    _engine = engine(alias)
    assert (_engine.dialect.name == 'postgresql')
    connection = _engine.raw_connection().connection  # type: psycopg2.extensions.connection
    cursor = connection.cursor()  # type: psycopg2.extensions.cursor
    try:
        yield cursor
        connection.commit()
    except:
        connection.rollback()
    finally:
        cursor.close()
        connection.close()


@functools.singledispatch
def client_command(alias: str, timezone: str = None) -> str:
    """
    Returns a command for accessing the database from the command line

    Args:
        alias: The database alias of the
        timezone: Sets the timezone of the client, if applicable

    Returns:
        A shell command string

    Example:
        >>> print(client_command('mara', 'Europe/Berlin'))
        PGTZ=Europe/Berlin psql --username=root --host=localhost --client-min-messages=warning --no-psqlrc --set ON_ERROR_STOP=on mara


        >>> print(client_command(sqlalchemy.engine.create_engine('postgresql+psycopg2://root@localhost/mara')))
        psql --username=root --host=localhost --client-min-messages=warning --no-psqlrc --set ON_ERROR_STOP=on mara

    """
    return client_command(engine(alias), timezone=timezone)


@client_command.register(sqlalchemy.engine.Engine)
def __(engine: sqlalchemy.engine.Engine, timezone: str = None):
    return client_command(engine.dialect, engine=engine, timezone=timezone)


@client_command.register(DefaultDialect)
def __(dialect, **_):
    raise NotImplementedError(f'Please implement function client_command for dialect {dialect.__class__.__name__}')


@client_command.register(PGDialect)
def __(_, engine: sqlalchemy.engine.Engine = None, timezone: str = None):
    assert (engine)
    return ((f'PGTZ={timezone} ' if timezone else '')
            + (f'PGPASSWORD={engine.url.password} ' if engine.url.password else '')
            + 'PGOPTIONS=--client-min-messages=warning psql'
            + (f' --username={engine.url.username}' if engine.url.username else '')
            + (f' --host={engine.url.host}' if engine.url.host else '')
            + (f' --port={engine.url.port}' if engine.url.port else '')
            + ' --no-psqlrc --set ON_ERROR_STOP=on '
            + (engine.url.database or ''))


@functools.singledispatch
def copy_from_stdin_command(alias: str, target_table: str,
                            sql_delimiter_char: str = None, quote_char: str = None,
                            null_value_string: str = None, timezone: str = None):
    return copy_from_stdin_command(engine(alias), target_table=target_table,
                                   sql_delimiter_char=sql_delimiter_char, quote_char=quote_char,
                                   null_value_string=null_value_string, timezone=timezone)


@copy_from_stdin_command.register(sqlalchemy.engine.Engine)
def __(engine: sqlalchemy.engine.Engine, target_table: str,
       sql_delimiter_char: str = None, quote_char: str = None,
       null_value_string: str = None, timezone: str = None):
    return copy_from_stdin_command(engine.dialect, engine=engine, target_table=target_table,
                                   sql_delimiter_char=sql_delimiter_char, quote_char=quote_char,
                                   null_value_string=null_value_string, timezone=timezone)


@copy_from_stdin_command.register(DefaultDialect)
def __(dialect, **kwargs):
    raise NotImplementedError(
        f'Please implement function copy_from_stdin_command for dialect {dialect.__class__.__name__}')


@copy_from_stdin_command.register(PGDialect)
def __(_, engine: sqlalchemy.engine.Engine, target_table: str,
       sql_delimiter_char: str = None, quote_char: str = None,
       null_value_string: str = None, timezone: str = None):
    sql = f'COPY {target_table} FROM STDIN WITH CSV'
    if sql_delimiter_char != None:
        sql += f" DELIMITER AS '{sql_delimiter_char}'"
    if null_value_string != None:
        sql += f" NULL AS '{null_value_string}'"
    if quote_char != None:
        sql += f" QUOTE AS '{quote_char}'"

    return f'{client_command(engine)} \\\n      --command="{sql}"'
