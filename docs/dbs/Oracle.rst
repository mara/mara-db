Oracle
======


Installation
------------

There are not special requirements for Oracle.


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
