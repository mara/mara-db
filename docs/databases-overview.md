Overview
========

The following database engines are supported:

| Database                  | Configuration class | SQLAlchemy Engine / dialect |
| ------------------------- | ------------------- | --------------------------- |
| [PostgreSQL]              | PostgreSQLDB        | postgresql+psycopg2
| [Amazon Redshift]         | RedshiftDB          | postgresql+psycopg2
| [Google Big Query]        | BigQueryDB          | bigquery
| [Databricks]              | DatabricksDB        | databricks+connector
| [MariaDB]                 | MysqlDB             | -
| [MySQL]                   | MysqlDB             | -
| [Microsoft SQL Server]    | SQLServerDB         | mssql+pyodbc
| [Azure Synapse Analytics] | SQLServerDB         | mssql+pyodbc
| [Oracle Database]         | OracleDB            | -
| [Snowflake]               | SnowflakeDB         | snowflake
| [SQLite]                  | SQLiteDB            | sqlite


[PostgreSQL]: https://www.postgresql.org/
[Amazon Redshift]: https://aws.amazon.com/de/redshift/
[Google Big Query]: https://cloud.google.com/bigquery
[Databricks]: https://www.databricks.com/
[MariaDB]: https://mariadb.com/
[MySQL]: https://www.mysql.com/
[Oracle Database]: https://www.oracle.com/database/
[Snowflake]: https://www.snowflake.com/
[SQLite]: https://www.sqlite.org/
[Microsoft SQL Server]: https://www.microsoft.com/en-us/sql-server
[Azure Synapse Analytics]: https://azure.microsoft.com/en-us/services/synapse-analytics/


Function support matrix
-----------------------

Shows which functions are supported with which database engine:

| Configuration class | Querying | Write STDOUT | Read STDIN | DB-API 2.0 | UI schema support |
| ------------------- | -------- | ------------ | ---------- | ---------- | ----------------- |
| PostgreSQLDB        | Yes      | Yes          | Yes        | Yes        | Yes
| RedshiftDB          | Yes      | Yes          | Yes        | Yes        | Yes
| BigQueryDB          | Yes      | Yes          | Yes        | Yes        | *no foreign key support by engine*
| DatabricksDB        | Yes      | Yes          | -          | Yes        |
| MysqlDB             | Yes      | Yes          | -          | Yes        | Yes
| SQLServerDB         | Yes      | Yes          | Yes        | Yes        | Yes
| OracleDB            | Yes      | Yes          | -          | -          |
| SnowflakeDB         | Yes      | Yes          | -          | -          |
| SQLiteDB            | Yes      | Yes          | -          | Yes        |

*Write STDOUT* gives the possibility to write a query to STDOUT

*Read STDIN* gives the possiblity to read a file to a predefined SQL table


Format support
--------------

Shows the formats supported per database engine

### Read STDIN

| Configuration class | CSV | JsonL | Avro | Parquet | ORC |
| ------------------- | ----| ----- | ---- | ------- | --- |
| PostgreSQLDB        | Yes | Yes   | -    | -       | -   |
| RedshiftDB          | Yes | Yes   | -    | -       | -   |
| BigQueryDB          | Yes | Yes   | Yes  | Yes     | Yes |
| SQLServerDB         | Yes | -     | -    | -       | -   |


### Write STDOUT

| Configuration class | CSV | JsonL | Avro | Parquet | ORC |
| ------------------- | ----| ----- | ---- | ------- | --- |
| PostgreSQLDB        | Yes | -     | -    | -       | -   |
| RedshiftDB          | Yes | -     | -    | -       | -   |
| BigQueryDB          | Yes | -     | -    | -       | -   |
| DatabricksDB        | Yes | -     | -    | -       | -   |
| MysqlDB             | Yes | -     | -    | -       | -   |
| SQLServerDB         | Yes | -     | -    | -       | -   |
| OracleDB            | Yes | -     | -    | -       | -   |
| SnowflakeDB         | Yes | -     | -    | -       | -   |
| SQLiteDB            | Yes | -     | -    | -       | -   |


Copy matrix
-----------

Shows which copy operations are implemented by default.

| from / to    | PostgreSQLDB | RedshiftDB | BigQueryDB | DatabricksDB | MysqlDB | SQLServerDB | OracleDB | SnowflakeDB | SQLiteDB |
| ------------ | ------------ | ---------- | ---------- | ------------ | ------- | ----------- | -------- | ----------- | -------- |
| PostgreSQLDB | Yes          | Yes        | Yes        | -            | -       | -           | -        | -           | -        |
| RedshiftDB   | Yes          | Yes        | Yes        | -            | -       | -           | -        | -           | -        |
| BigQueryDB   | Yes          | Yes        | -          | -            | -       | -           | -        | -           | -        |
| DatabricksDB | -            | -          | -          | -            | -       | -           | -        | -           | -        |
| MysqlDB      | Yes          | Yes        | Yes        | -            | -       | -           | -        | -           | -        |
| SQLServerDB  | Yes          | Yes        | Yes        | -            | -       | -           | -        | -           | -        |
| OracleDB     | Yes          | Yes        | Yes        | -            | -       | -           | -        | -           | -        |
| SnowflakeDB  | -            | -          | -          | -            | -       | -           | -        | -           | -        |
| SQLiteDB     | Yes          | Yes        | Yes        | -            | -       | -           | -        | -           | -        |
