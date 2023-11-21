CLI
===

.. module:: mara_db.cli

This part of the documentation covers all the available cli commands of Mara DB.


``migrate``
-----------

.. tabs::

    .. group-tab:: Mara CLI

        .. code-block:: shell

            mara db migrate

    .. group-tab:: Mara Flask App

        .. code-block:: python

            flask mara-db migrate


Compares the current database db alias `mara` with all defined models and applies
the diff using alembic.
