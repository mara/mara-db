Oracle
======


Installation
------------

You have to make sure that the `Oracle Instant Client <https://www.oracle.com/database/technologies/instant-client.html>`_ (`sqlplus64`) is installed.

On Mac, follow `these instructions <https://vanwollingen.nl/install-oracle-instant-client-and-sqlplus-using-homebrew-a233ce224bf>`_. Then `sudo ln -s /usr/local/bin/sqlplus /usr/local/bin/sqlplus64` to make the binary accessible as `sqlplus64`.


Configuration examples
----------------------

.. tabs::

    .. group-tab:: Default

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.OracleDB(
                    host='localhost',
                    user='root',
                    password='<my_strong_password>',
                    endpoint='oracle-endpoint'),
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

.. autoclass:: OracleDB
    :special-members: __init__
    :inherited-members:
    :members:
