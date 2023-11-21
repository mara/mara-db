"""Auto-migrate command line interface"""

import click
import sys
from warnings import warn


@click.group()
def mara_db():
    """Commands to interact with the database."""
    pass


@mara_db.command()
def migrate():
    """Compares the current database with all defined models and applies the diff"""
    import mara_db.auto_migration

    if not mara_db.auto_migration.auto_discover_models_and_migrate():
        sys.exit(-1)


# Old cli commands to be dropped in 5.0:

@click.command("migrate")
def _migrate():
    """Compares the current database with all defined models and applies the diff"""
    warn("CLI command `<app> mara_db.migrate` will be dropped in 5.0. Please use: `<app> mara-db migrate`")
    migrate.callback()
