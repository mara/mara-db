# Mara DB

Mini package for configuring and accessing multiple databases in a single project. Decouples the use of databases and their configuration by using "aliases" for databases.
 
The file [mara_db/dbs.py](mara_db/dbs.py) contains abstract database configurations for PostgreSQL, Mysql, SQL Server and SQLite. The database connections of a project are configured by overwriting the `databases` function in [mara_db/config.py](mara_db/config.py):

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

## Generating shell commands for accessing databases

The file [mara_db/shell.py](mara_db/shell.py) contains functions that create commands for accessing databases via their command line clients. 
   
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


## Accessing databases with SQLAlchemy

The configured database connections can be used in SQLAlchemy via the functions defined in [mara_db/sqlalchemy.py](mara_db/sqlalchemy.py):

```python
import mara_db.sqlalchemy

## create an sqlalchemy engine for a database configuration
print(mara_db.sqlalchemy.engine('mara'))
# -> Engine(postgresql+psycopg2://root@localhost/mara)


## creates a context that automatically commits or rollbacks an alchemy session
with mara_db.sqlalchemy.session_context(mara_db.dbs.PostgreSQLDB(host='localhost', user='root', database='kfz_dwh_mara')) as session:
    print(session.execute("SELECT 1").scalar())
# -> 1
```


