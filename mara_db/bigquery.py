"""Easy access to BigQuery databases via google.cloud.bigquery"""

import contextlib
import typing

import mara_db.dbs
import sys
import time
from google.api_core.exceptions import BadRequest


def bigquery_credentials(db: typing.Union[str, mara_db.dbs.BigQueryDB]) -> 'google.oauth2.service_account.Credentials':
    """Get the parsed service account """
    from google.oauth2.service_account import Credentials

    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    return Credentials.from_service_account_file(db.service_account_json_file_name)


def bigquery_client(db: typing.Union[str, mara_db.dbs.BigQueryDB]) -> 'google.cloud.bigquery.client.Client':
    """Get an bigquery client for a bq database alias"""
    from google.cloud.bigquery.client import Client

    if isinstance(db, str):
        db = mara_db.dbs.db(db)

    credentials = bigquery_credentials(db)

    return Client(project=credentials.project_id, credentials=credentials, location=db.location)


@contextlib.contextmanager
def bigquery_cursor_context(db: typing.Union[str, mara_db.dbs.BigQueryDB]) \
        -> 'google.cloud.bigquery.dbapi.cursor.Cursor':
    """Creates a context with a bigquery cursor for a database alias"""
    client = bigquery_client(db)

    from google.cloud.bigquery.dbapi.connection import Connection

    connection = Connection(client)
    cursor = connection.cursor()  # type: google.cloud.bigquery.dbapi.cursor.Cursor
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.close()
        raise e


def create_bigquery_table_from_postgresql_query(
        postgresql_query: str, postgresql_db_alias: str,
        bigquery_db_alias: str, bigquery_dataset_id: str, bigquery_table_name: str):
    """
    Creates a table in for bigquery from a Postgresql SELECT query. Will print the query

    Usefull for copying PostgreSQL tables to BigQuery (create table first and then copy)

    Example:
        >>> create_bigquery_table_from_postgresql_query(
        >>>              postgresql_db_alias='dwh',
        >>>              postgresql_query='SELECT 1::SMALLINT AS a, now() as b',
        >>>              bigquery_db_alias='reporting',
        >>>              bigquery_dataset_id='foo',
        >>>              bigquery_table_name='bar')
        CREATE OR REPLACE TABLE `foo`.`bar` (
            `a` INT64,
            `b` TIMESTAMP
        )

    Args:
        postgresql_query: The query to execute in PostgreSQL, must not end with a semicolon
        postgresql_db_alias: The postgresql database to execute the query in
        bigquery_db_alias: The mara db alias of the bigquery connection
        bigquery_dataset_id: The id of the bigquery dataset in which the table is to be created
        bigquery_table_name: The name of the to be created table
    """
    from mara_db.postgresql import postgres_cursor_context
    with mara_db.postgresql.postgres_cursor_context(postgresql_db_alias) as cursor:
        cursor.execute('SELECT oid, typname FROM pg_type;')
        pg_types = {}
        for oid, type_name in cursor.fetchall():
            pg_types[oid] = type_name

        # https://cloud.google.com/bigquery/docs/reference/standard-sql/federated_query_functions#postgressql_mapping
        pg_to_bigquery_type_mapping = {
            'bool': 'BOOL',
            'bytea': 'BYTES',
            'date': 'DATE',
            'int2': 'INT64',
            'int4': 'INT64',
            'int8': 'INT64',
            'json': 'STRING',
            'jsonb': 'STRING',
            'numeric': 'NUMERIC',
            'float4': 'FLOAT64',
            'float8': 'FLOAT64',
            'varchar': 'STRING',
            'text': 'STRING',
            'time': 'TIME',
            'timestamp': 'DATETIME',
            'timestamptz': 'TIMESTAMP',
        }

        cursor.execute(postgresql_query + ' LIMIT 0')

        column_specs = []
        for column in cursor.description:
            pg_type = pg_types[column.type_code]
            assert pg_type in pg_to_bigquery_type_mapping, f"Unmapped type '{pg_type}'"
            column_specs.append(f'`{column.name}` {pg_to_bigquery_type_mapping[pg_type]}')

        query = f"""
CREATE OR REPLACE TABLE `{bigquery_dataset_id}`.`{bigquery_table_name}` (
    """ + ',\n    '.join(column_specs) + "\n)"

        print(query)

        client = bigquery_client(bigquery_db_alias)
        client.query(query)


def replace_dataset(db_alias: str, dataset_id: str, next_dataset_id: str):
    """
    Replaces the a bigquery dataset with the contents of another one.

    Args:
        db_alias: the mara db alias of the bigquery connection
        dataset_id: the dataset that will be replaced
        nextdata_set_id: the contents of the new dataset
    """
    print(f'replacing dataset `{dataset_id}` with contents of `{next_dataset_id}`')
    from mara_db.bigquery import bigquery_client

    client = bigquery_client(db_alias)

    # create target dataset if not exists
    client.create_dataset(dataset=dataset_id, exists_ok=True)

    # all tables in the next dataset
    next_tables = set([table.table_id for table in client.list_tables(next_dataset_id)])

    ddl = '\n'

    # delete tables in target dataset that are not in next dataset
    for table in client.list_tables(dataset_id):
        if table.table_id not in next_tables:
            ddl += f'DROP TABLE `{dataset_id}`.`{table.table_id}`; \n'

    # hopefully atomic operation
    for table_id in next_tables:
        ddl += f'CREATE OR REPLACE TABLE `{dataset_id}`.`{table_id}` AS SELECT * FROM `{next_dataset_id}`.`{table_id}`;\n'
        ddl += f'DROP TABLE `{next_dataset_id}`.`{table_id}`;\n'

    print(ddl)
    client.query(ddl)

    print(f'deleting dataset {next_dataset_id}')
    retries = 1
    # for some reason the 'DROP TABLE ...'  statements take some time, retry the data set deletion
    while True:
        try:
            client.delete_dataset(next_dataset_id)
            return
        except BadRequest as e:
            if retries <= 10:
                print(e, file=sys.stderr)
                seconds_to_sleep = retries * 4
                print(f'Waiting {seconds_to_sleep} seconds')
                time.sleep(seconds_to_sleep)
                retries += 1
            else:
                raise e
