SQLite
======



Installation
------------

Use extras `duckdb` to install all required packages.

.. code-block:: shell

    $ pip install mara-db[duckdb]

The shell command `duckdb` is required. You can find installation instructions at [DuckDB Install]

[DuckDB Install]: https://duckdb.org/install/?environment=cli

Configuration examples
----------------------

.. tabs::

    .. group-tab:: Local file

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.DuckDB(
                    file_name='database.duckdb'),
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

.. autoclass:: DuckDB
    :special-members: __init__
    :inherited-members:
    :members:
