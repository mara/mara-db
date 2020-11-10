"""Abstract definition of database connections"""

import functools
import pathlib


@functools.lru_cache(maxsize=None)
def db(alias):
    """Returns a database configuration by alias"""
    from . import config
    databases = config.databases()
    if alias not in databases:
        raise KeyError(f'database alias "{alias}" not configured')
    return databases[alias]


class DB:
    """Generic database connection definition"""

    def __repr__(self) -> str:
        return (f'<{self.__class__.__name__}: '
                + ', '.join([f'{var}={"*****" if (var == "password" or "secret" in var) else getattr(self, var)}'
                             for var in vars(self) if getattr(self, var)])
                + '>')


class PostgreSQLDB(DB):
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None,
                 sslmode: str = None, sslrootcert: str = None, sslcert: str = None, sslkey: str = None):
        """
        Connection information for a PostgreSQL database

        For the SSL options, see https://www.postgresql.org/docs/current/libpq-ssl.html#LIBPQ-SSL-PROTECTION
        """
        self.host = host
        self.database = database
        self.port = port
        self.user = user
        self.password = password

        self.sslmode = sslmode
        self.sslrootcert = sslrootcert
        self.sslcert = sslcert
        self.sslkey = sslkey


class RedshiftDB(PostgreSQLDB):
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None,
                 aws_access_key_id=None, aws_secret_access_key=None, aws_s3_bucket_name=None):
        """
        Connection information for a RedShift database

        The aws_* parameters are for copying to Redshift from stdin via an s3 bucket
        (requires the https://pypi.org/project/awscli/) package to be installed)
        """
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_s3_bucket_name = aws_s3_bucket_name
        super(RedshiftDB, self).__init__(host, port, database, user, password)


class BigQueryDB(DB):
    def __init__(self, location: str = None, project: str = None, dataset: str = None,
                 gcloud_gcs_bucket_name=None, service_account_private_key_file: str = None,
                 use_legacy_sql: bool = False):
        """
        Connection information for a BigQueryDB database

        Enabling the BigQuery API and Service account json credentials are required. For more:
        https://cloud.google.com/bigquery/docs/quickstarts/quickstart-client-libraries#before-you-begin

        Args:
            location: Default geographic location to use when creating datasets or determining where jobs should run
            project: Default project to use for requests.
            dataset: Default dataset to use for requests.
            service_account_private_key_file: The private key file provided by Google when creating a service account. (it's a JSON file).
            gcloud_gcs_bucket_name: The Google Cloud Storage bucked used as cache for loading data
            use_legacy_sql: (default: false) If true, use the old BigQuery SQL dialect is used.
        """
        self.service_account_private_key_file = service_account_private_key_file
        self.location = location
        self.project = project
        self.dataset = dataset
        self.gcloud_gcs_bucket_name = gcloud_gcs_bucket_name
        self.use_legacy_sql = use_legacy_sql


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
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None, odbc_driver: str = None):
        # NOTE: The support for named instances is not added because the command `sqsh` does not support it
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        if odbc_driver is None:
            self.odbc_driver = 'ODBC Driver 17 for SQL Server' # default odbc driver
        else:
            self.odbc_driver = odbc_driver


class SqlcmdSQLServerDB(SQLServerDB):
    def __init__(self, host: str = None, instance: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None, odbc_driver: str = None,
                 protocol: str = None, quoted_identifier: bool = True):
        """
        Args:
            quoted_identifier: If set to true, the SET option QUOTED_IDENTIFIER is set to ON, otherwise OFF.
            protocol: can be tcp (TCP/IP connection), np (named pipe) or lcp (using shared memory). See as well: https://docs.microsoft.com/en-us/sql/ssms/scripting/sqlcmd-connect-to-the-database-engine?view=sql-server-ver15
        """
        super().__init__(host=host, port=port, database=database, user=user, password=password, odbc_driver=odbc_driver)
        if protocol:
            if protocol not in ['tcp','np','lpc']:
                raise ValueError(f'Not supported protocol: {protocol}')
            if protocol == 'tcp' and instance:
                raise ValueError(f'You can not use protocol tcp with an instance name')
            if protocol in ['np','lcp'] and port:
                raise ValueError(f'You can not use protocol np/lcp with a port number')
        if instance is not None and port is not None:
            raise ValueError('You can only use instance or port, not both together')
        self.protocol = protocol
        self.quoted_identifier = quoted_identifier
        self.instance = instance


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
