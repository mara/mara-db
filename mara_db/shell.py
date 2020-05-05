"""
Shell command generation for
- running queries in databases via their command line clients
- copying data from, into and between databases
"""

import shlex
import sys
from functools import singledispatch

from mara_db import dbs, config
from multimethod import multidispatch


@singledispatch
def query_command(db: object, timezone: str = None, echo_queries: bool = None) -> str:
    """
    Creates a shell command that receives a sql query from stdin and executes it

    Args:
        db: The database in which to run the query (either an alias or a `dbs.DB` object
        timezone: Sets the timezone of the client, if applicable
        echo_queries: Whether the client should print executed queries, if applicable

    Returns:
        A shell command string

    Example:
        >>> print(query_command('mara', 'America/New_York'))
        PGTZ=America/New_York PGOPTIONS=--client-min-messages=warning psql --username=root --host=localhost \
            --echo-all --no-psqlrc --set ON_ERROR_STOP=on mara


        >>> print(query_command(dbs.MysqlDB(host='localhost', database='test')))
        mysql --default-character-set=utf8mb4 --host=localhost test
    """
    raise NotImplementedError(f'Please implement query_command for type "{db.__class__.__name__}"')


@query_command.register(str)
def __(alias: str, timezone: str = None, echo_queries: bool = None):
    return query_command(dbs.db(alias), timezone=timezone, echo_queries=echo_queries)


@query_command.register(dbs.PostgreSQLDB)
def __(db: dbs.PostgreSQLDB, timezone: str = None, echo_queries: bool = None):
    if echo_queries is None:
        echo_queries = True

    return (f'PGTZ={timezone or config.default_timezone()} '
            + (f"PGPASSWORD='{db.password}' " if db.password else '')
            + (f'PGSSLMODE={db.sslmode} ' if db.sslmode else '')
            + (f'PGSSLROOTCERT={db.sslrootcert} ' if db.sslrootcert else '')
            + (f'PGSSLCERT={db.sslcert} ' if db.sslcert else '')
            + (f'PGSSLKEY={db.sslkey} ' if db.sslkey else '')
            + 'PGOPTIONS=--client-min-messages=warning psql'
            + (f' --username={db.user}' if db.user else '')
            + (f' --host={db.host}' if db.host else '')
            + (f' --port={db.port}' if db.port else '')
            + (' --echo-all' if echo_queries else ' ')
            + ' --no-psqlrc --set ON_ERROR_STOP=on '
            + (db.database or ''))


@query_command.register(dbs.RedshiftDB)
def __(db: dbs.RedshiftDB, timezone: str = None, echo_queries: bool = None):
    if echo_queries is None:
        echo_queries = True

    return (f'PGTZ={timezone or config.default_timezone()} '
            + (f"PGPASSWORD='{db.password}' " if db.password else '')
            + ' psql'
            + (f' --username={db.user}' if db.user else '')
            + (f' --host={db.host}' if db.host else '')
            + (f' --port={db.port}' if db.port else '')
            + (' --echo-all' if echo_queries else ' ')
            + ' --no-psqlrc --set ON_ERROR_STOP=on '
            + (db.database or ''))


@query_command.register(dbs.BigQueryDB)
def __(db: dbs.BigQueryDB, timezone: str = None, echo_queries: bool = None):
    echo_queries = None
    assert all(v is None for v in [timezone, echo_queries]), f"unimplemented parameter for BigQueryDB"

    return ('bq query'
            + (f' --use_legacy_sql=' + ('true' if db.use_legacy_sql else 'false'))
            + ' --quiet --headless -n=1000000000 ')


@query_command.register(dbs.MysqlDB)
def __(db: dbs.MysqlDB, timezone: str = None, echo_queries: bool = None):
    assert all(v is None for v in [timezone, echo_queries]), "unimplemented parameter for MysqlDB"
    return ((f"MYSQL_PWD='{db.password}' " if db.password else '')
            + 'mysql '
            + (f' --user={db.user}' if db.user else '')
            + (f' --host={db.host}' if db.host else '')
            + (f' --port={db.port}' if db.port else '')
            + (' --ssl' if db.ssl else '')
            + (f' {db.database}' if db.database else ''))


@query_command.register(dbs.SQLServerDB)
def __(db: dbs.SQLServerDB, timezone: str = None, echo_queries: bool = None):
    assert all(v is None for v in [timezone]), "unimplemented parameter for SQLServerDB"

    if echo_queries is None:
        echo_queries = True

    # sqsh does not do anything when a statement is not terminated by a ';', add one to be sure
    command = "(cat && echo ';') \\\n  | "
    command += "(cat && echo ';\n\go') \\\n  | "

    return (command + 'sqsh -a 1 -d 0 -f 10'
            + (f' -U {db.user}' if db.user else '')
            + (f' -P {db.password}' if db.password else '')
            + (f' -S {db.host}' if db.host else '')
            + (f' -D {db.database}' if db.database else '')
            + (f' -e' if echo_queries else ''))


@query_command.register(dbs.OracleDB)
def __(db: dbs.OracleDB, timezone: str = None, echo_queries: bool = None):
    assert all(v is None for v in [timezone, echo_queries]), "unimplemented parameter for OracleDB"

    # sqlplus does not do anything when a statement is not terminated by a ';', add one to be sure
    return (  # Oracle needs a semicolon at the end, with no newlines before
        # Remove all trailing whitespace and then add a semicolon if not there yet
            shlex.quote(sys.executable)
            + ''' -c "import sys; sql = sys.stdin.read().strip(); sql = sql + ';' if not sql[-1]==';' else sql; print(sql)" '''
            + ' \\\n  | sqlplus64 -s '
            + f'{db.user}/{db.password}@{db.host}:{db.port or 1521}/{db.endpoint}')


@query_command.register(dbs.SQLiteDB)
def __(db: dbs.SQLiteDB, timezone: str = None, echo_queries: bool = None):
    assert all(v is None for v in [timezone, echo_queries]), "unimplemented parameter for SQLiteDB"

    # sqlite does not complain if a file does not exist. Therefore check file existence first
    file_name = shlex.quote(str(db.file_name))
    return f'(test -f {file_name} && cat || >&2 echo {file_name} not found) \\\n' \
           + '  | sqlite3 -bail ' + shlex.quote(str(db.file_name))


# -------------------------------


@singledispatch
def copy_to_stdout_command(db: object,
                           header: bool = None,
                           footer: bool = None,
                           delimiter_char: str = None,
                           csv_format: bool = None) -> str:
    """
    Creates a shell command that receives a query from stdin, executes it and writes the output to stdout

    Args:
        db: The database in which to run the query (either an alias or a `dbs.DB` object
        header: Whether a csv header with the column name(s) will be included or not.
            No header, by default. (not implemented in sqsh for SQLServerDB)
        footer: Whether a footer will be included or not. False by default. (Only implemented for PostgreSQLDB)
        delimiter_char: str to delimit the fields in one row. Default: tab character
        csv_format: Double quote 'difficult' strings (Only implemented for PostgreSQLDB)

    Returns:
        The composed shell command

    Example:
        >>> print(copy_to_stdout_command(dbs.PostgreSQLDB(host='localhost', database='test')))
        PGTZ=Europe/Berlin PGOPTIONS=--client-min-messages=warning psql --host=localhost  --no-psqlrc --set ON_ERROR_STOP=on test --tuples-only --no-align --field-separator='	' \
            | grep -a -v -e '^$'
    """
    raise NotImplementedError(f'Please implement function copy_to_stdout_command for type "{db.__class__.__name__}"')


@copy_to_stdout_command.register(str)
def __(alias: str, header: bool = None, footer: bool = None, delimiter_char: str = None, csv_format: bool = None):
    return copy_to_stdout_command(dbs.db(alias), header=header, footer=footer,
                                  delimiter_char=delimiter_char, csv_format=csv_format)


@copy_to_stdout_command.register(dbs.PostgreSQLDB)
def __(db: dbs.PostgreSQLDB, header: bool = None, footer: bool = None,
       delimiter_char: str = None, csv_format: bool = None):
    if header is None:
        header = False

    if footer is None:
        footer = False

    if delimiter_char is None:
        delimiter_char = '\t'

    if csv_format:
        assert not (footer or header), 'unsupported when csv_format = True'
        return r" sed '/\;/q' | sed 's/\;.*//' " + '\\\n' \
               + f'''| (echo "COPY (" && cat && echo ") TO STDOUT WITH {'CSV ' if csv_format else ''} DELIMITER '{delimiter_char}' ") \\\n''' \
               + '  | ' + query_command(db, echo_queries=False) + ' --variable=FETCH_COUNT=10000 \\\n' \
               + "  | sed '/^$/d'"  # remove empty lines
    else:
        header_argument = '--tuples-only' if not header else ''
        footer_argument = '--pset="footer=off"' if not footer else ''
        return (query_command(db, echo_queries=False) + ' --variable=FETCH_COUNT=10000'
                + " " + header_argument + " " + footer_argument
                + f" --no-align --field-separator='{delimiter_char}' \\\n"
                + "  | sed '/^$/d'"  # remove empty lines
                )


@copy_to_stdout_command.register(dbs.MysqlDB)
def __(db: dbs.MysqlDB, header: bool = None, footer: bool = None, delimiter_char: str = None, csv_format: bool = None):
    if header is None:
        header = False

    assert all(v is None for v in [footer, delimiter_char, csv_format]), "unimplemented parameter for MysqlDB"
    header_argument = '--skip-column-names' if header is False else ''
    return query_command(db) + ' ' + header_argument


@copy_to_stdout_command.register(dbs.SQLServerDB)
def __(db: dbs.SQLServerDB, header: bool = None, footer: bool = None, delimiter_char: str = None,
       csv_format: bool = None):
    assert all(
        v is None for v in [header, footer, delimiter_char, csv_format]), "unimplemented parameter for SQLServerDB"
    return query_command(db) + " -m csv"


@copy_to_stdout_command.register(dbs.OracleDB)
def __(db: dbs.OracleDB, header: bool = None, footer: bool = None, delimiter_char: str = None, csv_format: bool = None):
    assert all(v is None for v in [header, footer, delimiter_char, csv_format]), "unimplemented parameter for OracleDB"
    return "(echo 'set markup csv on\nset feedback off\nset heading off' && cat)" \
           + " \\\n  | " + query_command(db)


@copy_to_stdout_command.register(dbs.SQLiteDB)
def __(db: dbs.SQLiteDB, header: bool = None, footer: bool = None, delimiter_char: str = None, csv_format: bool = None):
    if header is None:
        header = False

    if delimiter_char is None:
        delimiter_char = '\t'

    assert all(v is None for v in [footer, csv_format]), "unimplemented parameter for SQLiteDB"
    header_argument = '-noheader' if not header else ''
    return query_command(db) + " " + header_argument + f" -separator '{delimiter_char}' -quote"


# -------------------------------


@singledispatch
def copy_from_stdin_command(db: object, target_table: str,
                            csv_format: bool = None, skip_header: bool = None,
                            delimiter_char: str = None, quote_char: str = None,
                            null_value_string: str = None, timezone: str = None) -> str:
    """
    Creates a shell command that receives data from stdin and writes it to a table.

    Options are tailored for the PostgreSQL `COPY FROM STDIN` command, adaptions might be needed for other databases.
    https://www.postgresql.org/docs/current/static/sql-copy.html

    Args:
        db: The database to use (either an alias or a `dbs.DB` object
        target_table: The table in which the data is written
        csv_format: Treat the input as a CSV file (comma separated, double quoted literals)
        skip_header: When true, skip the first line
        delimiter_char: The character that separates columns
        quote_char: The character for quoting strings
        null_value_string: The string that denotes NULL values
        timezone: Sets the timezone of the client, if applicable

    Returns:
        The composed shell command

    Examples:
        >>>> print(copy_from_stdin_command('mara', target_table='foo'))
        PGTZ=Europe/Berlin PGOPTIONS=--client-min-messages=warning psql --username=root --host=localhost \
            --echo-all --no-psqlrc --set ON_ERROR_STOP=on mara \
            --command="COPY foo FROM STDIN WITH CSV"
    """
    raise NotImplementedError(f'Please implement copy_from_stdin_command for type "{db.__class__.__name__}"')


@copy_from_stdin_command.register(str)
def __(alias: str, target_table: str, csv_format: bool = None, skip_header: bool = None,
       delimiter_char: str = None, quote_char: str = None, null_value_string: str = None, timezone: str = None):
    return copy_from_stdin_command(
        dbs.db(alias), target_table=target_table, csv_format=csv_format, skip_header=skip_header,
        delimiter_char=delimiter_char, quote_char=quote_char,
        null_value_string=null_value_string, timezone=timezone)


@copy_from_stdin_command.register(dbs.PostgreSQLDB)
def __(db: dbs.PostgreSQLDB, target_table: str, csv_format: bool = None, skip_header: bool = None,
       delimiter_char: str = None, quote_char: str = None, null_value_string: str = None, timezone: str = None):
    sql = f'COPY {target_table} FROM STDIN WITH'
    if csv_format:
        sql += ' CSV'
    if skip_header:
        sql += ' HEADER'
    if delimiter_char is not None:
        sql += f" DELIMITER AS '{delimiter_char}'"
    if null_value_string is not None:
        sql += f" NULL AS '{null_value_string}'"
    if quote_char is not None:
        sql += f" QUOTE AS '{quote_char}'"

    return f'{query_command(db, timezone)} \\\n      --command="{sql}"'


@copy_from_stdin_command.register(dbs.RedshiftDB)
def __(db: dbs.RedshiftDB, target_table: str, csv_format: bool = None, skip_header: bool = None,
       delimiter_char: str = None, quote_char: str = None, null_value_string: str = None, timezone: str = None):
    import uuid
    import datetime

    tmp_file_name = f'tmp-{datetime.datetime.now().isoformat()}-{uuid.uuid4().hex}.csv'
    s3_write_command = f'AWS_ACCESS_KEY_ID={db.aws_access_key_id} AWS_SECRET_ACCESS_KEY={db.aws_secret_access_key} aws s3 cp - s3://{db.aws_s3_bucket_name}/{tmp_file_name}'
    s3_delete_tmp_file_command = f'AWS_ACCESS_KEY_ID={db.aws_access_key_id} AWS_SECRET_ACCESS_KEY={db.aws_secret_access_key} aws s3 rm s3://{db.aws_s3_bucket_name}/{tmp_file_name}'

    sql = f"COPY {target_table} FROM 's3://{db.aws_s3_bucket_name}/{tmp_file_name}' access_key_id '{db.aws_access_key_id}' secret_access_key '{db.aws_secret_access_key}'"

    if csv_format:
        sql += ' CSV'
    if skip_header:
        sql += ' HEADER'
    if delimiter_char is not None:
        sql += f" DELIMITER AS '{delimiter_char}'"
    if null_value_string is not None:
        sql += f" NULL AS '{null_value_string}'"
    if quote_char is not None:
        sql += f" QUOTE AS '{quote_char}'"

    return s3_write_command + '\n\n' \
           + f'{query_command(db, timezone)} \\\n      --command="{sql}"\n\n' \
           + s3_delete_tmp_file_command


@copy_from_stdin_command.register(dbs.BigQueryDB)
def __(db: dbs.BigQueryDB, target_table: str, csv_format: bool = None, skip_header: bool = None,
       delimiter_char: str = None, quote_char: str = None, null_value_string: str = None, timezone: str = None):
    sql = 'bq load'
    if csv_format:
        sql += ' --source_format=CSV'
    else:
        sql += ' --source_format=NEWLINE_DELIMITED_JSON'
    if skip_header:
        sql += ' --skip_leading_rows=1'  # requires already created table
    else:
        sql += '  --autodetect'  # schema auto-detection for CSV and JSON data
    if delimiter_char is not None:
        sql += f" --field_delimiter='{delimiter_char}'"
    if null_value_string is not None:
        sql += f" --null_marker='{null_value_string}'"
    if quote_char is not None:
        sql += f" --quote='{quote_char}'"

    return sql + ' ' + target_table


# -------------------------------


@multidispatch
def copy_command(source_db: object, target_db: object, target_table: str,
                 timezone=None, csv_format=None, delimiter_char=None) -> str:
    """
    Creates a shell command that
    - receives a sql query from stdin
    - executes the query in `source_db`
    - writes the results of the query to `target_table` in `target_db`

    Args:
        source_db: The database in which to run the query (either an alias or a `dbs.DB` object
        target_db: The database where to write the query results (alias or db configuration)
        target_table: The table in which to write the query results
        timezone: Sets the timezone of the client, if applicable
        csv_format: double quote 'difficult' strings
        delimiter_char: The character that separates columns, default '\t'


    Returns:
        A shell command string

    Examples:
        >>>> print(copy_command(dbs.SQLServerDB(database='source_db'), dbs.PostgreSQLDB(database='target_db'), \
                                'target_table'))
        sqsh  -D source_db -m csv \
          | PGTZ=Europe/Berlin PGOPTIONS=--client-min-messages=warning psql --echo-all --no-psqlrc \
               --set ON_ERROR_STOP=on target_db \
               --command="COPY target_table FROM STDIN WITH CSV HEADER"
    """
    raise NotImplementedError(
        f'Please implement copy_command for types "{source_db.__class__.__name__}" and "{target_db.__class__.__name__}"'
    )


@copy_command.register(str, str)
def __(source_db_alias: str, target_db_alias: str, target_table: str, timezone: str = None,
       csv_format: bool = None, delimiter_char: str = None):
    return copy_command(dbs.db(source_db_alias), dbs.db(target_db_alias),
                        target_table=target_table, timezone=timezone,
                        csv_format=csv_format, delimiter_char=delimiter_char)


@copy_command.register(dbs.DB, str)
def __(source_db: dbs.DB, target_db_alias: str, target_table: str, timezone: str = None,
       csv_format: bool = None, delimiter_char: str = None):
    return copy_command(source_db, dbs.db(target_db_alias),
                        target_table=target_table, timezone=timezone,
                        csv_format=csv_format, delimiter_char=delimiter_char)


@copy_command.register(dbs.PostgreSQLDB, dbs.PostgreSQLDB)
def __(source_db: dbs.PostgreSQLDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None):
    return (copy_to_stdout_command(source_db, delimiter_char=delimiter_char, csv_format=csv_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table,
                                               null_value_string='', timezone=timezone, csv_format=csv_format,
                                               delimiter_char=delimiter_char))


@copy_command.register(dbs.MysqlDB, dbs.PostgreSQLDB)
def __(source_db: dbs.MysqlDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None):
    return (copy_to_stdout_command(source_db) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table,
                                               null_value_string='NULL', timezone=timezone,
                                               csv_format=csv_format, delimiter_char=delimiter_char))


@copy_command.register(dbs.SQLServerDB, dbs.PostgreSQLDB)
def __(source_db: dbs.SQLServerDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None):
    if csv_format is None:
        csv_format = True
    return (copy_to_stdout_command(source_db) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table, csv_format=csv_format,
                                               delimiter_char=delimiter_char,
                                               skip_header=True, timezone=timezone))


@copy_command.register(dbs.OracleDB, dbs.PostgreSQLDB)
def __(source_db: dbs.OracleDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None):
    if csv_format is None:
        csv_format = True

    return (copy_to_stdout_command(source_db) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table,
                                               csv_format=csv_format, skip_header=False, delimiter_char=delimiter_char,
                                               null_value_string='NULL', timezone=timezone))


@copy_command.register(dbs.SQLiteDB, dbs.PostgreSQLDB)
def __(source_db: dbs.SQLiteDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None):
    if csv_format is None:
        csv_format = True
    return (copy_to_stdout_command(source_db) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table, timezone=timezone,
                                               null_value_string='NULL', quote_char="''", csv_format=csv_format,
                                               delimiter_char=delimiter_char))
