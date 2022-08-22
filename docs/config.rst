Configuration
=============


Mara Configuration Values
-------------------------

The following configuration values are used by this module. They are defined as python functions in ``mara_db.config``
and can be changed with the `monkey patch`_ from `Mara App`_. An example can be found `here <https://github.com/mara/mara-example-project-1/blob/master/app/local_setup.py.example>`_.

.. _monkey patch: https://github.com/mara/mara-app/blob/master/mara_app/monkey_patch.py
.. _Mara App: https://github.com/mara/mara-app


.. module:: mara_db.config

.. autofunction:: databases

|

.. autofunction:: default_timezone

|

.. autofunction:: default_echo_queries

|

.. autofunction:: schema_ui_foreign_key_column_regex
