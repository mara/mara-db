SQLite
======



Installation
------------

There are no special requirements for SQLite since it is already included in python.


Configuration examples
----------------------

.. tabs::

    .. group-tab:: Local file

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.SQLiteDB(
                    file_name='database.db'),
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

.. autoclass:: SQLiteDB
    :special-members: __init__
    :inherited-members:
    :members:
