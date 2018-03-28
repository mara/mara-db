# Changelog

## 2.2.3
*2018-03-28*

- Quote strings when copying from sqlite 

## 2.2.2
*2018-03-27*

- Fix bug in schema drawing


## 2.2.1
*2018-03-19*

- improve acl


## 2.2.0

- add web ui for visualizing database schemas (postgres only currently)


## 2.1.3
*2018-02-07*

- remove default-character-set=utf8mb4 from My SQL queries


## 2.1.2
*2018-01-26*

- always append ';\n\go' to queries against SQL Server


## 2.1.1
*2018-01-23*

- don't use sqlalchemy session in postgres_cursor_context because it creates to many setup queries on each instantiation


## 2.1.0
*2018-01-19*

- add SQLite support

## 2.0.1
*2018-01-14*

- various smaller improvements in mara_db/shell.py


## 2.0.0
*2017-12-20*

- change database configuration from sqalchemy urls to custom database specific classes
- create sqlalchemy session contexts from configuration objects
- add functions for creating shell commands for accessing databases
- add documentation
- bug fixes

**required changes**

This version is pretty much incompatible with previous versions. See README.md for new usage patterns.


## 1.1.0 
*2017-12-04*

- replaced config function databases with database_urls
- added functions for client command creation
 
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


## 1.0.1
*2017-04-05*

- Minor bug fixes and code style issues


## 1.0.0 
*2017-03-08* 

- Initial version


