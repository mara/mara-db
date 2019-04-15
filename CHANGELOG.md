# Changelog

## 4.0.0 - 4.0.1 (2019-04-12)

- Allow MARA_AUTOMIGRATE_SQLALCHEMY_MODELS to be a function (in order to improve import speed)
- Change MARA_XXX variables to functions to delay importing of imports
- Fix pg to pg copy command for json data
- Move some imports into the functions that use them in order to improve loading speed
- Remove dependency_links from setup.py to regain compatibility with recent pip versions

**required changes**

- Update `mara-app` to `>=2.0.0`


## 3.2.0 - 3.2.3 (2019-04-11)

- Add oracle db access
- Add SSL standard parameters to PostgreSQL connection string
- Add missing footer parameter to Oracle copy to stdout command
- Change arguments for sqsh client to return non zero exitcode in error case
- Add single quotes around PostgreSQL passwords to prevent bash errors when the password contains certain characters

## 3.1.0 - 3.1.2 (2018-08-30)

- Make graphviz engine in schema visualization selectable
- Implement Redshift DB
- Show enums in schema drawing for constrained tables
- Extend copy_to_stdout_command with "footer" argument for PostgreSQL DB


## 3.0.0 - 3.0.2 (2018-04-27)

- Move sqlalchemy auto-migration from mara-app to mara-db
- Remove `config.mara_db_alias` function
- Move function `sqlalchemy.postgres_cursor_context` to module `postgresql`
- Remove `sqlalchemy/session_context` context handler
- Import graphviz only when needed
- Update / improve documentation
- Add port to sqlalchemy postgres connection string
- Extend copy_to_stdout_command with "header" argument

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


