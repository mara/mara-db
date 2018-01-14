# Changelog

## 2.0.1
*2017-01-14*

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


