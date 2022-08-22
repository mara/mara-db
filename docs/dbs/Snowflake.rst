Snowflake
=========


Installation
------------

Use extras `snowflake` to install all required packages.

.. code-block:: shell

    $ pip install mara-db[snowflake]

The official `snowsql` client is required. See the `Installing SnowSQL <https://docs.snowflake.com/en/user-guide/snowsql-install-config.html>`_ page for installation details.


Configuration examples
----------------------

.. tabs::

    .. group-tab:: Use account

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.SnowflakeDB(
                    account='kaXXXXX.regio.cloud',
                    user='<user>',
                    password='<my_strong_password>',
                    database='dwh'),
            }

    .. group-tab:: Private key file

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.BigQueryDB(
                    account='kaXXXXX.regio.cloud',
                    user='<user>',
                    private_key_file='<path>/rsa_key.p8',
                    private_key_passphrase='<passphrase>',
                    database='dwh'),
            }

    .. group-tab:: Local connection configuration

        You can configure a named connection in the snowsql config file. See `here <https://docs.snowflake.com/en/user-guide/snowsql-start.html#label-connecting-named-connection>`_.

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.BigQueryDB(
                    connection='my_example_connection',
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

.. autoclass:: SnowflakeDB
    :special-members: __init__
    :inherited-members:
    :members:
