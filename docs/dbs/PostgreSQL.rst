PostgreSQL
==========

PostgreSQL is the main database engines which is currently installed by default.

.. warning::
    From version 5 the requirements for PostgreSQL will not be installed by default anymore.
    Please make sure to include extras ``postgres`` in your requirements.txt file, see below.


Installation
------------

Use extras `postgres` to install all required packages.

.. code-block:: shell

    $ pip install mara-db[postgres]

The ``psql`` client is required which can be installed on Ubuntu/Debian via

.. code-block:: shell

    $ sudo apt-get install postgresql-client

Configuration examples
----------------------

.. tabs::

    .. group-tab:: Trusted authentication

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.PostgreSQLDB(
                    host='localhost',
                    user='root',
                    database='dwh'),
            }

    .. group-tab:: Password authentication

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.PostgreSQLDB(
                    host='localhost',
                    user='root',
                    password='<my_strong_password>',
                    database='dwh'),
            }

|

|

API reference
-------------

This section contains database specific API in the module.

Configuration
~~~~~~~~~~~~~

.. module:: mara_db.dbs
    :noindex:

.. autoclass:: PostgreSQLDB
    :special-members: __init__
    :inherited-members:
    :members:
