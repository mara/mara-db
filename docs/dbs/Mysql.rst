MySQL
=====


Installation
------------

Use extras `mysql` to install all required packages.

.. code-block:: shell

    $ pip install mara-db[mysql]


Configuration examples
----------------------

.. tabs::

    .. group-tab:: Default

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.MysqlDB(
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

.. module:: mara_db.mysql

Configuration
~~~~~~~~~~~~~

.. module:: mara_db.dbs
    :noindex:

.. autoclass:: MysqlDB
    :special-members: __init__
    :inherited-members:
    :members:
