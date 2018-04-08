# Changelog

## 3.0.0 (2018-04-09)

- Move sqlalchemy auto-migration from mara-app to mara-db
- Remove `config.mara_db_alias` function
- Move function `sqlalchemy.postgres_cursor_context` to module `postgresql`
- Remove `sqlalchemy/session_context` context handler
- Import graphviz only when needed
- Update / improve documentation

**required changes**

- Replace all occurrences of `mara_db.config.mara_db_alias()` with `'mara'`
- Replace `mara_db.sqlalchemy.postgres_cursor_context` with `mara_db.postgresql.postgres_cursor_context`
- Change all usages of `mara_db.sqlalchemy.session_context` to psycopg2 using `mara_db.postgresql.postgres_cursor_context`


## 2.3.0 - 2.3.1 (2018-04-03)

- Switch dependency links in setup.py from ssh to https
- Add psycopg2 as dependency



## 2.2.0 (2018-02-28)

- add web ui for visualizing database schemas (postgres only currently)
- improve acl
- Fix bug in schema drawing
- Quote strings when copying from sqlite 
- NULL value handling when copying from sqlite 



## 2.1.0 - 2.1.3 (2018-01-19)

- add SQLite support
- don't use sqlalchemy session in postgres_cursor_context because it creates to many setup queries on each instantiation
- always append ';\n\go' to queries against SQL Server
- remove default-character-set=utf8mb4 from My SQL queries


## 2.0.0 - 2.0.1 (2017-12-20)

- change database configuration from sqalchemy urls to custom database specific classes
- create sqlalchemy session contexts from configuration objects
- add functions for creating shell commands for accessing databases
- add documentation
- bug fixes
- various smaller improvements in mara_db/shell.py

**required changes**

This version is pretty much incompatible with previous versions. See README.md for new usage patterns.


## 1.1.0 (2017-12-04)

- Replace config function databases with database_urls
- Add functions for client command creation
 
**required changes**

- Change database configurations from

```python
from sqlalchemy import engine
 
def databases() -> {str: engine.Engine}:
     """The list of database connections to use, by alias"""
    return {'mara': engine.create_engine('postgresql+psycopg2://root@localhost/mara')}

```

to

```python
import sqlalchemy.engine.url
 
def database_urls() -> {str: sqlalchemy.engine.url}:
     """The list of database connections to use, by alias"""
    return {'mara': sqlalchemy.engine.url.make_url('postgresql+psycopg2://root@localhost/mara')}
```

## 1.0.0 - 1.0.1 (2017-03-08) 

- Initial version
- Minor bug fixes and code style issues


