Installation
============

Python Version
--------------

We recommend using the latest version of Python. Mara supports Python
3.6 and newer.

Dependencies
------------

These packages will be installed automatically when installing Mara DB.

* [SQLAlchemy] the Database SQL Toolkit and Object Relation Mapper (ORM) for python
* [SQLAlchemy-Utils] various utility functions, new data types and helpers for SQLAlchemy
* [Alembic] a lightweight database migration tool
* [Multimethod] provides a decorator for adding multiple argument dispatching to functions
* [Graphviz] facilitates the creation and rendering of graph descriptions in the [DOT](https://www.graphviz.org/doc/info/lang.html) language of the [Graphviz](https://www.graphviz.org/) graph drawing software from Python.
* [Mara Page] mara core module for defining pages of Flask-based backends
* [psycopg2-binary] required fro PostgreSQL database support

[SQLAlchemy]: https://www.sqlalchemy.org/
[SQLAlchemy-Utils]: https://sqlalchemy-utils.readthedocs.io/
[Alembic]: https://pygments.org/
[Multimethod]: https://pypi.org/project/multimethod/
[Graphviz]: https://graphviz.readthedocs.io/
[Mara Page]: https://mara-page.readthedocs.io/
[psycopg2-binary]: https://pypi.org/project/psycopg2-binary/

```{warning}
The package ``psycopg2-binary`` is planned to be removed as default requirement. When using PostgreSQL as database
backend, please use extras ``postgres`` like `mara-db[postgres]` to make sure that the module gets installed.
```

Install Mara DB
---------------

To use the library directly, use pip:

``` bash
$ pip install mara-db
```

or

``` bash
$ pip install git+https://github.com/mara/mara-db.git
```

```{note}
For most of the database engines additional python packages are required which can be installed via extras.

For example, for PostgreSQL use

``$ pip install mara-db[postgres]``

to make sure all additional required packages are installed.
```