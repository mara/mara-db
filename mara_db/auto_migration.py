"""Auto-migration of sql alchemy models with alembic. Use with care"""

import copy
import io
import sys
import typing

import sqlalchemy.engine
import sqlalchemy.sql.schema
from sqlalchemy import *  # unfortunately needed to get the eval part further down working
# noinspection PyUnresolvedReferences
from sqlalchemy.dialects import *  # unfortunately needed to get the eval part further down working

import mara_db.dbs
from .sqlalchemy_engine import engine


def auto_migrate(engine: sqlalchemy.engine.Engine, models: [sqlalchemy.sql.schema.MetaData]):
    """
    Compares a database with a list of defined orm models and applies the diff. Prints executed SQL statements to stdout.

    Based on `alembic automigrations`_, but doesn't require intermediate migration files.

    Use with care, does not work in many cases.

    Args:
        engine: the database to use
        models: A list of orm models

    Returns:
        True in case of no failures

    .. _alembic automigrations:
        http://alembic.zzzcomputing.com/en/latest/autogenerate.html
    """
    import alembic.runtime.migration
    import alembic.autogenerate
    import sqlalchemy_utils

    try:
        # create database if it does not exist
        if not sqlalchemy_utils.database_exists(engine.url):
            sqlalchemy_utils.create_database(engine.url)
            print(f'Created database "{engine.url!r}"\n')
    except Exception as e:
        print(f'Could not access or create database "{engine.url!r}":\n{e}', file=sys.stderr)
        return False

    # merge all models into a single metadata object
    combined_meta_data = MetaData()
    for model in models:
        model.metadata.tables[model.__tablename__].tometadata(combined_meta_data)

    # create diff between models and current db and translate to ddl
    ddl = []
    with engine.connect() as connection:
        output = io.StringIO()

        diff_context = alembic.runtime.migration.MigrationContext(connection.dialect, connection, opts={})

        autogen_context = alembic.autogenerate.api.AutogenContext(diff_context,
                                                                  opts={'sqlalchemy_module_prefix': 'sqlalchemy.',
                                                                        'alembic_module_prefix': 'executor.'})

        execution_context = alembic.runtime.migration.MigrationContext(connection.dialect, connection,
                                                                       opts={'output_buffer': output, 'as_sql': True})

        # needed for the eval below
        executor = alembic.operations.Operations(execution_context)

        # Step 1: create a diff between the meta data and the data base
        # operations is a list of MigrateOperation instances, e.g. a DropTableOp
        operations = alembic.autogenerate.produce_migrations(diff_context, combined_meta_data).upgrade_ops.ops

        for operation in operations:
            # Step 2: autogenerate a python statement from the operation, e.g. "executor.drop_table('bar')"
            renderer = alembic.autogenerate.renderers.dispatch(operation)
            statements = renderer(autogen_context, operation)
            if not isinstance(statements, list):
                statements = [statements]

            for statement in statements:
                # Step 3: "execute" python statement and get sql from buffer, e.g. "DROP TABLE bar;"
                try:
                    eval(statement)
                except Exception as e:
                    print('statement: ' + statement)
                    raise (e)
                ddl.append(output.getvalue())
                output.truncate(0)
                output.seek(0)

    with engine.begin() as connection:
        for statement in ddl:
            sys.stdout.write('\033[1;32m' + statement + '\033[0;0m')
            connection.execute(statement)

    return True


def auto_discover_models_and_migrate() -> bool:
    """
    Auto-migrates all sqlalchemy models that been marked for auto-migration database with the alias 'mara'.

    Models are marked for auto-migration by being put into a module-level `MARA_AUTOMIGRATE_SQLALCHEMY_MODELS`
    variable. E.g.

        MARA_AUTOMIGRATE_SQLALCHEMY_MODELS = [MyModel]

    For this, all modules that contain sqlalchemy models need to be loaded first

    Returns:
        True when no failure happened
    """
    models = []
    for name, module in copy.copy(sys.modules).items():
        if 'MARA_AUTOMIGRATE_SQLALCHEMY_MODELS' in dir(module):
            module_models = getattr(module, 'MARA_AUTOMIGRATE_SQLALCHEMY_MODELS')
            if isinstance(module_models, typing.Callable):
                module_models = module_models()
            if isinstance(models, typing.Dict):
                module_models = module_models.values()
            assert (isinstance(module_models, typing.Iterable))
            models += module_models
    return auto_migrate(engine('mara'), models)


if __name__ == "__main__":
    # Example
    import sqlalchemy.ext.declarative
    import tempfile
    import pathlib

    with tempfile.TemporaryDirectory() as dir:
        db = mara_db.dbs.SQLiteDB(file_name=pathlib.Path(dir) / 'test.sqlite')


        # define a model / table
        class MyTable(sqlalchemy.ext.declarative.declarative_base()):
            __tablename__ = 'my_table'
            my_table_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
            column_1 = sqlalchemy.Column(sqlalchemy.TEXT, nullable=False, index=True)


        auto_migrate(engine=engine(db), models=[MyTable])


        # ->
        # Created database "sqlite:////var/folders/gg/8117h7rj08zd9rpt55l315_1xx044y/T/tmpl_sdop4j/test.sqlite"
        #
        # CREATE TABLE my_table (
        #     my_table_id SERIAL NOT NULL,
        #     column_1 TEXT NOT NULL,
        #     PRIMARY KEY (my_table_id)
        # );
        #
        # CREATE INDEX ix_my_table_column_1 ON my_table (column_1);

        # remove index and add another column
        class MyTable(sqlalchemy.ext.declarative.declarative_base()):
            __tablename__ = 'my_table'
            my_table_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
            column_1 = sqlalchemy.Column(sqlalchemy.TEXT, nullable=False)
            column_2 = sqlalchemy.Column(sqlalchemy.Integer)


        auto_migrate(engine=engine(db), models=[MyTable])
        # ->
        # ALTER TABLE my_table ADD COLUMN column_2 INTEGER;
        #
        # DROP INDEX ix_my_table_text_column_1;
