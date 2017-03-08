# Mara DB

Mini package that "owns" the configuration and monitoring of database connections. Decouples the use of databases 
and their configuration by using "aliases" for databases. 

```
from mara_db import dbs

with dbs.session_context('mara') as session: 
    print(session.execute("SELECT 1").scalar())
```      


