Databricks
==========


Installation
------------

Use extras `databricks` to install all required packages.

.. code-block:: shell

    $ pip install mara-db[databricks]

The official `dbsqlcli` client is required. See the `Install the Databricks SQL CLI <https://docs.databricks.com/dev-tools/databricks-sql-cli.html#install-the-databricks-sql-cli>`_ page for installation details.


Configuration examples
----------------------

.. tabs::

    .. group-tab:: Use access token

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.DatabricksDB(
                    host='dbc-a1b2345c-d6e78.cloud.databricks.com',
                    http_path='/sql/1.0/warehouses/1abc2d3456e7f890a',
                    access_token='dapi1234567890b2cd34ef5a67bc8de90fa12b'),
            }

    .. group-tab:: Environment variables

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.DatabricksDB(),
            }

        You need to define the environment variables `DBSQLCLI_HOST_NAME`, `DBSQLCLI_HTTP_PATH` and `DBSQLCLI_ACCESS_TOKEN`. See as well `Environment variables <https://docs.databricks.com/dev-tools/databricks-sql-cli.html#environment-variables>`_

    .. group-tab:: Settings file

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.DatabricksDB(),
            }
        
        You need to define the database connection in the `dbsqlclirc` settings file. See as well `Settings file <https://docs.databricks.com/dev-tools/databricks-sql-cli.html#settings-file>`_. Note that using a custom settings file is currently not supported in Mara.

|

|

API reference
-------------

This section contains database specific API in the module.

.. module:: mara_db.databricks

Configuration
~~~~~~~~~~~~~

.. module:: mara_db.dbs
    :noindex:

.. autoclass:: DatabricksDB
    :special-members: __init__
    :inherited-members:
    :members:


Cursor context
~~~~~~~~~~~~~~

.. module:: mara_db.databricks
    :noindex:

.. autofunction:: databricks_cursor_context
