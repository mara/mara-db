"""Easy access to BigQuery databases via google.cloud.bigquery"""

import contextlib
import typing
import mara_db.dbs


@contextlib.contextmanager
def bigquery_cursor_context(
        db: typing.Union[str, mara_db.dbs.BigQueryDB]) -> 'google.cloud.bigquery.dbapi.cursor.Cursor':
    """Creates a context with a bigquery cursor for a database alias"""

    from google.cloud import bigquery
    from google.cloud.bigquery import dbapi

    client = bigquery.Client.from_service_account_json(
        json_credentials_path=db.service_account_json
    )
    connection = dbapi.Connection(client)
    cursor = connection.cursor()  # type: google.cloud.bigquery.dbapi.cursor.Cursor
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.close()
        raise e
    finally:
        cursor.close()
        connection.close()
