"""Auto-migrate command line interface"""

import sys

import click

import mara_db.auto_migration


@click.command()
def migrate():
    """Compares the current database with all defined models and applies the diff"""
    if not mara_db.auto_migration.auto_discover_models_and_migrate():
        sys.exit(-1)
