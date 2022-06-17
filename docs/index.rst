.. rst-class:: hide-header

Mara DB documentation
=======================

Welcome to Mara DB’s documentation. This is one of the core modules of the `Mara Framework <https://github.com/mara>`_
for configuring and accessing multiple databases. Decouples the use of databases and their configuration by using "aliases" for databases.

The module ``mara_db.dbs`` contains abstract database configurations for various database backends. The database connections of a project
are configured by overwriting the ``databases`` function in ``mara_db.config``.

.. code-block:: python

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


User's Guide
------------

This part of the documentation focuses on step-by-step instructions how to use this module.

.. toctree::
   :maxdepth: 2

   installation


Databases
---------

This section focuses on the supported database engines.

.. toctree::
   :maxdepth: 2

   databases-overview
   dbs/PostgreSQL
   dbs/Redshift
   dbs/BigQuery
   dbs/Oracle
   dbs/SQLServer
   dbs/Mysql
   dbs/SQLite


API Reference
-------------

If you are looking for information on a specific function, class or
method, this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   api


Additional Notes
----------------

Legal information and changelog are here for the interested.

.. toctree::
   :maxdepth: 2

   license
   changes