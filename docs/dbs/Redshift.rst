Amazon Redshift
===============

.. warning::
    From version 5 the package ``psycopg2-binary``` will not be installed by default anymore.
    Please make sure to include extras ``redshift`` in your requirements.txt file, see below.


Installation
------------

Use extras `redshift` to install all required packages.

.. code-block:: shell

    $ pip install mara-db[redshift]

The ``psql`` client is required which can be installed on Ubuntu/Debian via

.. code-block:: shell

    $ sudo apt-get install postgresql-client

To read from STDIN an additional S3 bucket is required as temp storage. You need to install the `awscli <https://pypi.org/project/awscli/>`_ package in addition:

.. code-block:: shell

    $ pip install awscli


Configuration examples
----------------------

.. tabs::

    .. group-tab:: Default

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.RedshiftDB(
                    host='localhost',
                    user='root',
                    password='<my_strong_password>',
                    database='dwh'),
            }

    .. group-tab:: With S3 bucket

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.RedshiftDB(
                    host='localhost',
                    user='root',
                    password='<my_strong_password>',
                    database='dwh',
                    aws_access_key_id='...,
                    aws_secret_access_key='...',
                    =aws_s3_bucket_name='my-s3-bucket'),
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

.. autoclass:: RedshiftDB
    :special-members: __init__
    :inherited-members:
    :members:
