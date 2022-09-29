"""
Shell command generation for
- running queries in databases via their command line clients
- copying data from, into and between databases
"""

import shlex
from functools import singledispatch

import sys
from mara_db import dbs, config
from multimethod import multidispatch

from .format import *


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

    Examples:
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
        echo_queries = config.default_echo_queries()

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
        echo_queries = config.default_echo_queries()

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
    from .bigquery import bigquery_credentials

    service_account_email = bigquery_credentials(db).service_account_email

    return (f'CLOUDSDK_CORE_ACCOUNT={service_account_email}'
            + ' bq query'
            + ' --max_rows=50000000'  # run without user interaction
            + ' --headless'  # run without user interaction
            + ' --quiet'  # no job progress updates
            + ' --format=csv'  # no job progress updates
            + (f' --use_legacy_sql=' + ('true' if db.use_legacy_sql else 'false'))
            + (f' --project_id={db.project}' if db.project else '')
            + (f' --location={db.location}' if db.location else '')
            + (f' --dataset_id={db.dataset}' if db.dataset else '')
            + ' ')


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


@query_command.register(dbs.SqshSQLServerDB)
def __(db: dbs.SqshSQLServerDB, timezone: str = None, echo_queries: bool = None):
    assert timezone is None, "unimplemented parameter for SqshSQLServerDB"

    if echo_queries is None:
        echo_queries = config.default_echo_queries()

    # sqsh does not do anything when a statement is not terminated by a ';', add one to be sure
    command = "(cat && echo ';') \\\n  | "
    command += "(cat && echo ';\n\go') \\\n  | "

    return (command + 'sqsh -a 1 -d 0 -f 10'
            + (f' -U {db.user}' if db.user else '')
            + (f' -P {db.password}' if db.password else '')
            + (f' -S {db.host}' if db.host else '')
            + (f':{db.port}' if db.host and db.port and db.port != 1433 else '')
            + (f' -D {db.database}' if db.database else '')
            + (f' -e' if echo_queries else ''))


@query_command.register(dbs.SqlcmdSQLServerDB)
def __(db: dbs.SqlcmdSQLServerDB, timezone: str = None, echo_queries: bool = None):
    assert timezone is None, "unimplemented parameter for SQLServerDB"

    if echo_queries is None:
        echo_queries = config.default_echo_queries()

    if db.host:
        # connection to DB, see: https://docs.microsoft.com/en-us/sql/ssms/scripting/sqlcmd-connect-to-the-database-engine?view=sql-server-ver15
        if db.protocol == 'tcp':
            port = db.port if db.port else 1433
            server = f'tcp:{db.host},{port}'
        elif db.protocol == 'np':
            pipe = f'MSSQL${db.instance}\\sql\\query' if db.instance else 'pipe\\sql\\query'
            server = f'np:\\\\{db.host}\\{pipe}'
        elif db.protocol == 'lpc':
            server = f'lcp:{db.host}\\{db.instance}' if db.instance else f'lcp:{db.host}'
        else:
            if db.instance:
                server = f'{db.host}\\{db.instance}'
            elif db.port:
                server = f'{db.host},{db.port}'
            else:
                server = db.host

    return ('sqlcmd -b -r'
            + (f' -U {db.user}' if db.user else '')
            + (f' -P {db.password}' if db.password else '')
            + (f' -S {server}' if server else '')
            + (' -C' if db.trust_server_certificate else '')
            + (f' -d {db.database}' if db.database else '')
            + (' -e' if echo_queries else '')
            + (' -I' if db.quoted_identifier else '')
            + (' -i /dev/stdin'))


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


@query_command.register(dbs.SnowflakeDB)
def __(db: dbs.SnowflakeDB, timezone: str = None, echo_queries: bool = None):
    assert timezone is None, "unimplemented parameter for SnowflakeDB"
    assert not echo_queries, "unimplemented parameter for SnowflakeDB"
    return ((f'SNOWSQL_PWD={shlex.quote(db.password)} ' if db.password else '')
            +(f'SNOWSQL_PRIVATE_KEY_PASSPHRASE={shlex.quote(db.private_key_passphrase)}' if db.private_key_passphrase else '')
            + 'snowsql --noup -o exit_on_error=true'
            +(f' -c {db.connection}' if db.connection else '')
            +(f' -a {db.account}' if db.account else '')
            +(f' -u {db.user}' if db.user else '')
            +(f' --private-key-path {db.private_key_file}' if db.private_key_file else '')
            +(f' -d {db.database}' if db.database else '')
            +' -f /dev/stdin')


@query_command.register(dbs.DatabricksDB)
def __(db: dbs.DatabricksDB, timezone: str = None, echo_queries: bool = None):
    assert timezone is None, "unimplemented parameter for DatabricksDB"
    assert not echo_queries, "unimplemented parameter for DatabricksDB"
    return ('dbsqlcli'
            + (f' --hostname {db.host}' if db.host else '')
            + (f' --http-path {db.http_path}' if db.http_path else '')
            + (f' --access-token {db.access_token}' if db.access_token else '')
            + ' -e /dev/stdin')


# -------------------------------


@singledispatch
def copy_to_stdout_command(db: object,
                           header: bool = None,
                           footer: bool = None,
                           delimiter_char: str = None,
                           csv_format: bool = None,
                           pipe_format: Format = None) -> str:
    """
    Creates a shell command that receives a query from stdin, executes it and writes the output to stdout

    Args:
        db: The database in which to run the query (either an alias or a `dbs.DB` object
        header: Whether a csv header with the column name(s) will be included or not.
            No header, by default. (not implemented in sqsh for SQLServerDB)
        footer: Whether a footer will be included or not. False by default. (Only implemented for PostgreSQLDB)
        delimiter_char: str to delimit the fields in one row. Default: tab character
        csv_format: Double quote 'difficult' strings (Only implemented for PostgreSQLDB)
        pipe_format: The format passed to stdout

    Returns:
        The composed shell command

    Example:
        >>> print(copy_to_stdout_command(dbs.PostgreSQLDB(host='localhost', database='test')))
        PGTZ=Europe/Berlin PGOPTIONS=--client-min-messages=warning psql --host=localhost  --no-psqlrc --set ON_ERROR_STOP=on test --tuples-only --no-align --field-separator='	' \
            | grep -a -v -e '^$'
    """
    raise NotImplementedError(f'Please implement function copy_to_stdout_command for type "{db.__class__.__name__}"')


@copy_to_stdout_command.register(str)
def __(alias: str, header: bool = None, footer: bool = None, delimiter_char: str = None, csv_format: bool = None,
       pipe_format: Format = None):
    return copy_to_stdout_command(dbs.db(alias), header=header, footer=footer,
                                  delimiter_char=delimiter_char, csv_format=csv_format,
                                  pipe_format=pipe_format)


@copy_to_stdout_command.register(dbs.PostgreSQLDB)
def __(db: dbs.PostgreSQLDB, header: bool = None, footer: bool = None,
       delimiter_char: str = None, csv_format: bool = None, pipe_format: Format = None):
    if pipe_format:
        if isinstance(pipe_format, CsvFormat):
            if delimiter_char is None:
                delimiter_char = pipe_format.delimiter_char
            if header is None:
                header = pipe_format.header
            if footer is None:
                footer = pipe_format.footer
        else:
            raise ValueError(f'Unsupported pipe_format for PostgreSQLDB: {pipe_format}')

    if header is None:
        header = False

    if footer is None:
        footer = False

    if delimiter_char is None:
        delimiter_char = '\t'

    if csv_format or isinstance(pipe_format, CsvFormat):
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


@copy_to_stdout_command.register(dbs.BigQueryDB)
def __(db: dbs.BigQueryDB, header: bool = None, footer: bool = None, delimiter_char: str = None,
       csv_format: bool = None, pipe_format: Format = None):
    assert all(v is None for v in [header, footer]), "unimplemented parameter for BigQuery"
    if pipe_format:
        if isinstance(pipe_format, CsvFormat):
            if pipe_format.header:
                raise ValueError('Unsupported pipe_format.header for BigQueryDB')
        else:
            raise ValueError(f'Unsupported pipe_format for MysqlDB: {pipe_format}')

    remove_header = 'sed 1d'
    return query_command(db) + f' | {remove_header}'


@copy_to_stdout_command.register(dbs.MysqlDB)
def __(db: dbs.MysqlDB, header: bool = None, footer: bool = None, delimiter_char: str = None, csv_format: bool = None,
       pipe_format: Format = None):
    assert all(v is None for v in [footer, delimiter_char, csv_format]), "unimplemented parameter for MysqlDB"
    if pipe_format:
        if isinstance(pipe_format, CsvFormat):
            if header is None:
                header = pipe_format.header
        else:
            raise ValueError(f'Unsupported pipe_format for MysqlDB: {pipe_format}')

    if header is None:
        header = False

    header_argument = '--skip-column-names' if header == False else ''
    return query_command(db) + ' ' + header_argument


@copy_to_stdout_command.register(dbs.SqshSQLServerDB)
def __(db: dbs.SqshSQLServerDB, header: bool = None, footer: bool = None, delimiter_char: str = None,
       csv_format: bool = None, pipe_format: Format = None):
    assert all(v is None for v in [header, footer]), "unimplemented parameter for SqshSQLServerDB"
    if csv_format == False:
        raise ValueError(f'For SqshSQLServerDB csv_format must be True or not set')
    if pipe_format:
        if isinstance(pipe_format, CsvFormat):
            if pipe_format.header:
                raise ValueError('pipe_format.header is not supported for SqshSQLServerDB')
            if delimiter_char is None:
                delimiter_char = pipe_format.delimiter_char
        else:
            raise ValueError(f'Unsupported pipe_format for SqshSQLServerDB: {pipe_format}')
    if delimiter_char and delimiter_char != ',':
        raise ValueError(f"For SqshSQLServerDB delimiter_char must ','")
    return query_command(db, echo_queries=False) + " -m csv"


@copy_to_stdout_command.register(dbs.SqlcmdSQLServerDB)
def __(db: dbs.SqlcmdSQLServerDB, header: bool = None, footer: bool = None, delimiter_char: str = None,
       csv_format: bool = None, pipe_format: Format = None):
    assert footer is None, "unimplemented parameter for SqlcmdSQLServerDB"
    if csv_format == False:
        raise ValueError(f'For SqlcmdSQLServerDB csv_format must be True or not set')
    if pipe_format:
        if isinstance(pipe_format, CsvFormat):
            if header is None:
                header = pipe_format.header
            if delimiter_char is None:
                delimiter_char = pipe_format.delimiter_char
        else:
            raise ValueError(f'Unsupported pipe_format for SqlcmdSQLServerDB: {pipe_format}')

    # manipulate the SQL query
    command = "(echo 'SET NOCOUNT ON\n' && cat) \\\n  | "
    command += "(echo 'GO\n' && cat) \\\n  | "

    return (command + query_command(db, echo_queries=False)
            + ' -W'
            + (f' "-s{delimiter_char}"' if delimiter_char else ' -s,')
            + (f' -h-1' if not header else '')
            + (f' -w 65535') # see https://docs.microsoft.com/en-us/sql/tools/sqlcmd-utility?view=sql-server-ver15, is used to avoid line-break when output is longer then 80 characters
            # removes the dashed line between header and data rows
            + (" | sed -e '2d'" if header else ''))


@copy_to_stdout_command.register(dbs.OracleDB)
def __(db: dbs.OracleDB, header: bool = None, footer: bool = None, delimiter_char: str = None, csv_format: bool = None,
       pipe_format: Format = None):
    assert all(v is None for v in [header, footer, delimiter_char, csv_format]), "unimplemented parameter for OracleDB"
    if pipe_format and not isinstance(pipe_format, CsvFormat):
        raise ValueError(f'Unsupported pipe_format for OracleDB: {pipe_format}')
    return "(echo 'set markup csv on\nset feedback off\nset heading off' && cat)" \
           + " \\\n  | " + query_command(db)


@copy_to_stdout_command.register(dbs.SQLiteDB)
def __(db: dbs.SQLiteDB, header: bool = None, footer: bool = None, delimiter_char: str = None, csv_format: bool = None,
       pipe_format: Format = None):
    assert all(v is None for v in [footer, csv_format]), "unimplemented parameter for SQLiteDB"

    if pipe_format:
        if isinstance(pipe_format, CsvFormat):
            if header is None:
                header = pipe_format.header
            if delimiter_char is None:
                delimiter_char = pipe_format.delimiter_char
        else:
            raise ValueError(f'Unsupported pipe_format for SQLiteDB: {pipe_format}')

    if header is None:
        header = False

    if delimiter_char is None:
        delimiter_char = '\t'

    header_argument = '-noheader' if not header else ''
    return query_command(db) + " " + header_argument + f" -separator '{delimiter_char}' -quote"


@copy_to_stdout_command.register(dbs.SnowflakeDB)
def __(db: dbs.SnowflakeDB, header: bool = None, footer: bool = None, delimiter_char: str = None, csv_format: bool = None,
       pipe_format: Format = None):
    assert footer is None, "unimplemented parameter for SnowflakeDB"

    if pipe_format:
        if isinstance(pipe_format, CsvFormat):
            if header is None:
                header = pipe_format.header
            if delimiter_char is None:
                delimiter_char = pipe_format.delimiter_char
        else:
            raise ValueError(f'Unsupported pipe_format for SnowflakeDB: {pipe_format}')       

    if csv_format == False:
        raise ValueError('Not supported format: csv_format must be True or not set')

    if not delimiter_char:
        delimiter_char = ','

    output_format = None
    # https://docs.snowflake.com/en/user-guide/snowsql-config.html#output-format
    if delimiter_char == ',':
        output_format = 'csv'
    elif delimiter_char == '\t':
        output_format = 'tsv'
    else:
        raise ValueError(f"Not supported delimiter_char for SnowflakeDB: '{delimiter_char}'")

    # possible other output_format, not implemented:
    #   json = json array

    # see also: https://docs.snowflake.com/en/user-guide/snowsql-use.html#exporting-data
    return (query_command(db, echo_queries=False) + f' -o output_format={output_format} -o friendly=false -o timing=false'
            +(f' -o header=true' if header else ' -o header=false'))


@copy_to_stdout_command.register(dbs.DatabricksDB)
def __(db: dbs.DatabricksDB, header: bool = None, footer: bool = None, delimiter_char: str = None, csv_format: bool = None,
       pipe_format: Format = None):
    assert footer is None, "unimplemented parameter for DatabricksDB"

    if pipe_format:
        if isinstance(pipe_format, CsvFormat):
            if header is None:
                header = pipe_format.header
            if delimiter_char is None:
                delimiter_char = pipe_format.delimiter_char
        else:
            raise ValueError(f'Unsupported pipe_format for DatabricksDB: {pipe_format}')       

    if csv_format == False:
        raise ValueError('Not supported format: csv_format must be True or not set')

    if not header:
        remove_header = 'sed 1d'
    else:
        remove_header = None

    if delimiter_char == ',':
        table_format = 'csv'
    elif delimiter_char == '\t':
        table_format = 'tsv'
    else:
        raise ValueError(f"Not supported delimiter_char for DatabricksDB: '{delimiter_char}'")

    return (query_command(db, echo_queries=False)
            + f' --table-format {table_format}'
            + (f'\n  | {remove_header}' if remove_header else ''))


# -------------------------------


@singledispatch
def copy_from_stdin_command(db: object, target_table: str,
                            csv_format: bool = None, skip_header: bool = None,
                            delimiter_char: str = None, quote_char: str = None,
                            null_value_string: str = None, timezone: str = None,
                            pipe_format: Format = None) -> str:
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
        pipe_format: The format passed from stdin

    Returns:
        The composed shell command

    Example:
        >>> print(copy_from_stdin_command('mara', target_table='foo'))
        PGTZ=Europe/Berlin PGOPTIONS=--client-min-messages=warning psql --username=root --host=localhost \
            --echo-all --no-psqlrc --set ON_ERROR_STOP=on mara \
            --command="COPY foo FROM STDIN WITH CSV"
    """
    raise NotImplementedError(f'Please implement copy_from_stdin_command for type "{db.__class__.__name__}"')


@copy_from_stdin_command.register(str)
def __(alias: str, target_table: str, csv_format: bool = None, skip_header: bool = None,
       delimiter_char: str = None, quote_char: str = None, null_value_string: str = None,
       timezone: str = None, pipe_format: Format = None):
    return copy_from_stdin_command(
        dbs.db(alias), target_table=target_table, csv_format=csv_format, skip_header=skip_header,
        delimiter_char=delimiter_char, quote_char=quote_char,
        null_value_string=null_value_string, timezone=timezone, pipe_format=pipe_format)


@copy_from_stdin_command.register(dbs.PostgreSQLDB)
def __(db: dbs.PostgreSQLDB, target_table: str, csv_format: bool = None, skip_header: bool = None,
       delimiter_char: str = None, quote_char: str = None, null_value_string: str = None, timezone: str = None,
       pipe_format: Format = None):

    columns = ''
    sed_stdin = ''
    if pipe_format:
        if isinstance(pipe_format, JsonlFormat):
            columns = ' (' + ', '.join(['data']) + ')'
            # escapes JSON escapings since PostgreSQL interprets C-escapes in TEXT mode
            sed_stdin += "sed 's/\\\\/\\\\x5C/g' \\\n| "
        elif isinstance(pipe_format, CsvFormat):
            csv_format = True
            if delimiter_char is None:
                delimiter_char = pipe_format.delimiter_char
            if quote_char is None:
                quote_char = pipe_format.quote_char
            if skip_header is None:
                skip_header = pipe_format.header
        else:
            raise ValueError(f'Unsupported pipe_format for PostgreSQLDB: {pipe_format}')

    sql = f'COPY {target_table}{columns} FROM STDIN WITH'
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

    # escape double quotes
    sql = sql.replace('"', '\\"')

    return f'{sed_stdin}{query_command(db, timezone)} \\\n      --command="{sql}"'


@copy_from_stdin_command.register(dbs.RedshiftDB)
def __(db: dbs.RedshiftDB, target_table: str, csv_format: bool = None, skip_header: bool = None,
       delimiter_char: str = None, quote_char: str = None, null_value_string: str = None, timezone: str = None,
       pipe_format: Format = None):
    import uuid
    import datetime

    tmp_file_name = f'tmp-{datetime.datetime.now().isoformat()}-{uuid.uuid4().hex}.csv'
    s3_write_command = f'AWS_ACCESS_KEY_ID={db.aws_access_key_id} AWS_SECRET_ACCESS_KEY={db.aws_secret_access_key} aws s3 cp - s3://{db.aws_s3_bucket_name}/{tmp_file_name}'
    s3_delete_tmp_file_command = f'AWS_ACCESS_KEY_ID={db.aws_access_key_id} AWS_SECRET_ACCESS_KEY={db.aws_secret_access_key} aws s3 rm s3://{db.aws_s3_bucket_name}/{tmp_file_name}'

    columns = ''
    sed_stdin = ''
    if pipe_format:
        if isinstance(pipe_format, JsonlFormat):
            columns = ' (' + ', '.join(['data']) + ')'
            # escapes JSON escapings since PostgreSQL interprets C-escapes in TEXT mode
            sed_stdin += "sed 's/\\\\/\\\\x5C/g' \\\n| "
        elif isinstance(pipe_format, CsvFormat):
            csv_format = True
            if delimiter_char is None:
                delimiter_char = pipe_format.delimiter_char
            if quote_char is None:
                quote_char = pipe_format.quote_char
            if skip_header is None:
                skip_header = pipe_format.header
        else:
            raise ValueError(f'Unsupported pipe_format for RedshiftDB: {pipe_format}')

    sql = f"COPY {target_table}{columns} FROM 's3://{db.aws_s3_bucket_name}/{tmp_file_name}' access_key_id '{db.aws_access_key_id}' secret_access_key '{db.aws_secret_access_key}'"

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

    return s3_write_command + ' &&\n\n' \
            + f'{sed_stdin}{query_command(db, timezone)} \\\n      --command="{sql}" \\\n  || /bin/false \\\n  ; RC=$?\n\n' \
            + s3_delete_tmp_file_command+' &&\n  $(exit $RC) || /bin/false'


@copy_from_stdin_command.register(dbs.BigQueryDB)
def __(db: dbs.BigQueryDB, target_table: str, csv_format: bool = None, skip_header: bool = None,
       delimiter_char: str = None, quote_char: str = None, null_value_string: str = None, timezone: str = None,
       pipe_format: Format = None):
    assert db.gcloud_gcs_bucket_name, f"Please provide the 'gcloud_gcs_bucket_name' parameter to database '{db}' "

    if csv_format or isinstance(pipe_format, CsvFormat):
        bq_format = 'CSV'
        file_extension = 'csv'
        if isinstance(pipe_format, CsvFormat):
            if delimiter_char is None:
                delimiter_char = pipe_format.delimiter_char
            if quote_char is None:
                quote_char = pipe_format.quote_char
            if skip_header is None:
                skip_header = pipe_format.header
    elif not pipe_format or isinstance(pipe_format, JsonlFormat):
        bq_format = 'NEWLINE_DELIMITED_JSON'
        file_extension = 'jsonl'
    elif isinstance(pipe_format, AvroFormat):
        bq_format = 'AVRO'
        file_extension = 'avro'
    elif isinstance(pipe_format, ParquetFormat):
        bq_format = 'PARQUET'
        file_extension = 'parquet'
    elif isinstance(pipe_format, OrcFormat):
        bq_format = 'ORC'
        file_extension = 'orc'
    else:
        raise ValueError(f'Unsupported pipe_format for BigQueryDB: {pipe_format}')

    import uuid
    import datetime
    from .bigquery import bigquery_credentials

    tmp_file_name = f'tmp-{datetime.datetime.now().isoformat()}-{uuid.uuid4().hex}.{file_extension}'

    service_account_email = bigquery_credentials(db).service_account_email

    set_env_prefix = f'CLOUDSDK_CORE_ACCOUNT={service_account_email}'
    bq_load_command = (set_env_prefix
                       + ' bq load'
                       + ' --headless'
                       + ' --quiet'
                       + (f' --location={db.location}' if db.location else '')
                       + (f' --project_id={db.project}' if db.project else '')
                       + (f' --dataset_id={db.dataset}' if db.dataset else '')
                       + (f' --skip_leading_rows=1' if skip_header else '')
                       )

    bq_load_command += + f' --source_format={bq_format}'

    if delimiter_char is not None:
        bq_load_command += f" --field_delimiter='{delimiter_char}'"
    if null_value_string is not None:
        bq_load_command += f" --null_marker='{null_value_string}'"
    if quote_char is not None:
        bq_load_command += f" --quote='{quote_char}'"

    bq_load_command += f" '{target_table}'  gs://{db.gcloud_gcs_bucket_name}/{tmp_file_name}"

    gcs_write_command = f'{set_env_prefix} gsutil -q cp - gs://{db.gcloud_gcs_bucket_name}/{tmp_file_name}'
    gcs_delete_temp_file_command = f'{set_env_prefix} gsutil -q rm gs://{db.gcloud_gcs_bucket_name}/{tmp_file_name}'

    return gcs_write_command + '\\\n  \\\n  && ' \
           + bq_load_command + '\\\n  \\\n  && ' \
           + gcs_delete_temp_file_command


@copy_from_stdin_command.register(dbs.SqlcmdSQLServerDB)
def __(db: dbs.SqlcmdSQLServerDB, target_table: str, csv_format: bool = None, skip_header: bool = None,
       delimiter_char: str = None, quote_char: str = None, null_value_string: str = None, timezone: str = None,
       pipe_format: Format = None):
    assert all(v is None for v in [quote_char, timezone]), "unimplemented parameter for SqlcmdSQLServerDB"

    if pipe_format:
        if isinstance(pipe_format, CsvFormat):
            csv_format = True
            if delimiter_char is None:
                delimiter_char = pipe_format.delimiter_char
            if quote_char is None:
                quote_char = pipe_format.quote_char
            if skip_header is None:
                skip_header = pipe_format.header
        else:
            raise ValueError(f'Unsupported pipe_format for SqlcmdSQLServerDB: {pipe_format}')
    else:
        if csv_format == False:
            raise ValueError('The parameter csv_format must be true or none when the db_alias referres to a SQL Server (SqlcmdSQLServerDB)')

    if null_value_string is not None and null_value_string != '':
        raise ValueError("The parameter null_value_string must be None or an empty string ('') when the db_alias referres to a SQL Server (SqlcmdSQLServerDB)")

    if not delimiter_char:
        delimiter_char = ','

    if db.host:
        # connection to DB, see: https://docs.microsoft.com/en-us/sql/ssms/scripting/sqlcmd-connect-to-the-database-engine?view=sql-server-ver15
        if db.protocol == 'tcp':
            port = db.port if db.port else 1433
            server = f'tcp:{db.host},{port}'
        elif db.protocol == 'np':
            pipe = f'MSSQL${db.instance}\\sql\\query' if db.instance else 'pipe\\sql\\query'
            server = f'np:\\\\{db.host}\\{pipe}'
        elif db.protocol == 'lpc':
            server = f'lcp:{db.host}\\{db.instance}' if db.instance else f'lcp:{db.host}'
        else:
            if db.instance:
                server = f'{db.host}\\{db.instance}'
            elif db.port:
                server = f'{db.host},{db.port}'
            else:
                server = db.host

    return ('{ '
            # create a temporary file for stdin; bcp does not support stdin by default
            + 'TEMP_STDIN="$(mktemp)"; '
            # transforms CRLF to LF and saves stdin; bcp uses LF in unix systems by default
            + 'cat - | sed "s/\\r$//g" > "${TEMP_STDIN}"; '
            + f'bcp {target_table} in "${{TEMP_STDIN}}"'
            + (f' -U {db.user}' if db.user else '')
            + (f' -P {db.password}' if db.password else '')
            + (f' -S {server}' if server else '')
            + (' -u' if db.trust_server_certificate else '')
            + (f' -d {db.database}' if db.database else '')
            + ' -c'
            + (f' -t {delimiter_char}' if delimiter_char != '\t' else '')
            + (' -F2' if skip_header else '')
            # removes the temporary file
            + f'; rm -f "${{TEMP_STDIN}}" > /dev/null; '
            + '}')


# -------------------------------


@multidispatch
def copy_command(source_db: object, target_db: object, target_table: str,
                 timezone=None, csv_format=None, delimiter_char=None,
                 pipe_format: Format = None) -> str:
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
        pipe_format: The piping data format to be used


    Returns:
        A shell command string

    Example:
        >>> print(copy_command(dbs.SQLServerDB(database='source_db'), dbs.PostgreSQLDB(database='target_db'), \
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
       csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    return copy_command(dbs.db(source_db_alias), dbs.db(target_db_alias),
                        target_table=target_table, timezone=timezone,
                        csv_format=csv_format, delimiter_char=delimiter_char,
                        pipe_format=pipe_format)


@copy_command.register(dbs.DB, str)
def __(source_db: dbs.DB, target_db_alias: str, target_table: str, timezone: str = None,
       csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    return copy_command(source_db, dbs.db(target_db_alias),
                        target_table=target_table, timezone=timezone,
                        csv_format=csv_format, delimiter_char=delimiter_char,
                        pipe_format=pipe_format)


@copy_command.register(dbs.PostgreSQLDB, dbs.PostgreSQLDB)
def __(source_db: dbs.PostgreSQLDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    return (copy_to_stdout_command(source_db, delimiter_char=delimiter_char, csv_format=csv_format,
                                   pipe_format=pipe_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table,
                                               null_value_string='', timezone=timezone, csv_format=csv_format,
                                               delimiter_char=delimiter_char, pipe_format=pipe_format))


@copy_command.register(dbs.PostgreSQLDB, dbs.BigQueryDB)
def __(source_db: dbs.PostgreSQLDB, target_db: dbs.BigQueryDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    if csv_format is None and pipe_format is None:
        pipe_format = CsvFormat(
            delimiter_char='\t' if not delimiter_char and csv_format else delimiter_char)
    return (copy_to_stdout_command(source_db, delimiter_char=delimiter_char, csv_format=csv_format,
                                   pipe_format=pipe_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table,
                                               timezone=timezone, csv_format=csv_format,
                                               delimiter_char='\t' if not delimiter_char and csv_format else delimiter_char))


@copy_command.register(dbs.BigQueryDB, dbs.PostgreSQLDB)
def __(source_db: dbs.BigQueryDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    if csv_format is None and pipe_format is None:
        pipe_format = CsvFormat(
            delimiter_char='\t' if not delimiter_char and csv_format else delimiter_char)
    return (copy_to_stdout_command(source_db, delimiter_char=delimiter_char, csv_format=csv_format,
                                   pipe_format=pipe_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table,
                                               timezone=timezone, csv_format=csv_format,
                                               pipe_format=pipe_format))


@copy_command.register(dbs.MysqlDB, dbs.PostgreSQLDB)
def __(source_db: dbs.MysqlDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    return (copy_to_stdout_command(source_db, pipe_format=pipe_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table,
                                               null_value_string='NULL', timezone=timezone,
                                               csv_format=csv_format, delimiter_char=delimiter_char,
                                               pipe_format=pipe_format))


@copy_command.register(dbs.MysqlDB, dbs.BigQueryDB)
def __(source_db: dbs.MysqlDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    if csv_format is None and pipe_format is None:
        pipe_format = CsvFormat(delimiter_char=delimiter_char)
    return (copy_to_stdout_command(source_db, pipe_format=pipe_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table,
                                               null_value_string='NULL', timezone=timezone,
                                               csv_format=csv_format,
                                               pipe_format=pipe_format))


@copy_command.register(dbs.SQLServerDB, dbs.PostgreSQLDB)
def __(source_db: dbs.SQLServerDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    if csv_format is None and pipe_format is None:
        pipe_format = CsvFormat(delimiter_char=delimiter_char, header=True)
    return (copy_to_stdout_command(source_db, pipe_format=pipe_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table, csv_format=csv_format,
                                               skip_header=True, timezone=timezone,
                                               pipe_format=pipe_format))


@copy_command.register(dbs.SqshSQLServerDB, dbs.BigQueryDB)
def __(source_db: dbs.SQLServerDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    if csv_format is None and pipe_format is None:
        pipe_format = CsvFormat(delimiter_char=delimiter_char, header=True)
    return (copy_to_stdout_command(source_db, pipe_format=pipe_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table, csv_format=csv_format,
                                               skip_header=True, timezone=timezone,
                                               pipe_format=pipe_format))


@copy_command.register(dbs.SqlcmdSQLServerDB, dbs.BigQueryDB)
def __(source_db: dbs.SqlcmdSQLServerDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None):
    if csv_format is None:
        csv_format = True
    return (copy_to_stdout_command(source_db) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table, csv_format=csv_format,
                                               delimiter_char=delimiter_char,
                                               null_value_string='NULL', skip_header=True))


@copy_command.register(dbs.OracleDB, dbs.PostgreSQLDB)
def __(source_db: dbs.OracleDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    if csv_format is None and pipe_format is None:
        pipe_format = CsvFormat(delimiter_char=delimiter_char, header=False)
    return (copy_to_stdout_command(source_db, pipe_format=pipe_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table,
                                               csv_format=csv_format, skip_header=False,
                                               null_value_string='NULL', timezone=timezone, pipe_format=pipe_format))


@copy_command.register(dbs.OracleDB, dbs.BigQueryDB)
def __(source_db: dbs.OracleDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    if csv_format is None and pipe_format is None:
        pipe_format = CsvFormat(delimiter_char=delimiter_char, header=False)
    return (copy_to_stdout_command(source_db, pipe_format=pipe_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table,
                                               csv_format=csv_format, skip_header=False,
                                               null_value_string='NULL', timezone=timezone, pipe_format=pipe_format))


@copy_command.register(dbs.SQLiteDB, dbs.PostgreSQLDB)
def __(source_db: dbs.SQLiteDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    if csv_format is None and pipe_format is None:
        pipe_format = CsvFormat(delimiter_char=delimiter_char, quote_char="''")
    return (copy_to_stdout_command(source_db, pipe_format=pipe_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table, timezone=timezone,
                                               null_value_string='NULL', csv_format=csv_format,
                                               pipe_format=pipe_format))


@copy_command.register(dbs.SQLiteDB, dbs.BigQueryDB)
def __(source_db: dbs.SQLiteDB, target_db: dbs.PostgreSQLDB, target_table: str,
       timezone: str = None, csv_format: bool = None, delimiter_char: str = None, pipe_format: Format = None):
    if csv_format is None and pipe_format is None:
        pipe_format = CsvFormat(delimiter_char=delimiter_char, quote_char="''")
    return (copy_to_stdout_command(source_db, pipe_format=pipe_format) + ' \\\n'
            + '  | ' + copy_from_stdin_command(target_db, target_table=target_table, timezone=timezone,
                                               null_value_string='NULL', quote_char="''", csv_format=csv_format,
                                               pipe_format=pipe_format))
