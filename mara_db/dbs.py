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

    @property
    def sqlalchemy_url(self):
        """Returns the SQLAlchemy url for a database"""
        raise NotImplementedError(f'Please implement sqlalchemy_url for type "{self.__class__.__name__}"')

    def connect(self) -> object:
        """
        Constructor for creating a connection to the database.
        The returned connection object is PIP-249 compatible (DB-API).

        See also: https://peps.python.org/pep-0249/#connection-objects
        """
        raise NotImplementedError(f'Please implement connect for type "{self.__class__.__name__}"')

    def cursor_context(self) -> object:
        """
        A single iteration with a cursor context. When the iteration is
        closed, a commit is executed on the cursor.

        Example usage:
           with db.cursor_context() as c:
             c.execute('UPDATE table SET table.c1 = 1 WHERE table.id = 5')
        """
        connection = self.connect()
        try:
            cursor = connection.cursor()
            yield cursor
        except Exception:
            connection.rollback()
            raise
        else:
            connection.commit()
        finally:
            cursor.close()
            connection.close()


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

    @property
    def sqlalchemy_url(self):
        return (f'postgresql+psycopg2://{self.user}{":" + self.password if self.password else ""}@{self.host}'
                + f'{":" + str(self.port) if self.port else ""}/{self.database}')
    
    def connect(self) -> 'psycopg2.extensions.cursor':
        import psycopg2
        return psycopg2.connect(dbname=self.database, user=self.user, password=self.password,
                                host=self.host, port=self.port)


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
    def __init__(self,
                 service_account_json_file_name: str,
                 location: str = None, project: str = None, dataset: str = None,
                 gcloud_gcs_bucket_name=None, use_legacy_sql: bool = False):
        """
        Connection information for a BigQueryDB database

        Enabling the BigQuery API and Service account json credentials are required. For more:
        https://cloud.google.com/bigquery/docs/quickstarts/quickstart-client-libraries#before-you-begin

        Args:
            service_account_json_file_name: The name of the private key file provided by Google when creating a service account (in json format)
            location: Default geographic location to use when creating datasets or determining where jobs should run
            project: Default project to use for requests.
            dataset: Default dataset to use for requests.
            gcloud_gcs_bucket_name: The Google Cloud Storage bucked used as cache for loading data
            use_legacy_sql: (default: false) If true, use the old BigQuery SQL dialect is used.
        """
        self.service_account_json_file_name = service_account_json_file_name
        self.location = location
        self.project = project
        self.dataset = dataset
        self.gcloud_gcs_bucket_name = gcloud_gcs_bucket_name
        self.use_legacy_sql = use_legacy_sql

    @property
    def sqlalchemy_url(self):
        url = 'bigquery://'
        if self.project:
            url += self.project
            if self.dataset:
                url += '/' + self.dataset
        return url

    def connect(self):
        from google.oauth2.service_account import Credentials
        from google.cloud.bigquery.client import Client
        from google.cloud.bigquery.dbapi.connection import Connection
        credentials = Credentials.from_service_account_file(self.service_account_json_file_name)
        client = Client(project=credentials.project_id, credentials=credentials, location=self.location)
        return Connection(client)


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
    
    def connect(self) -> 'MySQLdb.cursors.Cursor':
        import MySQLdb.cursors # requires https://github.com/PyMySQL/mysqlclient-python
        return MySQLdb.connect(
            host=self.host, user=self.user, passwd=self.password, db=self.database, port=self.port,
            cursorclass=MySQLdb.cursors.Cursor)


class SQLServerDB(DB):
    def __new__(cls, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None, odbc_driver: str = None,
                 **kargs):
        """
        Connection information for a SQL Server database
        """
        if cls is SQLServerDB:
            # Here we define what happens when the class is directly created in code
            # 
            # We defined here that class SqshSQLServerDB shall be used by default. In a newer
            # major version we could change this to SqlcmdSQLServerDB but we do not want to
            # introduce a breaking change here at this point.
            return SqshSQLServerDB(host=host, port=port, database=database, user=user, password=password, odbc_driver=odbc_driver)
        else:
            # This is called when the class is created from a derived class (e.g. SqshSQLServerDB)
            return super(SQLServerDB, cls).__new__(cls)

    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None, odbc_driver: str = None):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        if odbc_driver is None:
            self.odbc_driver = 'ODBC Driver 17 for SQL Server' # default odbc driver
        else:
            self.odbc_driver = odbc_driver

    @property
    def sqlalchemy_url(self):
        import urllib.parse
        port = self.port if self.port else 1433
        driver = self.odbc_driver.replace(' ','+')
        return f'mssql+pyodbc://{self.user}:{urllib.parse.quote(self.password)}@{self.host}:{port}/{self.database}?driver={driver}'

    def connect(self) -> 'pyodbc.Cursor':
        import pyodbc # requires https://github.com/mkleehammer/pyodbc/wiki/Install
        server = self.host
        if self.port: # connecting via TCP/IP port
            server = f"{server},{self.port}"
        return pyodbc.connect(f"DRIVER={{{self.odbc_driver}}};SERVER={server};DATABASE={self.database};UID={self.user};PWD={self.password}" \
                                + (';Encrypt=YES;TrustServerCertificate=YES' if self.trust_server_certificate else ''))


class SqshSQLServerDB(SQLServerDB):
    def __init__(self, host: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None, odbc_driver: str = None):
        """
        Connection information for a SQL Server database using the unix package sqsh
        """
        # NOTE: The support for named instances is not added because the command `sqsh` does not support it
        super().__init__(host=host, port=port, database=database, user=user, password=password, odbc_driver=odbc_driver)


class SqlcmdSQLServerDB(SQLServerDB):
    def __init__(self, host: str = None, instance: str = None, port: int = None, database: str = None,
                 user: str = None, password: str = None, odbc_driver: str = None,
                 protocol: str = None, quoted_identifier: bool = True,
                 trust_server_certificate: bool = False):
        """
        Connection information for a SQL Server database using the MSSQL Tools e.g. sqlcmd

        Args:
            quoted_identifier: If set to true, the SET option QUOTED_IDENTIFIER is set to ON, otherwise OFF.
            protocol: can be tcp (TCP/IP connection), np (named pipe) or lcp (using shared memory). See as well: https://docs.microsoft.com/en-us/sql/ssms/scripting/sqlcmd-connect-to-the-database-engine?view=sql-server-ver15
            trust_server_certificate: Trust the server certificate without validation
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
        self.trust_server_certificate = trust_server_certificate

    @property
    def sqlalchemy_url(self):
        return super().sqlalchemy_url \
                + ('&TrustServerCertificate=yes' if self.trust_server_certificate else '')


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

    @property
    def sqlalchemy_url(self):
        return f'sqlite:///{self.file_name}'
    
    def connect(self):
        import sqlite3
        return sqlite3.connect(database=self.file_name)


class SnowflakeDB(DB):
    """A database connection to a Snowflake database"""
    def __init__(self, connection: str = None, account: str = None, user: str = None, password: str = None, database: str = None,
                 private_key_file: str = None, private_key_passphrase: str = None) -> None:
        """
        Connection information for a Snowflake database

        Args:
            connection: The connection name definend in the snowsql configuration ~/.snowsql/config
            account: The account identifier. See here: https://docs.snowflake.com/en/user-guide/admin-account-identifier.html
            user: The user name
            password: The password of the user
            database: The database name
            private_key_file: Path to private key file in PEM format used for key pair authentication. The private key file must be encrypted.
            private_key_passphrase: The passphrase for the private key file.
        """
        self.connection = connection
        self.account = account
        self.user = user
        self.password = password
        self.database = database
        self.private_key_file = private_key_file
        self.private_key_passphrase = private_key_passphrase

    @property
    def sqlalchemy_url(self):
        assert all(v is not None for v in [self.account, self.user, self.password]), "sqlalchemy_url for SnowflakeDB requires a user, password and account"
        return (f'snowflake://{self.user}:{self.password}@{self.account}'
                + (f'/{self.database}' if self.database else ''))


class DatabricksDB(DB):
    """A database connection to a Databricks"""
    def __init__(self, host: str = None, http_path: str = None, access_token: str = None) -> None:
        """
        Connection information for a Databricks

        Args:
            host: The hostname
            http_path: The http path
            access_token: The Access Token
        """
        self.host = host
        self.http_path = http_path
        self.access_token = access_token

    @property
    def sqlalchemy_url(self):
        return f"databricks+connector://token:{self.access_token}@{self.host}:443/"

    def connect(self):
        from databricks_dbapi import odbc
        return odbc.connect(
            host=self.host,
            http_path=self.http_path,
            token=self.access_token,
            driver_path=self.odbc_driver_path)
