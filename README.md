# Mara DB

[![Build Status](https://github.com/mara/mara-db/actions/workflows/build.yml/badge.svg)](https://github.com/mara/mara-db/actions/workflows/build.yml)
[![PyPI - License](https://img.shields.io/pypi/l/mara-db.svg)](https://github.com/mara/mara-db/blob/main/LICENSE)
[![PyPI version](https://badge.fury.io/py/mara-db.svg)](https://badge.fury.io/py/mara-db)
[![Slack Status](https://img.shields.io/badge/slack-join_chat-white.svg?logo=slack&style=social)](https://communityinviter.com/apps/mara-users/public-invite)

Mini package for configuring and accessing multiple databases in a single project. Decouples the use of databases and their configuration by using "aliases" for databases.
 
The file [mara_db/dbs.py](https://github.com/mara/mara-db/blob/main/mara_db/dbs.py) contains abstract database configurations for PostgreSQL, Mysql, SQL Server, Oracle, SQLite and Big Query. The database connections of a project are configured by overwriting the `databases` function in [mara_db/config.py](https://github.com/mara/mara-db/blob/main/mara_db/config.py):

```python
import mara_db.config
import mara_db.dbs

## configure database connections for different aliases
mara_db.config.databases = lambda: {
    'mara': mara_db.dbs.PostgreSQLDB(host='localhost', user='root', database='mara'),
    'dwh': mara_db.dbs.PostgreSQLDB(database='dwh'),
    'source-1': mara_db.dbs.MysqlDB(host='some-localhost', database='my_app', user='dwh'),
    'source-2': mara_db.dbs.SQLServerDB(user='dwh_read', password='123abc', database='db1', host='some-sql-server')
}

## access individual database configurations with `dbs.db`:
print(mara_db.dbs.db('mara'))
# -> <PostgreSQLDB: host=localhost, database=mara>
```

&nbsp;


## Visualization of (PostgreSQL, MySQL, SQL Server) database schemas 

[mara_db/views.py](https://github.com/mara/mara-db/blob/main/mara_db/views.py) contains a schema visualization for all configured databases using graphviz (currently PostgreSQL, Mysql and SQL Server only). It basically show tables of selected schemas together with the foreign key relations between them. 


![Schema visualization](https://github.com/mara/mara-db/blob/main/docs/_static/schema-visualization.png)

For finding missing foreign key constraints, columns that follow a specific naming pattern (configurable via `config.schema_ui_foreign_key_column_regex`, default `*_fk`) and that are not part of foreign key constraints are drawn in pink.    

&nbsp;


## Fast batch processing: Accessing databases with shell commands

The file [mara_db/shell.py](https://github.com/mara/mara-db/blob/main/mara_db/shell.py) contains functions that create commands for accessing databases via their command line clients. 
   
For example, the `query_command` function creates a shell command that can receive an SQL query from stdin and execute it:

```python
import mara_db.shell

print(mara_db.shell.query_command('source-1'))
# -> mysql --default-character-set=utf8mb4 --user=dwh --host=some-localhost my_app

print(mara_db.shell.query_command('dwh', timezone='Europe/Lisbon', echo_queries=False))
# -> PGTZ=Europe/Lisbon PGOPTIONS=--client-min-messages=warning psql  --no-psqlrc --set ON_ERROR_STOP=on dwh
```

The function `copy_to_stdout_command` creates a shell command that receives a query on stdin and writes the result to stdout in tabular form:

```python
print(mara_db.shell.copy_to_stdout_command('source-1'))
# -> mysql --default-character-set=utf8mb4 --user=dwh --host=some-localhost my_app --skip-column-names
```

Similarly, `copy_from_stdin_command` creates a client command that receives tabular data from stdin and and writes it to a target table: 

```python
print(mara_db.shell.copy_from_stdin_command('dwh', target_table='some_table', delimiter_char=';'))
# -> PGTZ=Europe/Berlin PGOPTIONS=--client-min-messages=warning psql --echo-all --no-psqlrc --set ON_ERROR_STOP=on dwh \
#      --command="COPY some_table FROM STDIN WITH DELIMITER AS ';'"
```

Finally, `copy_command` creates a shell command that receives a sql query from stdin, executes the query in `source_db` and then writes the result of to `target_table` in `target_db`:

```python
print(mara_db.shell.copy_command('source-2', 'dwh', target_table='some_table'))
# -> sed 's/\\\\$/\$/g;s/\$/\\\\$/g' \
#   | sqsh  -U dwh_read -P 123abc -S some-sql-server -D db1 -m csv \
#   | PGTZ=Europe/Berlin PGOPTIONS=--client-min-messages=warning psql --echo-all --no-psqlrc --set ON_ERROR_STOP=on dwh \
#         --command = "COPY some_table FROM STDIN WITH CSV HEADER"
```

&nbsp;


The following **command line clients** are used to access the various databases:

| Database | Client binary | Comments |  
| --- | --- | --- |
| Postgresql / Redshift | `psql` | Included in standard distributions. |
| MariaDB / Mysql | `mysql` | Included in standard distributions. |
| SQL Server | `sqsh`<br>- or -<br>`sqlcmd` | **sqsh**: From [https://sourceforge.net/projects/sqsh/](https://sourceforge.net/projects/sqsh/), usually messy to get working. On ubuntu, use [http://ppa.launchpad.net/jasc/sqsh/ubuntu/](http://ppa.launchpad.net/jasc/sqsh/ubuntu/) backport. On Mac, try the homebrew version or install from source.<br>**sqlcmd**: Official Microsoft Utility for SQL Server. See [sqlcmd Utility](https://docs.microsoft.com/en-us/sql/tools/sqlcmd-utility) |
| Oracle | `sqlplus64` | See the [Oracle Instant Client](https://www.oracle.com/technetwork/database/database-technologies/instant-client/overview/index.html) homepage for details. On Mac, follow [these instructions](https://vanwollingen.nl/install-oracle-instant-client-and-sqlplus-using-homebrew-a233ce224bf). Then ` sudo ln -s /usr/local/bin/sqlplus /usr/local/bin/sqlplus64` to make the binary accessible as `sqlplus64`. |
| SQLite | `sqlite3` | Available in standard distributions. Version >3.20.x required (not the case on Ubuntu 14.04). |
| Big Query | `bq` | See the [Google Cloud SDK](https://cloud.google.com/sdk/docs/quickstarts) page for details. |
| Snowflake | `snowsql` | See [SnowSQL (CLI Client)](https://docs.snowflake.com/en/user-guide/snowsql.html) |

&nbsp;


## Make it so! Auto-migration of SQLAlchemy models

[Alembic has a feature](http://alembic.zzzcomputing.com/en/latest/autogenerate.html) that can create a diff between the state of a database and the ORM models of an application. This feature is used in [mara_db/auto_migrate.py](https://github.com/mara/mara-db/blob/main/mara_db/auto_migrate.py) to automatically perform all necessary database transformations, without intermediate migration files:

```python
# define a model / table
class MyTable(sqlalchemy.ext.declarative.declarative_base()):
    __tablename__ = 'my_table'
    my_table_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    column_1 = sqlalchemy.Column(sqlalchemy.TEXT, nullable=False, index=True)


db = mara_db.dbs.SQLiteDB(file_name='/tmp/test.sqlite')

# create database and table 
mara_db.auto_migration.auto_migrate(engine=mara_db.auto_migration.engine(db), models=[MyTable])
# ->
# Created database "sqlite:////tmp/test.sqlite"
#
# CREATE TABLE my_table (
#     my_table_id SERIAL NOT NULL,
#     column_1 TEXT NOT NULL,
#     PRIMARY KEY (my_table_id)
# );
#
# CREATE INDEX ix_my_table_column_1 ON my_table (column_1);
```

When the model is changed later, then `auto_migrate` creates a diff against the existing database and applies it:

```python    
# remove index and add another column
class MyTable(sqlalchemy.ext.declarative.declarative_base()):
    __tablename__ = 'my_table'
    my_table_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    column_1 = sqlalchemy.Column(sqlalchemy.TEXT, nullable=False)
    column_2 = sqlalchemy.Column(sqlalchemy.Integer)

auto_migrate(engine=engine(db), models=[MyTable])
# ->
# ALTER TABLE my_table ADD COLUMN column_2 INTEGER;
#
# DROP INDEX ix_my_table_text_column_1;
```

**Use with care**! The are lot of changes [that alembic auto-generate can not detect](http://alembic.zzzcomputing.com/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect). We recommend testing each aut-migration on a staging system first before deploying to production. Sometimes manual migration scripts will be necessary.
 


## Installation

```bash
pip install mara-db
```

or

```bash
pip install git+https://github.com/mara/mara-db.git
```

### Optional: Installation of requirements for SQL Server

For usage with SQL Server, the python module pyodbc and a odbc driver (e.g. Microsoft ODBC Driver 17 for SQL Server) is required which is not included in the general requirement.

To see how to install pyodbc, take a look into [this install guide](https://github.com/mkleehammer/pyodbc/wiki/Install).
To see how to install ODBC 17, take a look into [Installing the Microsoft ODBC Driver for SQL Server on Linux and macOS](https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15).

On Linux, you most likely will have to deal with an SSL issue, see [this issue](https://github.com/microsoft/msphpsql/issues/1023). A quick, dirty option in a test/development environment could be to [disable the requirement for TLS 1.2](https://github.com/microsoft/msphpsql/issues/1023#issuecomment-523214695).

### Optional: Installation of requirements for BigQuery

For usage with BigQuery, the official `bq` and `gcloud` clients are required.
See the [Google Cloud SDK](https://cloud.google.com/sdk/docs/quickstarts) page for installation details.

Enabling the BigQuery API and Service account JSON credentials are also required as listed 
in the official documentation [here](https://cloud.google.com/bigquery/docs/quickstarts/quickstart-client-libraries#before-you-begin).

One time authentication of the service-account used:
```cmd
gcloud auth activate-service-account --key-file='path-to/service-account.json'
```

Optionally, for loading data from files into BigQuery, the `gcloud_gcs_bucket_name` can be specified in the database initialization.
This will use the Google Cloud Storage bucket specified as cache for loading data and over-coming potential limitations.
For more see [loading-data](https://cloud.google.com/bigquery/docs/bq-command-line-tool#loading_data). 
By default, files will directly loaded locally as described in [loading-local-data](https://cloud.google.com/bigquery/docs/loading-data-local#loading_data_from_a_local_data_source).

A BigQuery context with a python cursor is also available on demand for easy access to BigQuery databases.
In order to use, install the official Google python client library: [google-cloud-bigquery](https://cloud.google.com/bigquery/docs/reference/libraries#client-libraries-install-python).
