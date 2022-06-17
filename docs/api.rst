API
===

.. module:: mara_db

This part of the documentation covers all the interfaces of Mara Page. For
parts where the package depends on external libraries, we document the most
important right here and provide links to the canonical documentation.


DBs
---

.. module:: mara_db.dbs

.. autofunction:: db


Auto migration
--------------

.. module:: mara_db.auto_migration

.. autofunction:: auto_migrate

.. autofunction:: auto_discover_models_and_migrate


Shell
-----

.. module:: mara_db.shell

.. autofunction:: query_command

.. autofunction:: copy_to_stdout_command

.. autofunction:: copy_from_stdin_command

.. autofunction:: copy_command


SQLAlchemy
----------

.. module:: mara_db.sqlalchemy_engine

.. autofunction:: engine
