Microsoft SQL Server
====================

There are two ways to use SQL Server with mara:

1. using the official MSSQL Tools for SQL Server on linux (`sqlcmd`, `bcp`)
2. using the linux sql client tool `sqsh` (legacy)

Currently by default `sqsh` is used. This will be changed in a future version to the official MSSQL Tools from Microsoft. You can explicitly
specify the client tool you want to use, see below.


Prerequisites
-------------

On Ubuntu/Debian make sure you have the ODBC header files before installing

.. code-block:: shell

    $ sudo apt install unixodbc-dev

The python module `pyodbc <https://pypi.org/project/pyodbc/>`_ requires a ODBC driver to be installed. By default Microsoft ODBC Driver 17 for SQL Server is used. You can find the installation guide here:
`Installing the Microsoft ODBC Driver for SQL Server (Linux) <https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver15>`_.


Installation
------------

Use extras `mssql` to install all required packages.

.. code-block:: shell

    $ pip install mara-db[mssql]

Use MSSQL Tools
~~~~~~~~~~~~~~~

To see how to install the MSSQL Tools, follow this guide:
`Install the SQL Server command-line tools sqlcmd and bcp on Linux <https://docs.microsoft.com/en-us/sql/linux/sql-server-linux-setup-tools>`_


Use sqsh
~~~~~~~~
To install the `sqsh` shell tool, see here https://sourceforge.net/projects/sqsh/. Usually messy to get working.
On ubuntu, use http://ppa.launchpad.net/jasc/sqsh/ubuntu/ backport. On Mac, try the homebrew version or install from source.


Configuration examples
----------------------

.. tabs::

    .. group-tab:: Default

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.SQLServerDB(
                    host='localhost',
                    user='sa',
                    password='<my_strong_password>',
                    database='dwh'),
            }

            # explicitly define to use the MSSQL Tools (RECOMMENDED)
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.SqlcmdSQLServerDB(
                    host='localhost',
                    user='sa',
                    password='<my_strong_password>',
                    database='dwh'),
            }

            # explicitly define to use sqsh
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.SqshSQLServerDB(
                    host='localhost',
                    user='sa',
                    password='<my_strong_password>',
                    database='dwh'),
            }

    .. group-tab:: Use ODBC Driver 18

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.SQLServerDB(
                    host='localhost',
                    user='sa',
                    password='<my_strong_password>',
                    database='dwh',
                    odbc_driver='ODBC Driver 18 for SQL Server'),
            }

            # explicitly define to use the MSSQL Tools (RECOMMENDED)
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.SqlcmdSQLServerDB(
                    host='localhost',
                    user='sa',
                    password='<my_strong_password>',
                    database='dwh',
                    odbc_driver='ODBC Driver 18 for SQL Server'),
            }

            # explicitly define to use sqsh
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.SqshSQLServerDB(
                    host='localhost',
                    user='sa',
                    password='<my_strong_password>',
                    database='dwh',
                    odbc_driver='ODBC Driver 18 for SQL Server'),
            }

|

|

API reference
-------------

This section contains database specific API in the module.

.. module:: mara_db.sqlserver

Configuration
~~~~~~~~~~~~~

.. module:: mara_db.dbs
    :noindex:

.. autoclass:: SQLServerDB
    :special-members: __init__
    :inherited-members:
    :members:

.. autoclass:: SqlcmdSQLServerDB
    :special-members: __init__
    :inherited-members:
    :members:

.. autoclass:: SqshSQLServerDB
    :special-members: __init__
    :inherited-members:
    :members:


Cursor context
~~~~~~~~~~~~~~

.. module:: mara_db.sqlserver
    :noindex:

.. autofunction:: sqlserver_cursor_context
