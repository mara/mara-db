Google Big Query
================

Optionally, for loading data from files into BigQuery, the `gcloud_gcs_bucket_name` can be specified in the database initialization.
This will use the Google Cloud Storage bucket specified as cache for loading data and over-coming potential limitations.
For more see [loading-data](https://cloud.google.com/bigquery/docs/bq-command-line-tool#loading_data). 
By default, files will directly loaded locally as described in [loading-local-data](https://cloud.google.com/bigquery/docs/loading-data-local#loading_data_from_a_local_data_source).

Installation
------------

Use extras `bigquery` to install all required packages.

.. code-block:: shell

    $ pip install mara-db[bigquery]

The official `bq` and `gcloud` clients are required.
See the `Google Cloud SDK <https://cloud.google.com/sdk/docs/quickstarts>`_ page for installation details.

Enabling the BigQuery API and Service account JSON credentials are also required as listed 
in the official documentation `here <https://cloud.google.com/bigquery/docs/quickstarts/quickstart-client-libraries#before-you-begin>`_.

One time authentication of the service-account used:

.. code-block:: bash

    gcloud auth activate-service-account --key-file='path-to/service-account.json'

To read from STDIN an additional Google Cloud Storage bucket is required as temp storage.

Configuration examples
----------------------

.. tabs::

    .. group-tab:: Service account

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.BigQueryDB(
                    service_account_json_file_name='service-account.json',
                    location='EU',
                    project='my-project-name',
                    dataset='dwh'),
            }

    .. group-tab:: ... with GSC bucket

        .. code-block:: python

            import mara_db.dbs
            mara_db.config.databases = lambda: {
                'dwh': mara_db.dbs.BigQueryDB(
                    service_account_json_file_name='service-account.json',
                    location='EU',
                    project='my-project-name',
                    dataset='dwh',
                    gcloud_gcs_bucket_name='my-temp-bucket'),
            }

|

|

API reference
-------------

This section contains database specific API in the module.

.. module:: mara_db.bigquery

Configuration
~~~~~~~~~~~~~

.. module:: mara_db.dbs
    :noindex:

.. autoclass:: BigQueryDB
    :special-members: __init__
    :inherited-members:
    :members:


Cursor context
~~~~~~~~~~~~~~

.. module:: mara_db.bigquery
    :noindex:

.. autofunction:: bigquery_cursor_context

General helper functions
~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: mara_db.bigquery
    :noindex:

.. autofunction:: bigquery_credentials

.. autofunction:: bigquery_client

Data modelling helper functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. module:: mara_db.bigquery
    :noindex:

.. autofunction:: create_bigquery_table_from_postgresql_query

.. autofunction:: replace_dataset
